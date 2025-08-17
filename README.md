# vs-samples

```sh
pip install git+https://github.com/OpusGang/vs-samples.git --no-cache-dir -U
```

`vs-samples` is a small Python library for generating video test patterns, signals, and artifacts using [VapourSynth](http.www.vapoursynth.com/). It provides a collection of tools for creating various video samples for testing and analysis.

## Features

*   **Color Bars**: Generate standard color bar patterns for various video formats, including NTSC, PAL, HD, and UHD (PQ and HLG).
    * Colorbar generation requires https://github.com/ifb/vapoursynth-colorbars
*   **Signal Generation**: Create a variety of test signals and patterns, such as:
    *   Horizontal, vertical, circular, and corner ramps
    *   Spirals, checkerboards, and diamonds
    *   Rotating banding gradients and vortex patterns
*   **Artifact Simulation**: Simulate common video artifacts:
    *   JPEG compression artifacts with adjustable quality
    *   AVC-like block-based compression artifacts
    *   Dithering and quantization artifacts.
*   **NumPy Integration**: Context manager for processing vs.VideoNode's using NumPy for custom signal generation and analysis

TODO: More artifacts (Aliasing, Banding, Chromatic aberration, Sharpening)

## Modules

*   **`vssamples.colorbars`**: Functions and classes for generating SMPTE color bars.
*   **`vssamples.signals`**: Tools for creating various video test signals.
*   **`vssamples.artifacts`**: Classes for simulating video compression and quantization artifacts.
*   **`vssamples.wrapper`**: The `NumpyProcessor` class for (hopefully) seamless integration with NumPy and related libs.

## Usage

```python
import vapoursynth as vs
from vssamples.artifacts.jpeg import JpegArtifacts
from vssamples.wrapper import NumpyProcessor
import numpy as np

core = vs.core

# Simple animated ramp
class HorizontalRamp(NumpyProcessor):
    def __init__(self, format: vs.PresetVideoFormat = vs.GRAYS, static: bool = False): # noqa
        super().__init__(width=1000, height=256, length=300, format=format, static=static)

    def animate(self, n: int) -> np.ndarray:
        ramp = np.linspace(0, 1, self.width)
        ramp = np.tile(ramp, (self.height, 1))
        ramp *= n / (self.num_frames - 1)

        return ramp

# Generate ramp, add noise or whatever, convert to YUV420P8
ramp = HorizontalRamp(format=vs.GRAYS, static=False).generate()
noise = core.noise.Add(ramp, var=100, seed=422)
clip = core.resize.Bilinear(noise, format=vs.YUV420P8, matrix=vs.MATRIX_BT709)

# Apply JPEG artifacts 
jpeg = JpegArtifacts(clip, quality=25).process()

jpeg.set_output()
```
