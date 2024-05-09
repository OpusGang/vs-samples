from vstools import vs, core

def gradient(height: int = 50) -> vs.VideoNode:

    clip = [core.std.BlankClip(
        height=1,
        width=1,
        format=vs.GRAYS,
        color=i / 1000,
        length=1,
        keep=True
    ) for i in range(0, 1001)]

    splice = core.std.StackHorizontal(clip)
    splice = splice.std.SetFrameProp(prop="_ColorRange", intval=vs.ColorRange.RANGE_FULL)
    splice = splice.resize.Bilinear(height=height)

    return splice
