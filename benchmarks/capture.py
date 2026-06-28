"""Runtime resource capture for benchmarks (model-agnostic).

Measures wall time, peak VRAM, and CPU usage around a generation call. GPU
metrics use ``torch`` when present and degrade gracefully to zero on CPU-only
hosts, so this module imports and runs without CUDA (and is exercised in
CPU-only CI).
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Iterator
from dataclasses import dataclass

import psutil

try:  # torch is an optional (GPU) dependency; absent on CPU-only CI.
    import torch
except Exception:  # noqa: BLE001
    torch = None  # type: ignore[assignment]


def _cuda_available() -> bool:
    return torch is not None and torch.cuda.is_available()


def gpu_environment() -> dict[str, object]:
    """Static environment facts recorded with every benchmark row."""
    if _cuda_available():
        idx = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(idx)
        return {
            "gpu": props.name,
            "vram_total_gb": round(props.total_memory / 1024**3, 2),
            "cuda_version": torch.version.cuda or "unknown",
        }
    return {"gpu": "cpu", "vram_total_gb": 0.0, "cuda_version": "n/a"}


@dataclass
class ResourceSample:
    """What :func:`measure` observed across a single generation call."""

    wall_seconds: float = 0.0
    peak_vram_gb: float = 0.0
    cpu_usage_percent: float = 0.0


@contextlib.contextmanager
def measure() -> Iterator[ResourceSample]:
    """Context manager that fills a :class:`ResourceSample` for the wrapped call.

    On exit it records wall time, system CPU% over the window, and peak CUDA
    VRAM (reset at entry). Fields stay at zero when no GPU is present.
    """
    sample = ResourceSample()
    if _cuda_available():
        torch.cuda.reset_peak_memory_stats()
    psutil.cpu_percent(interval=None)  # prime the rolling CPU% baseline
    start = time.perf_counter()
    try:
        yield sample
    finally:
        sample.wall_seconds = time.perf_counter() - start
        sample.cpu_usage_percent = psutil.cpu_percent(interval=None)
        if _cuda_available():
            sample.peak_vram_gb = round(torch.cuda.max_memory_allocated() / 1024**3, 2)
