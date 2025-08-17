# https://github.com/HomeOfVapourSynthEvolution/mvsfunc/blob/master/mvsfunc/mvsfunc.py#L2829
from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import Enum
from typing import Union, Any

import vapoursynth as vs

core = vs.core

class ZimgDither(Enum):
    NONE = "none"
    ORDERED = "ordered"
    RANDOM = "random"
    ERROR_DIFFUSION = "error_diffusion"

class SampleType(Enum):
    INTEGER = vs.INTEGER
    FLOAT = vs.FLOAT

    @staticmethod
    def from_vs(sample_type_value: int) -> "SampleType":
        return SampleType.FLOAT if sample_type_value == vs.FLOAT else SampleType.INTEGER

    def to_vs(self) -> int:
        return int(self.value)

class FmtConvDitherMode(Enum):
    ORDERED = 0
    NONE = 1
    ROUND = 2
    SIERRA_2_4A = 3
    STUCKI = 4
    ATKINSON = 5
    FLOYD_STEINBERG = 6
    OSTROMOUKHOV = 7
    VOID_AND_CLUSTER = 8
    QUASIRANDOM = 9

@dataclass
class FmtConvDither:
    dmode: FmtConvDitherMode = FmtConvDitherMode.SIERRA_2_4A
    ampo: float = 1.0
    ampn: float = 0.0
    dyn: bool = False
    staticnoise: bool = False
    cpuopt: int = 0
    patsize: int = 32
    tpdfo: bool = False
    tpdfn: bool = False
    corplane: bool = False

    def to_kwargs(self) -> dict[str, Any]:
        return {
            'dmode': int(self.dmode.value),
            'ampo': float(self.ampo),
            'ampn': float(self.ampn),
            'dyn': bool(self.dyn),
            'staticnoise': bool(self.staticnoise),
            'cpuopt': int(self.cpuopt),
            'patsize': int(self.patsize),
            'tpdfo': bool(self.tpdfo),
            'tpdfn': bool(self.tpdfn),
            'corplane': bool(self.corplane)
        }

UserDither = Union[ZimgDither, FmtConvDither]

@dataclass
class DepthConfig:
    target_depth: int
    target_sample: SampleType
    input_full_range: bool
    output_full_range: bool
    prefer_zimg: bool
    dithering: UserDither

def make_default_depth_config(input_clip: vs.VideoNode, target_depth: int, prefer_zimg: bool = False) -> DepthConfig:
    if not isinstance(input_clip, vs.VideoNode):
        raise type_error('"input" must be a clip!')
    fmt = input_clip.format
    if fmt is None:
        raise value_error('Variable or unknown format is not supported!')
    is_yuv = fmt.color_family == vs.YUV
    is_gray = fmt.color_family == vs.GRAY
    input_full = False if is_yuv or is_gray else True
    output_full = input_full
    target_sample = SampleType.FLOAT if target_depth >= 32 else SampleType.from_vs(fmt.sample_type)

    # Choose dithering policy explicitly
    if prefer_zimg:
        if target_depth == 32 or (target_depth >= fmt.bits_per_sample and output_full == input_full and not output_full):
            dither: UserDither = ZimgDither.NONE
        else:
            dither = ZimgDither.ERROR_DIFFUSION
    else:
        if target_depth == 32 or (target_depth >= fmt.bits_per_sample and output_full == input_full and not output_full):
            dither = FmtConvDither(FmtConvDitherMode.NONE)
        else:
            dither = FmtConvDither()

    return DepthConfig(
        target_depth=target_depth,
        target_sample=target_sample,
        input_full_range=input_full,
        output_full_range=output_full,
        prefer_zimg=prefer_zimg,
        dithering=dither,
    )

