"""High-fidelity runtime encoding for derivatives of immutable user leg art.

WebP keeps the complete 8-bit alpha channel lossless. Quality 82 preserves
the painted volume while avoiding the release cost of lossless RGB noise.
Always encode from the transformed source, never from a previous derivative.
"""
from pathlib import Path
import numpy as np
from PIL import Image


def save_user_derivative(image, target, *, method=6):
    """Atomically save and validate an RGBA derivative; return error metrics."""
    source = np.asarray(image.convert('RGBA'))
    target = Path(target)
    temporary = target.with_suffix('.tmp')
    try:
        image.save(temporary, format='WEBP', quality=82, method=method, exact=True)
        decoded = np.asarray(Image.open(temporary).convert('RGBA'))
        assert np.array_equal(source[:, :, 3], decoded[:, :, 3]), 'Alpha changed'
        opaque = source[:, :, 3] > 240
        error = np.abs(source[:, :, :3].astype(float) - decoded[:, :, :3])[opaque]
        metrics = {
            'encoding': 'WebP q82; lossless alpha',
            'alpha_exact': True,
            'opaque_rgb_mae': float(error.mean()),
            'opaque_rgb_p99': float(np.percentile(error, 99)),
            'opaque_rgb_max': float(error.max()),
        }
        assert metrics['opaque_rgb_mae'] < 1.5, metrics
        assert metrics['opaque_rgb_p99'] <= 5, metrics
        temporary.replace(target)
        return metrics
    finally:
        temporary.unlink(missing_ok=True)
