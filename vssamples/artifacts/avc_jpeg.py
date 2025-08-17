from __future__ import annotations
import vapoursynth as vs
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from enum import Enum
import random

core = vs.core

class BlockSize(Enum):
    B4x4 = 4
    B8x8 = 8
    B16x16 = 16

LUMA_QUANT_TABLE = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
], dtype=np.float32)

CHROMA_QUANT_TABLE = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99]
], dtype=np.float32)


def get_dct_matrix(N: int):
    T = np.zeros((N, N), dtype=np.float32)
    for i in range(N):
        for j in range(N):
            if i == 0:
                T[i, j] = 1 / np.sqrt(N)
            else:
                T[i, j] = np.sqrt(2 / N) * np.cos((2 * j + 1) * i * np.pi / (2 * N))
    return T

def get_scaled_quant_table(table: np.ndarray, quality: int) -> np.ndarray:
    if quality < 50:
        S = 5000 / quality
    else:
        S = 200 - 2 * quality
    
    scaled_table = np.floor((table * S + 50) / 100)
    scaled_table = np.clip(scaled_table, 1, 255)
    return scaled_table

def resize_quant_table(table: np.ndarray, size: int) -> np.ndarray:
    if table.shape == (size, size):
        return table
    
    x = np.arange(table.shape[1])
    y = np.arange(table.shape[0])
    
    interp_func = RegularGridInterpolator(
        (y, x),
        table,
        method='cubic',
        bounds_error=False,
        fill_value=None  # type: ignore[arg-type]
    )
    
    new_y, new_x = np.mgrid[0:table.shape[0]-1:size*1j, 0:table.shape[1]-1:size*1j]
    
    return interp_func((new_y, new_x))