def get_func_name(num_of_call_stacks=1):
    frame = inspect.currentframe()
    for _ in range(num_of_call_stacks):
        if frame is None:
            break
        frame = frame.f_back  # type: ignore[attr-defined]
    if frame is None or frame.f_code is None:  # type: ignore[attr-defined]
        return "<unknown>"
    return frame.f_code.co_name  # type: ignore[attr-defined]

def type_error(obj1, *args, num_stacks=1):
    name = get_func_name(num_stacks + 1)
    return TypeError(f'[mvsfunc.{name}] {obj1}', *args)

def value_error(obj1, *args, num_stacks=1):
    name = get_func_name(num_stacks + 1)
    return ValueError(f'[mvsfunc.{name}] {obj1}', *args)

def attribute_error(obj1, *args, num_stacks=1):
    name = get_func_name(num_stacks + 1)
    return AttributeError(f'[mvsfunc.{name}] {obj1}', *args)

def CheckColorFamily(color_family, valid_list=None, invalid_list=None):
    if valid_list is None:
        valid_list = ('RGB', 'YUV', 'GRAY')
    if invalid_list is None:
        invalid_list = ('COMPAT', 'UNDEFINED')
    for cf in invalid_list:
        if color_family == getattr(vs, cf, None):
            raise value_error(f'color family *{cf}* is not supported!')
    if valid_list:
        if color_family not in [getattr(vs, cf, None) for cf in valid_list]:
            raise value_error(f'color family not supported, only {valid_list} are accepted')

def RemoveFrameProp(clip, prop):
    if hasattr(core.std, 'RemoveFrameProps'):
        return core.std.RemoveFrameProps(clip, prop)
    # Fallback not available in some API versions; no-op to avoid linter issues
    return clip

def RegisterFormat(color_family, sample_type, bits_per_sample, subsampling_w, subsampling_h):
    # Modern VapourSynth exposes query_video_format
    return core.query_video_format(color_family, sample_type, bits_per_sample, subsampling_w, subsampling_h)

def SetColorSpace(clip, ColorRange=None):
    if not isinstance(clip, vs.VideoNode):
        raise type_error('"clip" must be a clip!')
    if ColorRange is not None:
        if isinstance(ColorRange, bool):
            if not ColorRange:
                clip = RemoveFrameProp(clip, '_ColorRange')
        elif isinstance(ColorRange, int):
            if 0 <= ColorRange <= 1:
                clip = core.std.SetFrameProp(clip, prop='_ColorRange', intval=ColorRange)
            else:
                raise value_error('valid range of "ColorRange" is [0, 1]!')
        else:
            raise type_error('"ColorRange" must be an int or a bool!')
    return clip

def _quantization_parameters(sample: int = vs.INTEGER, depth: int = 8, full: bool = True, chroma: bool = False):
    qp = {}
    if depth < 1:
        raise value_error('"depth" should not be less than 1!', num_stacks=2)

    lShift, rShift = depth - 8, 8 - depth
    shift = lShift if lShift >= 0 else rShift
    op = '<<' if lShift >= 0 else '>>'

    if sample == vs.INTEGER:
        if chroma:
            qp['floor'] = 0 if full else (16 << shift if op == '<<' else 16 >> shift)
            qp['neutral'] = (128 << shift if op == '<<' else 128 >> shift)
            qp['ceil'] = (1 << depth) - 1 if full else (240 << shift if op == '<<' else 240 >> shift)
        else:
            qp['floor'] = 0 if full else (16 << shift if op == '<<' else 16 >> shift)
            qp['neutral'] = qp['floor']
            qp['ceil'] = (1 << depth) - 1 if full else (235 << shift if op == '<<' else 235 >> shift)
    elif sample == vs.FLOAT:
        qp.update({'floor': -0.5 if chroma else 0.0, 'neutral': 0.0, 'ceil': 0.5 if chroma else 1.0})
    else:
        raise value_error('Unsupported "sample" specified!', num_stacks=2)
    
    qp['range'] = qp['ceil'] - qp['floor']
    return qp

