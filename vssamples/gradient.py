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

def radial() -> vs.VideoNode:
    import numpy as np

    def _process_frame(n: int, f: vs.VideoNode) -> vs.VideoFrame:
        f1 = f
        fout = f1.copy()
        
        width = f.width
        height = f.height
        
        x = np.linspace(0, width, width)
        y = np.linspace(0, height, height)
        
        xx, yy = np.meshgrid(x, y)
        center_x, center_y = width // 2, height // 2
        
        radius = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
        
        radius_normalized = radius / np.max(radius)
        gradient = np.exp(-n * radius_normalized)
        
        np.copyto(np.asarray(fout[0]), gradient)

        return fout

    clip = core.std.BlankClip(None, 256, 256, format=vs.GRAYS, color=[0.1], length=48)
    clip = clip.std.ModifyFrame(clip, _process_frame)

    return clip
