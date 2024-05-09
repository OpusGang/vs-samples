from enum import IntEnum

class Resolution(IntEnum):
    NTSC_BT601 = 0
    PAL_BT601 = 1
    HD_720P = 2
    HD_1080 = 3
    UHD_2K = 4
    UHD_4K = 5
    UHD_4K_DCI = 6
    UHD_8K = 7
    NTSC_4FSC = 8
    PAL_4FSC = 9


class HDR(IntEnum):
    SDR = 0
    HLG = 1
    PQ = 2
    PQ_FULL_RANGE = 3


class WCG(IntEnum):
    """
    Enable ITU-R BT.2020, aka wide color gamut. Only valid with UHD and higher resolutions. Required for 8K, although ColorBars does not enforce this and will generate 8K Rec.709 with a warning. No effect when hdr > 0.
    """
    BT709 = 0
    BT2020 = 1


class Compatibility(IntEnum):
    """
    Controls how pedantic you want to be, especially for legacy NTSC/PAL systems.  No effect when hdr > 0.

    NTSC and PAL both have an active digital width of 720 pixels when using BT.601 (13.5 MHz) sampling.

    525-line NTSC has 710.85x484 active picture plus two half lines. 712 is used in modes 0 and 1 with 4 blanking pixels on each side.

    625-line PAL has 702x574 active picture plus two half lines.  702 is used in mode 0, with 9 blanking pixels on each side.  704 is used in mode 1, with 8 blanking pixels on each side.

    4fsc NTSC (14.318 MHz) has 768 digital active samples.  757.27 samples are active (52+8/9 us).  Mode 0 is 758 wide with 5 blanking pixels on each side.  Mode 1 is 760 wide with 4 blanking pixels on each side.

    4fsc PAL (17.734 MHz) has 948 digital active samples.  922 samples are active (52 us) in modes 0 and 1 with 12 blanking pixels on each side.

    NTSC modes 0 and 1 have 486 active lines.  DVB/ATSC/DV/HDMI use 480 lines, like in mode 2.

    """
    IDEAL_DIMENSIONS = 0
    """
    Use ideal bar dimensions, rounded to the nearest integer.  Bar widths are specified as fractions of the active picture and can be odd.
    """
    EVEN_DIMENSIONS = 1
    """
    Use even bar dimensions to facilitate chroma subsampling.  Conversions to YUV420 or YUV422 later may be problematic otherwise.
    """
    IGNORE_BLANKING = 2
    """
    For NTSC and PAL, ignore blanking.  The entire line contains the active image.  For HD and higher resolutions, use dimensions that are compatible with chroma subsampling and with 4:3 center-cut downconversion.  For UHD/4K and 8K, use multiples of four and eight respectively for 2SI compatibility.
    """


class SubBlack(IntEnum):
    """
    Controls whether to generate the below black ramp in the middle third of the first 0% black patch on the bottom row. Only valid with HD and higher resolutions. No effect when hdr > 0.
    """
    FALSE = 0
    TRUE = 1


class SuperWhite(IntEnum):
    """
    Controls whether to generate an above white ramp in the middle third of the 100% white chip on the bottom row. Only valid with HD and higher resolutions. No effect when hdr > 0.
    """
    FALSE = 0
    TRUE = 1


class IQ(IntEnum):
    """
    Controls the second patch of rows 2 and 3. Only valid with HD and higher resolutions. No effect when hdr > 0. Mode 1 and 2 are not valid if wcg=1.
    
    The +I/-I/+Q values are conveniently specified in RP 219 for systems with Rec.709 primaries (HD up to 4K). For NTSC, the values were calculated and later verified to match an Evertz SDI test signal generator. Note that converting from YUV to RGB will produce out of range values.
    
    """
    WHITE_75_BLACK_0 = 0
    """
    75% white and 0% black
    """
    NEG_I_POS_Q = 1
    """
    -I and +Q
    """
    POS_I_BLACK_0 = 2
    """
    +I and 0% black
    """
    WHITE_100_BLACK_0 = 3
    """
    100% white and 0% black
    """


class HalfLine(IntEnum):
    """
    For ultimate pedantry, perform halfline blanking on analog lines 284/263 (NTSC) and 23/623 (PAL). Applies to NTSC and PAL resolutions only.
    """
    FALSE = 0
    TRUE = 1
