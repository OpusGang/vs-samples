from enum import Enum
import vapoursynth as vs
core = vs.core
from .enums import Compatibility, Gamut, HalfLine, EOTF, IQ, Resolution, SubBlack, SuperWhite

class Generator:
    # TODO
    # Move this into the actual implementation
    # NTSC().preset -> return dict with enforced values
    class Preset(Enum):
        """
        Enforced defaults
        """

        NTSC = {
            "resolution": Resolution.NTSC_BT601,
            "format": vs.YUV444P12,
        }

        PAL = {
            "resolution": Resolution.PAL_BT601,
            "format": vs.YUV444P12
        }

        HD1080 = {
            "resolution": Resolution.HD_1080,
            "format": vs.YUV444P10
        }

        UHD_PQ = {
            "resolution": Resolution.UHD_4K,
            "format": vs.RGB36,
            "EOTF": EOTF.PQ,
        }
        """ITU-R BT.2111-2"""
        UHD_HLG = {
            "resolution": Resolution.UHD_4K,
            "format": vs.RGB30,
            "EOTF": EOTF.HLG,
        }
        """ITU-R BT.2111-2"""
        UHD_2020 = {
            "resolution": Resolution.UHD_4K,
            "format": vs.YUV444P12,
            "EOTF": EOTF.SDR,
            "gamut": Gamut.BT2020
        }
        """ITU-R BT.2111-2
        The readme stipulates that ITU-R BT.2111-2 should be R'G'B.\n
        However, the plugin limits SDR generation to Y'CbCr.
        Either these aren't compliant or a plugin oversight

        """

    @staticmethod
    def _generate_settings(
        preset: Preset,
        compatibility: Compatibility,
        subblack: SubBlack,
        superwhite: SuperWhite,
        iq: IQ,
        halfline: HalfLine
    ) -> dict:

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
        EOTF: EOTF = EOTF.SDR,
        gamut: Gamut = Gamut.BT709,
        compatibility: Compatibility = Compatibility.IGNORE_BLANKING,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:

        return core.colorbars.ColorBars(
            resolution=resolution,
            format=format,
            hdr=EOTF,
            wcg=gamut,
            compatability=compatibility,
            subblack=subblack,
            superwhite=superwhite,
            iq=iq,
            halfline=halfline
        )

    @staticmethod
    def metadata(
        clip: vs.VideoNode, 
        duration: int = 60, 
        fpsnum: int = 24000, 
        fpsden: int = 1001, 
        field_based: int = vs.FIELD_PROGRESSIVE,
        blur: bool = True,
        crop: dict = dict(left=0, right=0, top=0, bottom=0),
        format: vs.PresetVideoFormat = vs.YUV422P10
    ) -> vs.VideoNode:
        """
        Simple metdata wrapper. Intended for internal use.
        duration in seconds
        
        Note on blur:

        Note that bar transitions are not instant.
        RP 219 requires proper shaping.
        Rise and fall times are 4 samples (10% to 90%) and +/-10% of the nominal value and the shape is recommended to be an integrated sine-squared pulse.
        Shaping may be integrated into ColorBars later, but for now you can apply a horizontal blur.
        
        """
        clip = clip.std.SetFrameProp(prop="_FieldBased", intval=field_based)
        
        if crop:
            clip = clip.std.Crop(**crop)

        if blur:
            clip = clip.std.Convolution(mode="h", matrix=[1, 2, 4, 2, 1])

        try:
            clip = clip.resize.Point(format=format)
        except Exception:
            clip = clip.resize.Point(format=format, matrix_s="2020ncl")

        clip = clip * (duration * fpsnum // fpsden)
        return clip.std.AssumeFPS(fpsnum=fpsnum, fpsden=fpsden)



class ColorBars(Generator):
    """
    ColorBars is a filter for generating test signals. The output is a single frame of color bars according to SMPTE RP 219-1, 219-2, or ITU-R BT.2111-2. For NTSC, the bar pattern is described in SMPTE EG 1. For PAL, EBU bars are generated.

    SMPTE RP 219-2 gives explicit color bar values in 10-bit and 12-bit Y'Cb'Cr'. ITU BT.2111-2 gives explicit color bar values in 10-bit and 12-bit R'G'B'. These values are used directly instead of being generated at runtime.

    Either vs.YUV444P10 or vs.YUV444P12 are supported in SDR mode. Either vs.RGB30 or vs.RGB36 are supported in HDR mode. This is because SMPTE defines bar values in terms of Y'Cb'Cr' and ITU uses R'G'B'.

    """
        
    @staticmethod
    def NTSC(
        compatibility: Compatibility = Compatibility.IDEAL_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE,
    ) -> vs.VideoNode:
        """Generate NTSC color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.NTSC, compatibility, subblack, superwhite, iq, halfline
        )
        settings: vs.VideoNode = ColorBars._generate(**settings)
        return ColorBars.metadata(
            settings,
            60,
            3000,
            1001,
            vs.FIELD_BOTTOM,
            True,
            dict(left=4, right=4),
            vs.YUV422P10
        )

    @staticmethod
    def PAL(
        compatibility: Compatibility = Compatibility.IDEAL_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE,
    ) -> vs.VideoNode:
        """Generate PAL color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.PAL, compatibility, subblack, superwhite, iq, halfline
        )
        settings = ColorBars._generate(**settings)
        return ColorBars.metadata(
            settings,
            60,
            25,
            1,
            vs.FIELD_TOP,
            True,
            False,
            vs.YUV422P10
        )

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
        settings = ColorBars._generate(**settings)
        return ColorBars.metadata(
            settings,
            60,
            30_000,
            1001,
            vs.FIELD_TOP,
            True,
            False,
            vs.YUV422P10
        )

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
        settings = ColorBars._generate(**settings)
        return ColorBars.metadata(
            settings,
            60,
            24_000,
            1001,
            vs.FIELD_PROGRESSIVE,
            True,
            False,
            vs.YUV422P10
        )

    @staticmethod
    def UHD_PQ(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.WHITE_75_BLACK_0,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate UHD ITU-R BT.2111-2 color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.UHD_PQ, compatibility, subblack, superwhite, iq, halfline
        )
        settings = ColorBars._generate(**settings)
        return ColorBars.metadata(
            settings,
            60,
            60,
            1001,
            vs.FIELD_PROGRESSIVE,
            True,
            False,
            vs.YUV422P10
        )

    @staticmethod
    def UHD_HLG(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.WHITE_75_BLACK_0,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate UHD ARIB STD-B67 color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.UHD_HLG, compatibility, subblack, superwhite, iq, halfline
        )
        settings = ColorBars._generate(**settings)
        return ColorBars.metadata(
            settings,
            60,
            50,
            1,
            vs.FIELD_PROGRESSIVE,
            True,
            False,
            vs.YUV422P10
        )

    @staticmethod
    def UHD_2020(
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.WHITE_75_BLACK_0,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """Generate UHD BT.2020 color bars."""
        settings = ColorBars._generate_settings(
            ColorBars.Preset.UHD_2020, compatibility, subblack, superwhite, iq, halfline
        )
        settings = ColorBars._generate(**settings)
        return ColorBars.metadata(
            settings,
            60,
            60_000,
            1001,
            vs.FIELD_PROGRESSIVE,
            True,
            False,
            vs.YUV422P10
        )

    @staticmethod
    def Custom(
        resolution: Resolution = Resolution.HD_1080,
        format: vs.VideoFormat = vs.YUV444P12,
        EOTF: EOTF = EOTF.SDR,
        gamut: Gamut = Gamut.BT709,
        compatibility: Compatibility = Compatibility.EVEN_DIMENSIONS,
        subblack: SubBlack = SubBlack.TRUE,
        superwhite: SuperWhite = SuperWhite.TRUE,
        iq: IQ = IQ.NEG_I_POS_Q,
        halfline: HalfLine = HalfLine.FALSE
    ) -> vs.VideoNode:
        """
        Generate custom color bars. There are some restrictions,
        check the various docstrings or the original readme if unsure https://github.com/ifb/vapoursynth-colorbars
        """        
        settings = {
            "resolution": resolution,
            "format": format,
            "EOTF": EOTF,
            "gamut": gamut,
            "compatibility": compatibility,
            "subblack": subblack,
            "superwhite": superwhite,
            "iq": iq,
            "halfline": halfline,
        }
        return ColorBars._generate(**settings)
