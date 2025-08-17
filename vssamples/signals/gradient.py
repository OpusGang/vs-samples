import vapoursynth as vs
import numpy as np
from dataclasses import dataclass

from wrapper.manager import NumpyProcessor

core = vs.core


class HorizontalRamp(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        ramp = np.linspace(0, 1, self.width)
        ramp = np.tile(ramp, (self.height, 1))
        ramp *= n / (self.num_frames - 1)

        return ramp

class VerticalRamp(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        ramp = np.linspace(0, 1, self.height)
        ramp = np.tile(ramp, (self.width, 1)).T
        ramp *= n / (self.num_frames - 1)
        return ramp

class CornerRamp(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        x = np.linspace(0, 1, self.width)
        y = np.linspace(0, 1, self.height)
        xx, yy = np.meshgrid(x, y)
        ramp = xx * yy
        ramp *= n / (self.num_frames - 1)
        return ramp

class CircularRamp(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        x = np.linspace(-1, 1, self.width)
        y = np.linspace(-1, 1, self.height)
        xx, yy = np.meshgrid(x, y)
        ramp = np.sqrt(xx**2 + yy**2)
        ramp = (ramp - np.min(ramp)) / (np.max(ramp) - np.min(ramp))
        ramp *= n / (self.num_frames - 1)
        return ramp

class Spiral(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        x = np.linspace(-10, 10, self.width)
        y = np.linspace(-10, 10, self.height)

        xx, yy = np.meshgrid(x, y)

        r = np.sqrt(xx ** 2 + yy ** 2)

        spiral = np.sin(r - n)
        
        return spiral

class Checkerboard(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        pattern = np.zeros((self.height, self.width))
        pattern[::2, ::2] = 1
        pattern[1::2, 1::2] = 1
        
        return pattern

class Diamond(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        x = np.linspace(-1, 1, self.width)
        y = np.linspace(-1, 1, self.height)
        xx, yy = np.meshgrid(x, y)
        
        gradient = 1 - np.abs(xx) - np.abs(yy)
        gradient = np.clip(gradient, 0, 1)
        if not self.static:
            gradient *= n / (self.num_frames - 1)
        
        return gradient

class RotatingBandingGradients(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.RGBS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        x = np.linspace(-1, 1, self.width)
        y = np.linspace(-1, 1, self.height)

        xx, yy = np.meshgrid(x, y)

        angle = n * np.pi / 180

        peak_n = self.num_frames / 10
        peak_frame = self.num_frames // 2

        if not self.static:
            if n < peak_frame:
                n = peak_n * n / peak_frame # type: ignore
            else:
                n = peak_n * (self.num_frames - n) / (self.num_frames - peak_frame) # type: ignore
        
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

class Vortex(NumpyProcessor):
    def __init__(self, width: int, height: int, length: int, format: vs.PresetVideoFormat = vs.RGBS, static: bool = False): # noqa
        super().__init__(width=width, height=height, length=length, format=format, static=static)
    
    def animate(self, n: int) -> np.ndarray:
        x = np.linspace(-1, 1, self.width)
        y = np.linspace(-1, 1, self.height)
        xx, yy = np.meshgrid(x, y)
        
        angle = np.arctan2(yy, xx)
        radius = np.sqrt(xx**2 + yy**2)
        
        vortex_r = np.sin(angle * 5 + radius * 10 - n / 10)
        vortex_g = np.sin(angle * 5 + radius * 10 - n / 10 + 2 * np.pi / 3)
        vortex_b = np.sin(angle * 5 + radius * 10 - n / 10 + 4 * np.pi / 3)
        
        vortex = np.stack((vortex_r, vortex_g, vortex_b), axis=-1)
        vortex = (vortex + 1) / 2
        if not self.static:
            vortex *= n / (self.num_frames - 1)
        
        mask = np.exp(-radius**2 * 5)
        vortex *= mask[..., np.newaxis]

        return vortex
