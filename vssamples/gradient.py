from sympy import N
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

        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)

        xx, yy = np.meshgrid(x, y)

        radius = np.sqrt(xx ** 2 + yy ** 2)
        gradient = np.exp(-n * radius**2)
        
        np.copyto(np.asarray(fout[0]), gradient)

        return fout

    clip = core.std.BlankClip(None, 256, 256, format=vs.GRAYS, color=[0.1], length=24)
    clip = clip.std.ModifyFrame(clip, _process_frame)

    return clip

def spiral() -> vs.VideoNode:
    import numpy as np

    def _process_frame(n: int, f: vs.VideoNode) -> vs.VideoFrame:
        f1 = f
        fout = f1.copy()
        
        width = f.width
        height = f.height

        x = np.linspace(-10, 10, width)
        y = np.linspace(-10, 10, height)

        xx, yy = np.meshgrid(x, y)

        r = np.sqrt(xx ** 2 + yy ** 2)
        theta = np.arctan2(yy, xx)

        spiral = np.sin(r + theta)
        
        np.copyto(np.asarray(fout[0]), spiral)

        return fout

    clip = core.std.BlankClip(None, 256, 256, format=vs.GRAYS, color=[0.1], length=24)
    clip = clip.std.ModifyFrame(clip, _process_frame)

    return clip

def checkerboard() -> vs.VideoNode:
    import numpy as np

    def _process_frame(n: int, f: vs.VideoNode) -> vs.VideoFrame:
        f1 = f
        fout = f1.copy()
        
        width = f.width
        height = f.height

        pattern = np.zeros((height, width))
        pattern[::2, ::2] = 1
        pattern[1::2, 1::2] = 1
        
        np.copyto(np.asarray(fout[0]), pattern)

        return fout

    clip = core.std.BlankClip(None, 256, 256, format=vs.GRAYS, color=[0.1], length=1000)
    clip = clip.std.ModifyFrame(clip, _process_frame)

    return clip

def rotating_banding_gradients() -> vs.VideoNode:
    import numpy as np
    def _process_frame(n: int, f: vs.VideoNode) -> vs.VideoFrame:
        f1 = f
        fout = f1.copy()
        
        width = f.width
        height = f.height

        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)

        xx, yy = np.meshgrid(x, y)

        colors = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0]
        ])

        angle = n * np.pi / 180

        num_frames = 240
        peak_n = num_frames / 10
        peak_frame = num_frames // 2

        angle = n * np.pi / 180
        
        if n < peak_frame:
            n = peak_n * n / peak_frame
        else:
            n = peak_n * (num_frames - n) / (num_frames - peak_frame)
        
        # TODO pre-calc
        center_x = 0.5 * np.sin(angle + np.array([
            0, np.pi / 2, np.pi, 3 * np.pi / 2
        ]))

        center_y = 0.5 * np.cos(angle + np.array([
            0, np.pi / 2, np.pi, 3 * np.pi / 2
        ]))
        
        radius = np.sqrt((xx[:, :, np.newaxis] - center_x)**2 + (yy[:, :, np.newaxis] - center_y)**2)
        
        gradient = np.exp(-n * radius**2)
        
        rgb_gradient = gradient[:, :, :, np.newaxis] * colors
        
        rgb_gradient = np.sum(rgb_gradient, axis=2)
        
        rgb_gradient = (rgb_gradient - np.min(rgb_gradient)) / (np.max(rgb_gradient) - np.min(rgb_gradient))
        rgb_gradient = np.transpose(rgb_gradient, (2, 0, 1))

        for plane in range(fout.format.num_planes):
            np.copyto(np.asarray(fout[plane]), rgb_gradient[plane])

        return fout

    clip = core.std.BlankClip(None, 256, 256, format=vs.RGBS, length=240)
    clip = clip.std.ModifyFrame(clip, _process_frame)

    return clip

def spiral2() -> vs.VideoNode:
    import numpy as np

    def _process_frame(n: int, f: vs.VideoNode) -> vs.VideoFrame:
        f1 = f
        fout = f1.copy()
        
        width = f.width
        height = f.height

        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)

        xx, yy = np.meshgrid(x, y)

        radius_tl = np.sqrt((xx + 0.5)**2 + (yy + 0.5)**2)
        angle_tl = np.arctan2(yy + 0.5, xx + 0.5) + n * np.pi / 180
        gradient_tl = np.sin(radius_tl * 5 + angle_tl)

        np.copyto(np.asarray(fout[0]), gradient_tl)

        return fout

    clip = core.std.BlankClip(None, 256, 256, format=vs.GRAYS, color=[0.1], length=1000)
    clip = clip.std.ModifyFrame(clip, _process_frame)

    return clip
