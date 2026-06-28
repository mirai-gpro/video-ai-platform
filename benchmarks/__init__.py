"""Benchmark capture and reporting (proposal §§12-13).

Provides the canonical ``BenchmarkRecord`` schema, CSV/JSON persistence, a
human-readable report renderer, resource capture (``capture``), and the
``BenchmarkRecorder`` that the Pipeline uses to auto-record every successful
generation. GPU metrics (peak VRAM) populate when run on CUDA; on CPU they are
zero, so the wiring is exercised in CI without a GPU.
"""

from benchmarks.capture import ResourceSample, gpu_environment, measure
from benchmarks.record import BenchmarkRecord
from benchmarks.recorder import BenchmarkRecorder
from benchmarks.report import render_report
from benchmarks.store import append_csv, write_json

__all__ = [
    "BenchmarkRecord",
    "BenchmarkRecorder",
    "ResourceSample",
    "append_csv",
    "gpu_environment",
    "measure",
    "render_report",
    "write_json",
]
