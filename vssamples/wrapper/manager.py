from __future__ import annotations
import vapoursynth as vs
import numpy as np
from typing import Callable, Sequence, Any, Union, TypedDict
from dataclasses import dataclass

core = vs.core

class NumpyProcessor:
    """
    Use as a context manager:
        with NumpyProcessor(width=720, height=720, format=vs.RGBS, length=180, fps=(30,1)) as p:
            # build static arrays once
            ...
            p.process(lambda: out_arr)  # OR p.process(static_arr)
        out = p.clip_out

    Or subclass and override animate(self, n) -> ndarray | tuple(per-plane):
        class MyGen(NumpyProcessor):
            def __init__(...):
                super().__init__(..., static=False)
                # precompute grids/masks
            def animate(self, n):
                return out_arr_or_planes
        clip = MyGen(...).generate()

    Data you can pass to process / animate:
      - HxW (Y only; chroma neutral if present)
      - HxWxC at luma size (C>=planes; extra ignored; chroma auto downsampled for 420/422)
      - tuple/list of per-plane arrays with native plane shapes
    """

    def __init__(
        self,
        *clips: vs.VideoNode,
        width: int = 640,
        height: int = 480,
        length: int = 100,
        format: vs.PresetVideoFormat = vs.RGBS,
        fps: tuple[int, int] = (30, 1),
        color: Union[float, Sequence[float]] = [0, 0, 0],
        autoscale: bool = True,
        static: bool = True
    ) -> None:

        self._NO_PIXELS = object()

        self.autoscale = autoscale
        self._processor: Callable[[], np.ndarray | Sequence[np.ndarray]] | np.ndarray | Sequence[np.ndarray] | None = None
        self._subclass_mode = not static
        self.static = static

        self._static_frame: np.ndarray | Sequence[np.ndarray] | None = None

        if clips:
            self.clips = clips
            self.ref_clip = clips[0]

        else:
            fpsnum, fpsden = fps
            
            if format is vs.GRAYS:
                color = color[0] # type: ignore
            else:
                color = color # type: ignore

            self.ref_clip = core.std.BlankClip(
                width=width, height=height, format=format, color=color, length=length,
                fpsnum=fpsnum, fpsden=fpsden, keep=True
            ) # type: ignore
            self.clips = (self.ref_clip,)

        self.num_planes = self.ref_clip.format.num_planes # type: ignore
        self.sub_w = int(self.ref_clip.format.subsampling_w or 0) # type: ignore
        self.sub_h = int(self.ref_clip.format.subsampling_h or 0) # type: ignore
        self.has_subsampling = (self.sub_w != 0 or self.sub_h != 0)
        self.bits = self.ref_clip.format.bits_per_sample # type: ignore
        self.sample_type = self.ref_clip.format.sample_type # type: ignore
        self.bytes_per_sample = self.ref_clip.format.bytes_per_sample # type: ignore

        if self.sample_type == vs.FLOAT:
            self.dtype = np.float32
            self.range_max = 1.0
            self.neutral_chroma = 0.5
        elif self.bytes_per_sample == 1:
            self.dtype = np.uint8
            self.range_max = (1 << self.bits) - 1
            self.neutral_chroma = 1 << (self.bits - 1)
        elif self.bytes_per_sample == 2:
            self.dtype = np.uint16
            self.range_max = (1 << self.bits) - 1
            self.neutral_chroma = 1 << (self.bits - 1)
        else:
            self.dtype = np.uint32
            self.range_max = (1 << self.bits) - 1
            self.neutral_chroma = 1 << (self.bits - 1)

        self.width = self.ref_clip.width
        self.height = self.ref_clip.height
        self.planes = self.num_planes
        self.num_frames = self.ref_clip.num_frames

        if self.planes == 1:
            self.frame: np.ndarray = np.zeros((self.height, self.width), dtype=self.dtype)
        else:
            self.frame: np.ndarray = np.zeros((self.height, self.width, self.planes), dtype=self.dtype)

        self.frames: list[np.ndarray | tuple[np.ndarray, ...]] = []
        self.n: int
        self.is_single_clip = len(self.clips) == 1
        self.clip_out: vs.VideoNode

    def __enter__(self) -> "NumpyProcessor":
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            return  # error path; do nothing
        self._build_output()

    @dataclass
    class NumpyProcessorData:
        data: np.ndarray | Sequence[np.ndarray]
        props: dict[str, Any] | None


    def process(
            self,
            processor: Callable[[], NumpyProcessorData | np.ndarray | Sequence[np.ndarray]] | np.ndarray | Sequence[np.ndarray]
    ) -> None:
        # TODO // Create dataclass object for the return type
        """
        Register a processing callable (called once per frame) OR a static ndarray / per-plane sequence.
        For animation, pass a zero-arg callable (e.g., lambda) that returns ndarray or per-plane arrays.
        Register the per-frame generator. It may return:
          • ndarray or per-plane sequence        -> write pixels
          • dict                                 -> props-only (no pixel changes)
          • (ndarray|planes, dict)               -> write pixels then set props
        """
        self._processor = processor

    def plane_shape(self, plane: int) -> tuple[int, int]:
        """(H, W) for a given plane, accounting for subsampling."""
        if plane == 0 or not self.has_subsampling:
            return (self.height, self.width)
        return (self.height >> self.sub_h, self.width >> self.sub_w)

    # ndarray (HxW, HxWxC) or per-plane tuple/list at native shapes.
    def animate(self, n: int) -> np.ndarray | Sequence[np.ndarray]:
        if self._processor is None:
            raise RuntimeError("No processor set. Use process(...) or override animate().")
        if callable(self._processor):
            return self._processor()
        return self._processor

    def generate(self) -> vs.VideoNode:
        self._build_output()
        assert self.clip_out is not None
        return self.clip_out

    def _build_output(self) -> None:
        def _eval(n, f):
            frames_vs = [f] if self.is_single_clip else f
            self.n = n
            self.frames = [self._frame_to_planes(frame) for frame in frames_vs]
            self.frame = self.frames[0] # type: ignore

            if self.static and self._static_frame is not None:
                out = self._static_frame
            elif self.static and self._static_frame is None:
                out = self.animate(0)
                self._static_frame = out
            else:
                out = self.animate(n)
                
            data_obj = self._interpret_out(out)          # 
            return self._write_output_frame(frames_vs[0], data_obj)  # 

        self.clip_out = self.ref_clip.std.ModifyFrame(clips=list(self.clips), selector=_eval)

    def _frame_to_planes(self, frame: vs.VideoFrame) -> np.ndarray | tuple[np.ndarray, ...]:
        if self.planes == 1:
            return np.asarray(frame[0])
        return tuple(np.asarray(frame[p]) for p in range(self.planes))

    def _interpret_out(self, out: Any) -> NumpyProcessorData:
        # TODO // Clean this up
        # props-only
        if isinstance(out, dict):
            return self.NumpyProcessorData(data=self._NO_PIXELS, props=out)
        # (data, props)
        if isinstance(out, tuple) and len(out) == 2 and isinstance(out[1], dict):
            return self.NumpyProcessorData(data=out[0], props=out[1])
        # pixels only
        return self.NumpyProcessorData(data=out, props=None)

    # TODO // Clean this up
    def _write_output_frame(self, frame_in: vs.VideoFrame, data_obj: NumpyProcessorData) -> vs.VideoFrame:
        fout = frame_in.copy()

        if data_obj.data is not self._NO_PIXELS:
            planes = self._prepare_planes(data_obj.data, autoscale=self.autoscale)
            for i, a in enumerate(planes):
                np.copyto(np.asarray(fout[i]), a)

        if data_obj.props:
            for k, v in data_obj.props.items():
                fout.props[k] = v

        return fout

    def _area_downsample_pow2(self, arr: np.ndarray, fx: int, fy: int) -> np.ndarray:

        if fx == 1 and fy == 1:
            return arr
        h, w = arr.shape[:2]
        if (h % fy) or (w % fx):
            raise ValueError(f"Array size {(h, w)} not divisible by factors (fx={fx}, fy={fy}).")

        arr = arr.reshape(h // fy, fy, w // fx, fx, *arr.shape[2:])

        return arr.mean(axis=(1, 3))

    def _normalize_plane_dtype(self, arr: np.ndarray, *, autoscale: bool) -> np.ndarray:
        if self.sample_type == vs.INTEGER:
            if np.issubdtype(arr.dtype, np.floating) and autoscale:
                arr = np.clip(arr, 0.0, 1.0) * self.range_max
                arr = np.rint(arr).astype(self.dtype, copy=False)
            else:
                arr = np.clip(arr, 0, self.range_max).astype(self.dtype, copy=False)
        else:
            arr = arr.astype(np.float32, copy=False) if np.issubdtype(arr.dtype, np.floating) else arr.astype(np.float32, copy=False)
        return np.ascontiguousarray(arr)

    def _prepare_planes(self, data, *, autoscale: bool) -> list[np.ndarray]:
        # TODO // Clean this up
        """
          - ndarray HxW               (luma-only; chroma planes neutral if present)
          - ndarray HxWxC (luma size) (C mapped to planes; chroma auto-downsampled for 420/422)
          - sequence of per-plane ndarrays at native shapes
        Return native per-plane arrays, dtype/range normalized.
        """
        planes: list[np.ndarray] = []

        if isinstance(data, (list, tuple)):
            if len(data) != self.planes:
                raise ValueError(f"Expected {self.planes} plane arrays, got {len(data)}")
            for p, a in enumerate(data):
                eh, ew = self.plane_shape(p)
                if a.shape[:2] != (eh, ew):
                    raise ValueError(f"Plane {p} has shape {a.shape[:2]}, expected {(eh, ew)}")
                planes.append(self._normalize_plane_dtype(a, autoscale=autoscale))
            return planes

        arr = np.asarray(data)

        # HxW: Y-only
        if arr.ndim == 2:
            planes.append(self._normalize_plane_dtype(arr, autoscale=autoscale))
            for _ in range(1, self.planes):
                planes.append(np.full(self.plane_shape(1), self.neutral_chroma, dtype=self.dtype))
            return planes

        # HxWxC at luma size
        if arr.ndim == 3:
            h, w, c = arr.shape
            if (h, w) != (self.height, self.width):
                raise ValueError(f"3D array must be at luma size {(self.height, self.width)}, got {(h, w)}.")
            chans = [arr[..., i] if i < c else None for i in range(self.planes)]

            if chans[0] is None:
                raise ValueError("Need at least one channel for luma.")
            planes.append(self._normalize_plane_dtype(chans[0], autoscale=autoscale))

            for p in range(1, self.planes):
                eh, ew = self.plane_shape(p)
                if chans[p] is None:
                    planes.append(np.full((eh, ew), self.neutral_chroma, dtype=self.dtype))
                else:
                    fx = 1 << self.sub_w
                    fy = 1 << self.sub_h
                    ch = self._area_downsample_pow2(chans[p], fx, fy) # type: ignore
                    planes.append(self._normalize_plane_dtype(ch, autoscale=autoscale))
            return planes

        raise TypeError("Unsupported data. Provide ndarray (HxW or HxWxC) or per-plane sequence.")
