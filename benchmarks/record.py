"""Canonical benchmark record schema (proposal §12).

Every field the proposal lists as a "保存項目" (saved item) is a first-class
column so that OmniAvatar 1.3B and every future model produce directly
comparable rows.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class BenchmarkRecord:
    # Identity
    provider: str
    model_version: str

    # Environment
    gpu: str
    vram_total_gb: float
    cuda_version: str

    # Output characteristics
    resolution: str  # e.g. "1280x720"
    fps: int
    video_length_seconds: float

    # Performance
    inference_seconds: float
    peak_vram_gb: float
    cpu_usage_percent: float
    output_file_size_mb: float

    # Reproducibility — full generation settings (sampler, steps, seed, …)
    generation_settings: dict[str, object] = field(default_factory=dict)

    # Stamped by the caller (scripts can't read the clock; see Workflow notes).
    timestamp: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    # Stable, explicit column order for CSV output.
    CSV_COLUMNS = (
        "timestamp",
        "provider",
        "model_version",
        "gpu",
        "vram_total_gb",
        "cuda_version",
        "resolution",
        "fps",
        "video_length_seconds",
        "inference_seconds",
        "peak_vram_gb",
        "cpu_usage_percent",
        "output_file_size_mb",
        "generation_settings",
    )