def _quantization_conversion(clip: vs.VideoNode, depths: int, depthd: int, sample: int,
                             fulls: bool, fulld: bool, chroma: bool, dbitPS: int, mode: int):
    if not isinstance(clip, vs.VideoNode):
        raise type_error('"clip" must be a clip!', num_stacks=2)

    src_format = clip.format
    if src_format is None:
        raise value_error('Variable or unknown format is not supported!', num_stacks=2)
    color_family = src_format.color_family
    CheckColorFamily(color_family)
    is_yuv = color_family == vs.YUV
    is_gray = color_family == vs.GRAY
    src_sample = src_format.sample_type
    d_sample = sample
    clamp = d_sample == vs.INTEGER
    d_format = RegisterFormat(src_format.color_family, d_sample, dbitPS, src_format.subsampling_w, src_format.subsampling_h)

    def build_expr(use_chroma: bool, mode_val: int) -> str:
        if d_sample == vs.INTEGER:
            expr_lower = 0
            expr_upper = (1 << (d_format.bytes_per_sample * 8)) - 1
        else:
            expr_lower = float('-inf')
            expr_upper = float('inf')

        s_qp = _quantization_parameters(src_sample, depths, fulls, use_chroma)
        d_qp = _quantization_parameters(d_sample, depthd, fulld, use_chroma)

        gain = d_qp['range'] / s_qp['range']
        offset = d_qp['neutral' if use_chroma else 'floor'] - s_qp['neutral' if use_chroma else 'floor'] * gain

        scale = 256 if mode_val == 1 else 1
        gain *= scale
        offset *= scale

        parts: list[str] = []
        if gain != 1 or offset != 0 or clamp:
            parts.append(' x ')
            if gain != 1:
                parts.append(f' {gain} * ')
            if offset != 0:
                parts.append(f' {offset} + ')
            if clamp:
                lower = d_qp['floor'] * scale
                upper = d_qp['ceil'] * scale
                if lower > expr_lower:
                    parts.append(f' {lower} max ')
                if upper < expr_upper:
                    parts.append(f' {upper} min ')
        return ''.join(parts)

    y_expr = build_expr(False, mode)
    c_expr = build_expr(True, mode)

    expr = [y_expr, c_expr] if is_yuv else (c_expr if is_gray and chroma else y_expr)
    out = core.std.Expr(clip, expr, format=d_format.id)
    return SetColorSpace(out, ColorRange=0 if fulld else 1)

def zDepth(clip, sample=None, depth=None, range=None, range_in=None, dither_type=None, cpu_type=None):
    if not isinstance(clip, vs.VideoNode):
        raise type_error('"clip" must be a clip!')

    src_fmt = clip.format
    if src_fmt is None:
        raise value_error('Variable or unknown format is not supported!')
    sample = src_fmt.sample_type if sample is None else sample
    depth = src_fmt.bits_per_sample if depth is None else depth

    fmt = RegisterFormat(src_fmt.color_family, sample, depth, src_fmt.subsampling_w, src_fmt.subsampling_h)
    if hasattr(core, 'resize'):
        return core.resize.Bicubic(clip, format=fmt.id, range=range, range_in=range_in, dither_type=dither_type, cpu_type=cpu_type)
    raise attribute_error('no available core.resize found!')

