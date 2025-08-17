from __future__ import annotations
from .enums import Compatibility, Gamut, HalfLine, EOTF, IQ, Resolution, SubBlack, SuperWhite
from dataclasses import dataclass, replace
from typing import TypeVar
import vapoursynth as vs

T = TypeVar("T", bound="ColorbarsBackend")


@dataclass(frozen=True)
class ColorbarsBackend:
    resolution: Resolution
    format: vs.PresetVideoFormat
    eotf: EOTF
    gamut: Gamut
    compatibility: Compatibility
    subblack: SubBlack
    superwhite: SuperWhite
    iq: IQ
    halfline: HalfLine

    def apply_preset(self: T, preset: 'ColorbarsBackend') -> T:
        return replace(self, **vars(preset))


@dataclass(frozen=True, slots=True)
class ColorbarsSettings(ColorbarsBackend):
    resolution: Resolution
    format: vs.PresetVideoFormat
    eotf: EOTF = EOTF.SDR
    gamut: Gamut = Gamut.BT709
    compatibility: Compatibility = Compatibility.IGNORE_BLANKING
    subblack: SubBlack = SubBlack.TRUE
    superwhite: SuperWhite = SuperWhite.TRUE
    iq: IQ = IQ.NEG_I_POS_Q
    halfline: HalfLine = HalfLine.FALSE


@dataclass(frozen=True, slots=True)
class Crop:
    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0