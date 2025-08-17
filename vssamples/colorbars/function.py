from typing import Optional

from colorbars.colorbars import ColorBars
import vapoursynth as vs
from .types import ColorbarsSettings, Resolution, EOTF, Gamut, Compatibility, SubBlack, SuperWhite, IQ, HalfLine, Crop
from dataclasses import fields, replace
from .backend import Signature


def color_bars(
    preset: Optional[ColorbarsSettings] = None,
    resolution: Resolution = Resolution.HD_1080,
    format: vs.PresetVideoFormat = vs.YUV444P10,
    eotf: EOTF = EOTF.SDR,
    gamut: Gamut = Gamut.BT709,
    compatibility: Compatibility = Compatibility.IGNORE_BLANKING,
    subblack: SubBlack = SubBlack.TRUE,
    superwhite: SuperWhite = SuperWhite.TRUE,
    iq: IQ = IQ.NEG_I_POS_Q,
    halfline: HalfLine = HalfLine.FALSE,
    duration: int = 60,
    fpsnum: int = 30_000,
    fpsden: int = 1001,
    field_based: int = vs.FIELD_PROGRESSIVE,
    blur: bool = True,
    crop: Crop = Crop(0, 0, 0, 0)
) -> vs.VideoNode:

    settings = ColorbarsSettings(
        resolution=resolution,
        format=format,
        eotf=eotf,
        gamut=gamut,
        compatibility=compatibility,
        subblack=subblack,
        superwhite=superwhite,
        iq=iq,
        halfline=halfline,
    )

    sig = Signature.generate(color_bars, settings)
    user_overrides = sig.changed

    if preset is not None:
        settings = settings.apply_preset(preset)

    settings = replace(settings, **user_overrides)

    node = ColorBars.generate(settings)

    return ColorBars.metadata(
        node, duration=duration, fpsnum=fpsnum, fpsden=fpsden,
        field_based=field_based, blur=blur,
        crop=crop,
        format=format
    )