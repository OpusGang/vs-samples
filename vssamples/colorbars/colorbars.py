from __future__ import annotations

from dataclasses import dataclass, replace

import vapoursynth as vs

from .enums import EOTF, IQ, Compatibility, Gamut, HalfLine, Resolution, SubBlack, SuperWhite
from .presets import Preset
from .types import ColorbarsSettings, Crop

core = vs.core

class Subsampling:
    SDR = [vs.YUV420P10, vs.YUV420P12]
    HLG = [vs.RGB30, vs.RGB36]
    PQ = [vs.RGB30, vs.RGB36]
    PQ_FULL_RANGE = [vs.RGB30, vs.RGB36]

class Generator:
    @staticmethod
    def settings(
        preset: ColorbarsSettings,
        compatibility: Compatibility,
        subblack: SubBlack,
        superwhite: SuperWhite,
        iq: IQ,
        halfline: HalfLine
    ) -> ColorbarsSettings:

        return replace(
            preset,
            compatibility=compatibility,
            subblack=subblack,
            superwhite=superwhite,
            iq=iq,
            halfline=halfline
        )

    @staticmethod
    def generate(settings: ColorbarsSettings) -> vs.VideoNode:
        # TODO: // When generating the colorbars, we need to provide format for the requested EOTF.
        return core.colorbars.ColorBars(
            resolution=settings.resolution,
            format=settings.format,
            hdr=settings.eotf,
            wcg=settings.gamut,
            compatability=settings.compatibility,
            subblack=settings.subblack,
            superwhite=settings.superwhite,
            iq=settings.iq,
            halfline=settings.halfline
        )

    @staticmethod
    def metadata(
        clip: vs.VideoNode,
        duration: int = 60,
        fpsnum: int = 24000,
        fpsden: int = 1001,
        field_based: int = vs.FIELD_PROGRESSIVE,
        blur: bool = True,
        crop: Crop | None = None,
        format: vs.PresetVideoFormat = vs.YUV422P10
    ) -> vs.VideoNode:

        clip = clip.std.SetFrameProp(prop="_FieldBased", intval=field_based)

        if crop is not None and any(getattr(crop, attr) != 0 for attr in Crop.__dataclass_fields__):
            clip = clip.std.Crop(left=crop.left, right=crop.right, top=crop.top, bottom=crop.bottom)

        if blur:
            clip = clip.std.Convolution(mode="h", matrix=[1, 2, 4, 2, 1])

        try:
            clip = clip.resize.Bilinear(format=format)
        except Exception:
            clip = clip.resize.Bilinear(format=format, matrix_s="2020ncl")

        clip = clip * (duration * fpsnum // fpsden)
        return clip.std.AssumeFPS(fpsnum=fpsnum, fpsden=fpsden)


class ColorBars(Generator):
    @staticmethod
    def NTSC(
        compatibility: Compatibility = Compatibility.IDEAL_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE,
    ) -> vs.VideoNode:
        settings = ColorBars.settings(
            Preset.NTSC, compatibility, subblack, superwhite, iq, halfline
        )

        node = ColorBars.generate(settings)
        return ColorBars.metadata(
            node, duration=60, fpsnum=3000, fpsden=1001,
            field_based=vs.FIELD_BOTTOM, blur=True,
            crop=Crop(left=4, right=4),
            format=vs.YUV422P10
        )

    @staticmethod
    def PAL(
        compatibility: Compatibility = Compatibility.IDEAL_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE,
    ) -> vs.VideoNode:
        settings = ColorBars.settings(
            Preset.PAL, compatibility, subblack, superwhite, iq, halfline
        )
        node = ColorBars.generate(settings)
        return ColorBars.metadata(
            node, duration=60, fpsnum=25, fpsden=1,
            field_based=vs.FIELD_TOP, blur=True,
            crop=None,
            format=vs.YUV422P10
        )

    @staticmethod
    def HD1080i(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        settings = ColorBars.settings(
            Preset.HD1080, compatibility, subblack, superwhite, iq, halfline
        )
        node = ColorBars.generate(settings)
        return ColorBars.metadata(
            node, duration=60, fpsnum=30_000, fpsden=1001,
            field_based=vs.FIELD_TOP, blur=True,
            crop=None,
            format=vs.YUV422P10
        )

    @staticmethod
    def HD1080p(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        settings = ColorBars.settings(
            Preset.HD1080, compatibility, subblack, superwhite, iq, halfline
        )
        node = ColorBars.generate(settings)
        return ColorBars.metadata(
            node, duration=60, fpsnum=24_000, fpsden=1001,
            field_based=vs.FIELD_PROGRESSIVE, blur=True,
            crop=None,
            format=vs.YUV422P10
        )

    @staticmethod
    def UHD_PQ(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.WHITE_75_BLACK_0,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        settings = ColorBars.settings(
            Preset.UHD_PQ, compatibility, subblack, superwhite, iq, halfline
        )
        node = ColorBars.generate(settings)
        return ColorBars.metadata(
            node, duration=60, fpsnum=60, fpsden=1001,
            field_based=vs.FIELD_PROGRESSIVE, blur=True,
            crop=None,
            format=vs.YUV422P10
        )

    @staticmethod
    def UHD_HLG(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.WHITE_75_BLACK_0,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        settings = ColorBars.settings(
            Preset.UHD_HLG, compatibility, subblack, superwhite, iq, halfline
        )
        node = ColorBars.generate(settings)
        return ColorBars.metadata(
            node, duration=60, fpsnum=50, fpsden=1,
            field_based=vs.FIELD_PROGRESSIVE, blur=True,
            crop=None,
            format=vs.YUV422P10
        )

    @staticmethod
    def UHD_2020(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.WHITE_75_BLACK_0,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        settings = ColorBars.settings(
            Preset.UHD_2020, compatibility, subblack, superwhite, iq, halfline
        )
        node = ColorBars.generate(settings)
        return ColorBars.metadata(
            node, duration=60, fpsnum=60_000, fpsden=1001,
            field_based=vs.FIELD_PROGRESSIVE, blur=True,
            crop=None,
            format=vs.YUV422P10
        )

    @staticmethod
    def Custom(
        resolution: Resolution = Resolution.HD_1080,
        format: vs.PresetVideoFormat = vs.YUV444P12,
        eotf: EOTF = EOTF.SDR,
        gamut: Gamut = Gamut.BT709,
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
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

        return ColorBars.generate(settings)
