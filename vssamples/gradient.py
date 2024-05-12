import vapoursynth as vs
core = vs.core
import numpy as np

class NumpyToVideoNode:
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS):
        self.width = width
        self.height = height
        self.length = length
        self.format = format
        
        self.planes = 1 if self.format is vs.GRAYS else 3 
        self.clip = vs.core.std.BlankClip(
            width=width,
            height=height,
            format=self.format,
            color=[0] * self.planes,
            length=length
        )
        
    def _process_frame(self, n: int, f: vs.VideoNode) -> vs.VideoFrame:
        fout = f.copy()
        
        ramp = self._generate(n)
        
        if fout.format.num_planes == 1:
            np.copyto(np.asarray(fout[0]), ramp)
        else:
            for i in range(fout.format.num_planes):
                np.copyto(np.asarray(fout[i]), ramp[..., i])

        return fout

    def _generate(self, n: int) -> np.ndarray:
        raise NotImplementedError("subclass broken")
    
    def generate(self) -> vs.VideoNode:
        processed_clip = self.clip.std.ModifyFrame(
            clips=self.clip,
            selector=self._process_frame
            )

        return processed_clip

class HorizontalRamp(NumpyToVideoNode):
    def _generate(self, n: int) -> np.ndarray:
        ramp = np.linspace(0, 1, self.width)
        ramp = np.tile(ramp, (self.height, 1))
        ramp *= n / (self.length - 1)
        return ramp

class VerticalRamp(NumpyToVideoNode):
    def _generate(self, n: int) -> np.ndarray:
        ramp = np.linspace(0, 1, self.height)
        ramp = np.repeat(ramp, self.width).reshape(self.height, self.width)
        ramp *= n / (self.length - 1)
        return ramp

class CornerRamp(NumpyToVideoNode):
    def _generate(self, n: int) -> np.ndarray:
        x = np.linspace(0, 1, self.width)
        y = np.linspace(0, 1, self.height)
        xx, yy = np.meshgrid(x, y)
        ramp = xx * yy
        ramp *= n / (self.length - 1)
        return ramp

class CircularRamp(NumpyToVideoNode):
    def _generate(self, n: int) -> np.ndarray:
        x = np.linspace(-1, 1, self.width)
        y = np.linspace(-1, 1, self.height)
        xx, yy = np.meshgrid(x, y)
        ramp = np.sqrt(xx**2 + yy**2)
        ramp = (ramp - np.min(ramp)) / (np.max(ramp) - np.min(ramp))
        ramp *= n / (self.length - 1)
        return ramp

class Spiral(NumpyToVideoNode):
    def _generate(self, n: int) -> np.ndarray:
        x = np.linspace(-10, 10, self.width)
        y = np.linspace(-10, 10, self.height)

        xx, yy = np.meshgrid(x, y)

        r = np.sqrt(xx ** 2 + yy ** 2)

        spiral = np.sin(r - n)
        
        return spiral

class Checkerboard(NumpyToVideoNode):
    def _generate(self, n: int) -> np.ndarray:
        pattern = np.zeros((self.height, self.width))
        pattern[::2, ::2] = 1
        pattern[1::2, 1::2] = 1
        
        return pattern

class RotatingBandingGradients(NumpyToVideoNode):
    def __init__(self, width: int, height: int, length: int):
        super().__init__(width, height, length, format=vs.RGBS)

    def _generate(self, n: int, format=vs.RGBS) -> np.ndarray:
        x = np.linspace(-1, 1, self.width)
        y = np.linspace(-1, 1, self.height)

        xx, yy = np.meshgrid(x, y)

        angle = n * np.pi / 180

        num_frames = 240
        peak_n = num_frames / 10
        peak_frame = num_frames // 2

        angle = n * np.pi / 180
        
        if n < peak_frame:
            n = peak_n * n / peak_frame
        else:
            n = peak_n * (num_frames - n) / (num_frames - peak_frame)
        
        c = n / 10

        colors = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 1]
        ])

        angle_array = angle + np.array([0, np.pi / 2, np.pi, 3 * np.pi / 2])

        center_x = c / 3 * np.sin(angle_array)
        center_y = c / 3 * np.cos(angle_array)

        radius = np.sqrt((xx[:, :, np.newaxis] - center_x)**2 + (yy[:, :, np.newaxis] - center_y)**2)
        
        gradient = np.exp(-n * radius**2)
        
        rgb_gradient = gradient[:, :, :, np.newaxis] * colors
        
        rgb_gradient = np.sum(rgb_gradient, axis=2)

        rgb_gradient = (rgb_gradient - np.min(rgb_gradient)) / (np.max(rgb_gradient) - np.min(rgb_gradient) + 1e-8)
        
        return rgb_gradient
