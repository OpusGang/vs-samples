from enum import Enum
import vapoursynth as vs
core = vs.core
from .enums import Compatibility, HalfLine, HDR, IQ, Resolution, SubBlack, SuperWhite, WCG

class ColorBars:
    """
    ColorBars is a filter for generating test signals. The output is a single frame of color bars according to SMPTE RP 219-1, 219-2, or ITU-R BT.2111-2. For NTSC, the bar pattern is described in SMPTE EG 1. For PAL, EBU bars are generated.

    SMPTE RP 219-2 gives explicit color bar values in 10-bit and 12-bit Y'Cb'Cr'. ITU BT.2111-2 gives explicit color bar values in 10-bit and 12-bit R'G'B'. These values are used directly instead of being generated at runtime.

    Either vs.YUV444P10 or vs.YUV444P12 are supported in SDR mode. Either vs.RGB30 or vs.RGB36 are supported in HDR mode. This is because SMPTE defines bar values in terms of Y'Cb'Cr' and ITU uses R'G'B'.

    """
    class Preset(Enum):
        """
        Enforced defaults
        """

        NTSC = {
            "resolution": Resolution.NTSC_BT601,
            "format": vs.YUV444P12,
            "compatibility": Compatibility.EVEN_DIMENSIONS
        }

        PAL = {
            "resolution": Resolution.PAL_BT601,
            "format": vs.YUV444P12
        }

        HD1080 = {
            "resolution": Resolution.HD_1080,
            "format": vs.YUV444P10
        }

        UHD = {
            "resolution": Resolution.UHD_4K,
            "format": vs.RGB36,
            "hdr": HDR.PQ,
            "wcg": WCG.BT2020
        }

        HLG_UHD = {
            "resolution": Resolution.UHD_4K,
            "format": vs.RGB30,
            "hdr": HDR.HLG
        }

    @staticmethod
    def NTSC(
        compatibility: Compatibility = Compatibility.IDEAL_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate NTSC color bars."""
        settings = ColorBars._generate_settings(ColorBars.Preset.NTSC, compatibility, subblack, superwhite, iq, halfline)
        return ColorBars._generate(**settings)

    @staticmethod
    def PAL(
        compatibility: Compatibility = Compatibility.IDEAL_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate PAL color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.PAL, compatibility, subblack, superwhite, iq, halfline
        )
        return ColorBars._generate(**settings)

    @staticmethod
    def HD1080i(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate 1080i color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.HD1080, compatibility, subblack, superwhite, iq, halfline
        )
        return ColorBars._generate(**settings).std.SetFrameProp(prop="_FieldBased", intval=vs.FIELD_TOP)

    @staticmethod
    def HD1080p(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate 1080p color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.HD1080, compatibility, subblack, superwhite, iq, halfline
        )
        return ColorBars._generate(**settings)

    @staticmethod
    def UHD(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.WHITE_75_BLACK_0,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate UHD color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.UHD, compatibility, subblack, superwhite, iq, halfline
        )
        return ColorBars._generate(**settings)

    @staticmethod
    def HLG_UHD(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate HLG color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.HLG_UHD, compatibility, subblack, superwhite, iq, halfline
        )
        return ColorBars._generate(**settings)

    @staticmethod
    def custom(
        resolution: Resolution = Resolution.HD_1080,
        format: vs.VideoFormat = vs.YUV444P12,
        hdr: HDR = HDR.SDR,
        wcg: WCG = WCG.BT709,
        compatibility: Compatibility = Compatibility.IGNORE_BLANKING,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate custom color bars."""
        settings = {
            "resolution": resolution,
            "format": format,
            "hdr": hdr,
            "wcg": wcg,
            "compatibility": compatibility,
            "subblack": subblack,
            "superwhite": superwhite,
            "iq": iq,
            "halfline": halfline
        }
        return ColorBars._generate(**settings)

    @staticmethod
    def _generate_settings(preset: Preset, compatibility: Compatibility, subblack: SubBlack, superwhite: SuperWhite, iq: IQ, halfline: HalfLine) -> dict:
        return {
            **preset.value,
            "compatibility": compatibility,
            "subblack": subblack,
            "superwhite": superwhite,
            "iq": iq,
            "halfline": halfline
        }

    @staticmethod
    def _generate(
        resolution: Resolution = Resolution.HD_1080,
        format: vs.VideoFormat = vs.YUV444P12,
        hdr: HDR = HDR.SDR,
        wcg: WCG = WCG.BT709,
        compatibility: Compatibility = Compatibility.IGNORE_BLANKING,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        return core.colorbars.ColorBars(
            resolution=resolution,
            format=format,
            hdr=hdr,
            wcg=wcg,
            compatability=compatibility,
            subblack=subblack,
            superwhite=superwhite,
            iq=iq,
            halfline=halfline
        )
