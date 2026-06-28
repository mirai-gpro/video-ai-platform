"""Benchmark recorder + Pipeline capture wiring (CPU-only, no GPU/model)."""

from __future__ import annotations

import pytest

from benchmarks.capture import ResourceSample, measure
from benchmarks.recorder import BenchmarkRecorder
from pipeline import Pipeline, PipelineRequest
from providers.base import (
    GenerationMode,
    GenerationRequest,
    GenerationResult,
    NotYetImplementedError,
    ProviderInfo,
    VideoProvider,
    VideoSpec,
)

CPU_ENV = {"gpu": "cpu", "vram_total_gb": 0.0, "cuda_version": "n/a"}
FIXED_CLOCK = lambda: "2026-06-28T00:00:00+00:00"  # noqa: E731


def _result(out_path, size_bytes=2 * 1024 * 1024):
    out_path.write_bytes(b"x" * size_bytes)
    return GenerationResult(
        output_path=out_path,
        provider="skyreels",
        model_version="V3",
        mode=GenerationMode.TEXT_TO_VIDEO,
        spec=VideoSpec(width=1280, height=720, fps=24, duration_seconds=15.0),
        inference_seconds=12.5,
        metrics={"steps": 30, "seed": 7},
    )


def test_measure_runs_without_gpu():
    with measure() as sample:
        sum(range(1000))
    assert isinstance(sample, ResourceSample)
    assert sample.wall_seconds >= 0.0
    assert sample.peak_vram_gb == 0.0  # no CUDA in CI


def test_recorder_builds_expected_record(tmp_path):
    rec = BenchmarkRecorder(tmp_path, environment=CPU_ENV, clock=FIXED_CLOCK)
    sample = ResourceSample(wall_seconds=13.0, peak_vram_gb=0.0, cpu_usage_percent=11.0)
    record = rec.build(_result(tmp_path / "v.mp4"), sample)
    assert record.provider == "skyreels"
    assert record.resolution == "1280x720"
    assert record.inference_seconds == 12.5  # provider value preferred over wall
    assert record.output_file_size_mb == 2.0
    assert record.generation_settings == {"steps": 30, "seed": 7}
    assert record.gpu == "cpu"


def test_recorder_persists_csv_and_json(tmp_path):
    rec = BenchmarkRecorder(tmp_path, environment=CPU_ENV, clock=FIXED_CLOCK)
    out = rec.record(_result(tmp_path / "v.mp4"), ResourceSample(cpu_usage_percent=5.0))
    assert out is not None
    csv_text = (tmp_path / "benchmarks.csv").read_text()
    assert csv_text.splitlines()[0].startswith("timestamp,provider")
    assert "skyreels" in csv_text
    assert any(p.suffix == ".json" for p in tmp_path.iterdir())


def test_disabled_recorder_is_noop(tmp_path):
    rec = BenchmarkRecorder(tmp_path, enabled=False, environment=CPU_ENV, clock=FIXED_CLOCK)
    assert rec.record(_result(tmp_path / "v.mp4"), ResourceSample()) is None
    assert not (tmp_path / "benchmarks.csv").exists()


class _FakeProvider(VideoProvider):
    def __init__(self, out_path):
        self._out = out_path

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo("fake", "0", frozenset({GenerationMode.TEXT_TO_VIDEO}))

    def generate(self, req: GenerationRequest) -> GenerationResult:
        self._require(GenerationMode.TEXT_TO_VIDEO)
        self._out.write_bytes(b"x" * 1024)
        return GenerationResult(
            output_path=self._out,
            provider="fake",
            model_version="0",
            mode=GenerationMode.TEXT_TO_VIDEO,
            spec=req.spec,
            inference_seconds=0.1,
        )


def test_pipeline_records_on_success(tmp_path):
    out = tmp_path / "o.mp4"
    recorder = BenchmarkRecorder(tmp_path, environment=CPU_ENV, clock=FIXED_CLOCK)
    pipe = Pipeline(provider_factory=lambda name: _FakeProvider(out), recorder=recorder)
    pipe.run(
        PipelineRequest("fake", GenerationMode.TEXT_TO_VIDEO, GenerationRequest(output_path=out))
    )
    assert (tmp_path / "benchmarks.csv").exists()


def test_pipeline_does_not_record_on_failure(tmp_path):
    # SkyReels design-phase generate() raises -> no benchmark row written.
    recorder = BenchmarkRecorder(tmp_path, environment=CPU_ENV, clock=FIXED_CLOCK)
    pipe = Pipeline(recorder=recorder)  # real registry -> skyreels
    with pytest.raises(NotYetImplementedError):
        pipe.run(PipelineRequest("skyreels", GenerationMode.TEXT_TO_VIDEO, GenerationRequest()))
    assert not (tmp_path / "benchmarks.csv").exists()
