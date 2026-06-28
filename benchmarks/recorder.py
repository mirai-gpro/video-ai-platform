"""BenchmarkRecorder — turn a generation result + resource sample into a record.

Builds a canonical :class:`BenchmarkRecord` from a Provider's
``GenerationResult`` and the measured :class:`ResourceSample`, then persists it
(CSV append + per-run JSON). This is model-agnostic: it reads only the shared
contract, so every Provider produces comparable rows.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from benchmarks.capture import ResourceSample, gpu_environment
from benchmarks.record import BenchmarkRecord
from benchmarks.report import render_report
from benchmarks.store import append_csv, write_json
from providers.base import GenerationResult


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _file_size_mb(path: Path | None) -> float:
    try:
        if path and Path(path).exists():
            return round(Path(path).stat().st_size / 1024**2, 2)
    except OSError:
        pass
    return 0.0


class BenchmarkRecorder:
    """Builds and persists benchmark records for successful generations."""

    def __init__(
        self,
        output_dir: str | Path = "benchmarks/runs",
        *,
        enabled: bool = True,
        environment: dict[str, object] | None = None,
        clock: Callable[[], str] = _utc_now_iso,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.enabled = enabled
        # Environment is static for a process; capture once. Injectable for tests.
        self._env = environment if environment is not None else gpu_environment()
        self._clock = clock

    def build(self, result: GenerationResult, sample: ResourceSample) -> BenchmarkRecord:
        spec = result.spec
        settings = dict(result.metrics)
        return BenchmarkRecord(
            provider=result.provider,
            model_version=result.model_version,
            gpu=str(self._env.get("gpu", "unknown")),
            vram_total_gb=float(self._env.get("vram_total_gb", 0.0)),
            cuda_version=str(self._env.get("cuda_version", "n/a")),
            resolution=f"{spec.width}x{spec.height}",
            fps=spec.fps,
            video_length_seconds=spec.duration_seconds,
            # Prefer the Provider's measured inference time; fall back to wall time.
            inference_seconds=result.inference_seconds or sample.wall_seconds,
            # Prefer the measured peak VRAM; fall back to anything the Provider reported.
            peak_vram_gb=sample.peak_vram_gb or float(settings.get("peak_vram_gb", 0.0)),
            cpu_usage_percent=sample.cpu_usage_percent,
            output_file_size_mb=_file_size_mb(result.output_path),
            generation_settings=settings,
            timestamp=self._clock(),
        )

    def record(self, result: GenerationResult, sample: ResourceSample) -> BenchmarkRecord | None:
        """Build, persist (CSV + JSON), and return the record. No-op if disabled."""
        if not self.enabled:
            return None
        rec = self.build(result, sample)
        append_csv(rec, self.output_dir / "benchmarks.csv")
        stamp = "".join(c for c in rec.timestamp if c.isdigit())
        write_json(rec, self.output_dir / f"{rec.provider}-{stamp}.json")
        return rec

    def report(
        self,
        result: GenerationResult,
        sample: ResourceSample,
        baseline: BenchmarkRecord | None = None,
    ) -> str:
        return render_report(self.build(result, sample), baseline=baseline)