def Depth(input_clip: vs.VideoNode, depth: int = 8, sample: int = vs.INTEGER, fulls: bool = False, fulld: bool = False,
          dither: UserDither = FmtConvDither(dmode=FmtConvDitherMode.NONE), useZ: bool = False):

    if not isinstance(input_clip, vs.VideoNode):
        raise type_error('"input" must be a clip!')

    src_fmt = input_clip.format
    if src_fmt is None:
        raise value_error('Variable or unknown format is not supported!')
    color_family = src_fmt.color_family
    CheckColorFamily(color_family)
    is_yuv = color_family == vs.YUV
    is_gray = color_family == vs.GRAY

    src_bits = src_fmt.bits_per_sample
    src_sample = src_fmt.sample_type

    if fulls is None:
        fulls = False if is_yuv or is_gray else True

    low_depth = (depth or src_bits) < 8
    out_bits = 8 if low_depth else (depth or src_bits)

    out_sample = sample if sample is not None else (vs.FLOAT if out_bits >= 32 else src_sample)
    if depth is None and src_sample != out_sample:
        out_bits = 32 if out_sample == vs.FLOAT else 16

    fulld = fulls if fulld is None else fulld

    def _is_none_dither(d) -> bool:
        if isinstance(d, FmtConvDither):
            return d.dmode == FmtConvDitherMode.NONE
        if isinstance(d, ZimgDither):
            return d == ZimgDither.NONE
        return d in ["none", 1]

    needs_final_lowdepth_convert = False
    final_lowdepth_full: bool = bool(fulld)

    if low_depth:
        if _is_none_dither(dither):
            clip = _quantization_conversion(input_clip, src_bits, depth, vs.INTEGER, fulls, fulld, chroma=False, dbitPS=8, mode=0)
            return _quantization_conversion(clip, depth, 8, vs.INTEGER, fulld, fulld, chroma=False, dbitPS=8, mode=0)
        else:
            final_lowdepth_full = fulld
            clip = _quantization_conversion(input_clip, src_bits, depth, vs.INTEGER, fulls, fulld, chroma=False, dbitPS=16, mode=1)
            src_sample, src_bits, fulls, fulld = vs.INTEGER, 16, False, False
            needs_final_lowdepth_convert = True
    else:
        clip = input_clip

    useZ = useZ or (src_sample == vs.INTEGER and src_bits in [13, 15]) or \
           (out_sample == vs.INTEGER and (out_bits == 11 or 13 <= out_bits <= 15)) or \
           (src_sample == vs.FLOAT and src_bits < 32) or (out_sample == vs.FLOAT and out_bits < 32)

    if dither is None:
        if out_bits == 32 or (out_bits >= src_bits and fulld == fulls and not fulld):
            dither = ZimgDither.NONE if useZ else FmtConvDither(FmtConvDitherMode.NONE)
        else:
            dither = ZimgDither.ERROR_DIFFUSION if useZ else FmtConvDither()

    if out_sample == src_sample and out_bits == src_bits and (src_sample == vs.FLOAT or fulld == fulls) and not low_depth:
        return clip

    if useZ:
        dither_type = dither.value if isinstance(dither, ZimgDither) else "error_diffusion"
        clip = zDepth(clip, sample=out_sample, depth=out_bits, range=fulld, range_in=fulls, dither_type=dither_type)
    else:
        fmtc_params: dict[str, Any] = dither.to_kwargs() if isinstance(dither, FmtConvDither) else {'dmode': dither if isinstance(dither, int) else 3}
        if 'ampo' not in fmtc_params:
            fmtc_params['ampo'] = 1.5 if fmtc_params.get('dmode') == 0 else 1.0

        clip = core.fmtc.bitdepth(clip, bits=out_bits, flt=out_sample, fulls=fulls, fulld=fulld, **fmtc_params)
        clip = SetColorSpace(clip, ColorRange=0 if fulld else 1)

    if needs_final_lowdepth_convert:
        clip = _quantization_conversion(clip, depth, 8, vs.INTEGER, bool(final_lowdepth_full), bool(final_lowdepth_full), chroma=False, dbitPS=8, mode=0)

    return clip


if __name__ == "__vspreview__":
    from signals.gradient import Vortex

    clip = Vortex(width=1920, height=1080, length=100)
    clip = clip.generate()

    clip = Depth(
        clip,
        depth=2,
        dither=FmtConvDither(dmode=FmtConvDitherMode.OSTROMOUKHOV)
        )

    clip.set_output(0)