from __future__ import annotations
import vapoursynth as vs
import numpy as np

core = vs.core

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


def get_dct_matrix(N=8):

    T = np.zeros((N, N), dtype=np.float32)
    for i in range(N):
        for j in range(N):
            if i == 0:
                T[i, j] = 1 / np.sqrt(N)
            else:
                T[i, j] = np.sqrt(2 / N) * np.cos((2 * j + 1) * i * np.pi / (2 * N))
    return T

DCT_MATRIX = get_dct_matrix(8)
IDCT_MATRIX = DCT_MATRIX.T


def get_scaled_quant_table(table: np.ndarray, quality: int) -> np.ndarray:

    if quality < 50:
        S = 5000 / quality
    else:
        S = 200 - 2 * quality
    
    scaled_table = np.floor((table * S + 50) / 100)
    scaled_table = np.clip(scaled_table, 1, 255)
    return scaled_table


class JpegArtifacts:
    def __init__(self, clip: vs.VideoNode, quality: int = 50):
    
        if not (0 < quality <= 100):
            raise ValueError("JpegArtifacts: quality must be between 1 and 100.")

        self.clip = clip
        self.quality = quality
        self.bit_depth = clip.format.bits_per_sample # type: ignore
        self.is_float = (self.bit_depth == 32)

        self.luma_q_table = get_scaled_quant_table(LUMA_QUANT_TABLE, self.quality)
        self.chroma_q_table = get_scaled_quant_table(CHROMA_QUANT_TABLE, self.quality)


    def _process_plane(self, plane: np.ndarray, q_table: np.ndarray) -> np.ndarray:

        h, w = plane.shape
        block_size = 8
        
        pad_h = (block_size - h % block_size) % block_size
        pad_w = (block_size - w % block_size) % block_size
        plane_padded = np.pad(plane, ((0, pad_h), (0, pad_w)), 'edge')
        
        plane_padded = plane_padded - 128
        
        ph, pw = plane_padded.shape
        blocks = plane_padded.reshape(ph // block_size, block_size, pw // block_size, block_size)
        blocks = blocks.transpose(0, 2, 1, 3)

        dct_blocks = DCT_MATRIX @ blocks @ IDCT_MATRIX


        quant_blocks = np.round(dct_blocks / q_table).astype(np.int32)

        # Inverse here

        dequant_blocks = quant_blocks * q_table

        idct_blocks = IDCT_MATRIX @ dequant_blocks @ DCT_MATRIX

        idct_blocks = idct_blocks.transpose(0, 2, 1, 3)
        plane_reconstructed = idct_blocks.reshape(ph, pw)

        plane_reconstructed = plane_reconstructed + 128
        
        return plane_reconstructed[:h, :w]


    def _process_frame_int(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()
        
        scale_factor = 255.0 / ((1 << self.bit_depth) - 1)
        
        for i in range(3):
            plane = np.asarray(f[i])
            q_table = self.luma_q_table if i == 0 else self.chroma_q_table
            
            plane_float = plane.astype(np.float32)
            
            scaled_plane = plane_float * scale_factor

            processed_plane = self._process_plane(scaled_plane, q_table)
            
            rescaled_plane = processed_plane / scale_factor
            
            max_val = (1 << self.bit_depth) - 1
            clipped_plane = np.clip(rescaled_plane, 0, max_val)
            final_plane = np.round(clipped_plane).astype(plane.dtype)
            
            np.copyto(np.asarray(fout[i]), final_plane)
            
        return fout

    def _process_frame_float(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()
        
        y_plane_vs = np.asarray(f[0])
        u_plane_vs = np.asarray(f[1])
        v_plane_vs = np.asarray(f[2])
        
        y_jpeg = y_plane_vs * 255.0
        u_jpeg = (u_plane_vs + 0.5) * 255.0
        v_jpeg = (v_plane_vs + 0.5) * 255.0

        y_processed = self._process_plane(y_jpeg - 128.0, self.luma_q_table) + 128.0
        u_processed = self._process_plane(u_jpeg - 128.0, self.chroma_q_table) + 128.0
        v_processed = self._process_plane(v_jpeg - 128.0, self.chroma_q_table) + 128.0
        
        y_out = np.clip(y_processed / 255.0, 0.0, 1.0)
        u_out = np.clip((u_processed / 255.0) - 0.5, -0.5, 0.5)
        v_out = np.clip((v_processed / 255.0) - 0.5, -0.5, 0.5)
        
        np.copyto(np.asarray(fout[0]), y_out)
        np.copyto(np.asarray(fout[1]), u_out)
        np.copyto(np.asarray(fout[2]), v_out)
            
        return fout

    def process(self) -> vs.VideoNode:
        selector = self._process_frame_float if self.is_float else self._process_frame_int
        return self.clip.std.ModifyFrame(clips=[self.clip], selector=selector)
