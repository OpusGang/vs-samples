from dataclasses import dataclass
from typing import Final
from .types import ColorbarsSettings
from .enums import Resolution, EOTF, Gamut
import vapoursynth as vs


@dataclass(frozen=True, slots=True)
class Preset:
    NTSC: Final[ColorbarsSettings] = ColorbarsSettings(
        resolution=Resolution.NTSC_BT601,
        format=vs.YUV444P12,
    )

    PAL: Final[ColorbarsSettings] = ColorbarsSettings(
        resolution=Resolution.PAL_BT601,
        format=vs.YUV444P12,
    )

    HD1080: Final[ColorbarsSettings] = ColorbarsSettings(
        resolution=Resolution.HD_1080,
        format=vs.YUV444P10,
    )

    UHD_PQ: Final[ColorbarsSettings] = ColorbarsSettings(
        resolution=Resolution.UHD_4K,
        format=vs.RGB36,
        eotf=EOTF.PQ,
    )

    UHD_HLG: Final[ColorbarsSettings] = ColorbarsSettings(
        resolution=Resolution.UHD_4K,
        format=vs.RGB30,
        eotf=EOTF.HLG,
    )

    UHD_2020: Final[ColorbarsSettings] = ColorbarsSettings(
        resolution=Resolution.UHD_4K,
        format=vs.YUV444P12,
        eotf=EOTF.SDR,
        gamut=Gamut.BT2020,
    )