class AvcBlockJpeg:
    """
    Frankenstienian in-memory JPEG encoder with variable block size based on motion
    """
    def __init__(self, clip: vs.VideoNode, quality: int = 50, 
                 block_sizes: list[BlockSize] = [BlockSize.B4x4, BlockSize.B8x8, BlockSize.B16x16]):

        self.clip = clip
        self.quality = quality
        self.block_sizes = block_sizes if block_sizes else [BlockSize.B8x8]
        self.bit_depth = clip.format.bits_per_sample # type: ignore
        self.is_float = (self.bit_depth == 32)

        self.block_sizes.sort(key=lambda bs: bs.value)

        self.motion_thresholds: list[int]

        self._temporal_clips(self.clip)
        self.motion_mask = self._motion_mask(self.clip)

        if self.motion_mask:
            if not isinstance(self.motion_mask, vs.VideoNode):
                raise TypeError("AvcBlockJpeg: motion_mask must be a VapourSynth clip.")
            if self.motion_mask.width != clip.width or self.motion_mask.height != clip.height:
                raise ValueError("AvcBlockJpeg: motion_mask must have the same dimensions as clip.")
            
            if self.motion_thresholds:
                if len(self.motion_thresholds) != len(self.block_sizes) - 1:
                    raise ValueError("AvcBlockJpeg: motion_thresholds must have len(block_sizes) - 1 elements.")
            else:
                num_levels = (1 << self.motion_mask.format.bits_per_sample) # type: ignore
                step = num_levels / len(self.block_sizes)
                self.motion_thresholds = [int(step * (i + 1)) for i in range(len(self.block_sizes) - 1)]

        self.dct_matrices = {
            bs.value: get_dct_matrix(bs.value) for bs in self.block_sizes
        }
        self.idct_matrices = {
            bs.value: self.dct_matrices[bs.value].T for bs in self.block_sizes
        }

        self.luma_q_tables = {}
        self.chroma_q_tables = {}

        for bs in self.block_sizes:
            size = bs.value
            luma_q = resize_quant_table(LUMA_QUANT_TABLE, size)
            chroma_q = resize_quant_table(CHROMA_QUANT_TABLE, size)
            self.luma_q_tables[size] = get_scaled_quant_table(luma_q, self.quality)
            self.chroma_q_tables[size] = get_scaled_quant_table(chroma_q, self.quality)


    def _temporal_clips(self, clip: vs.VideoNode):
        self.offset_fwd = clip[1:] + clip[:-1]
        self.offset_bwd = clip[:-1] + clip[1:] 

    def _motion_mask(self, clip: vs.VideoNode):
        return core.akarin.Expr([clip, self.offset_fwd, self.offset_bwd], "x y - abs 10 * z - abs 10 *")

    def _process_plane(
        self,
        plane: np.ndarray,
        q_tables: dict[int, np.ndarray],
        mask_plane: np.ndarray | None,
    ) -> np.ndarray:
        h, w = plane.shape
        macro_block_size = max(bs.value for bs in self.block_sizes)

        pad_h = (macro_block_size - h % macro_block_size) % macro_block_size
        pad_w = (macro_block_size - w % macro_block_size) % macro_block_size
        plane_padded = np.pad(plane, ((0, pad_h), (0, pad_w)), 'edge')
        
        mask_plane_padded: np.ndarray | None = None
        if mask_plane is not None:
            mask_plane_padded = np.pad(mask_plane, ((0, pad_h), (0, pad_w)), 'edge')

        reconstructed_plane = np.zeros_like(plane_padded)

        for r in range(0, plane_padded.shape[0], macro_block_size):
            for c in range(0, plane_padded.shape[1], macro_block_size):
                macro_block = plane_padded[r:r+macro_block_size, c:c+macro_block_size]
                
                if mask_plane is not None:
                    assert mask_plane_padded is not None
                    mask_macro_block = mask_plane_padded[r:r+macro_block_size, c:c+macro_block_size]
                    avg_motion = np.mean(mask_macro_block)
                    
                    chosen_bs_val = self.block_sizes[-1].value
                    for i in range(len(self.motion_thresholds or [])):
                        if avg_motion <= (self.motion_thresholds or [])[i]:
                            chosen_bs_val = self.block_sizes[i].value
                            break
                    
                    chosen_bs_enum: BlockSize = next(bs for bs in self.block_sizes if bs.value == chosen_bs_val)
                else:
                    chosen_bs_enum = random.choice(self.block_sizes)

                chosen_bs = chosen_bs_enum.value
                
                if chosen_bs == macro_block_size:
                    reconstructed_plane[r:r+macro_block_size, c:c+macro_block_size] = self._process_block(
                        macro_block, chosen_bs, q_tables[chosen_bs]
                    )
                else:
                    for sr in range(0, macro_block_size, chosen_bs):
                        for sc in range(0, macro_block_size, chosen_bs):
                            sub_block = macro_block[sr:sr+chosen_bs, sc:sc+chosen_bs]
                            reconstructed_plane[r+sr:r+sr+chosen_bs, c+sc:c+sc+chosen_bs] = self._process_block(
                                sub_block, chosen_bs, q_tables[chosen_bs]
                            )
        
        return reconstructed_plane[:h, :w]

    def _process_block(self, block: np.ndarray, block_size: int, q_table: np.ndarray) -> np.ndarray:
        dct_matrix = self.dct_matrices[block_size]
        idct_matrix = self.idct_matrices[block_size]

        block = block - 128
        
        dct_block = dct_matrix @ block @ idct_matrix
        quant_block = np.round(dct_block / q_table).astype(np.int32)
        dequant_block = quant_block * q_table
        idct_block = idct_matrix @ dequant_block @ dct_matrix

        return idct_block + 128

    def _process_frame_int(self, n: int, f: list[vs.VideoFrame]) -> vs.VideoFrame:
        if self.motion_mask:
            main_frame, mask_frame = f
        else:
            main_frame, mask_frame = f[0], None

        fout = main_frame.copy()
        mask_plane = np.asarray(mask_frame[0]) if mask_frame else None
        scale_factor = 255.0 / ((1 << self.bit_depth) - 1)
        
        for i in range(3):
            plane = np.asarray(main_frame[i])
            q_tables = self.luma_q_tables if i == 0 else self.chroma_q_tables
            
            plane_float = plane.astype(np.float32)
            scaled_plane = plane_float * scale_factor
            processed_plane = self._process_plane(scaled_plane, q_tables, mask_plane if i == 0 else None)
            rescaled_plane = processed_plane / scale_factor
            
            max_val = (1 << self.bit_depth) - 1
            clipped_plane = np.clip(rescaled_plane, 0, max_val)
            final_plane = np.round(clipped_plane).astype(plane.dtype)
            
            np.copyto(np.asarray(fout[i]), final_plane)
            
        return fout

    def _process_frame_float(self, n: int, f: list[vs.VideoFrame]) -> vs.VideoFrame:
        if self.motion_mask:
            main_frame, mask_frame = f
        else:
            main_frame, mask_frame = f[0], None

        fout = main_frame.copy()
        mask_plane = np.asarray(mask_frame[0]) if mask_frame else None
        
        y_plane, u_plane, v_plane = (np.asarray(main_frame[i]) for i in range(3))

        y_jpeg = y_plane * 255.0
        u_jpeg = (u_plane + 0.5) * 255.0
        v_jpeg = (v_plane + 0.5) * 255.0

        y_processed = self._process_plane(y_jpeg, self.luma_q_tables, mask_plane)
        u_processed = self._process_plane(u_jpeg, self.chroma_q_tables, None)
        v_processed = self._process_plane(v_jpeg, self.chroma_q_tables, None)

        y_out = np.clip(y_processed / 255.0, 0.0, 1.0)
        u_out = np.clip((u_processed / 255.0) - 0.5, -0.5, 0.5)
        v_out = np.clip((v_processed / 255.0) - 0.5, -0.5, 0.5)
        
        np.copyto(np.asarray(fout[0]), y_out)
        np.copyto(np.asarray(fout[1]), u_out)
        np.copyto(np.asarray(fout[2]), v_out)
            
        return fout

    def process(self) -> vs.VideoNode:
        selector = self._process_frame_float if self.is_float else self._process_frame_int

        if self.motion_mask:
            return core.std.ModifyFrame(clip=self.clip, clips=[self.clip, self.motion_mask], selector=selector)
        
        return core.std.ModifyFrame(clip=self.clip, clips=[self.clip], selector=selector)
