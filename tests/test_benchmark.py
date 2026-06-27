"""Benchmark schema, persistence, and report rendering tests."""

from __future__ import annotations

from benchmarks import BenchmarkRecord, append_csv, render_report, write_json


def _record(**over) -> BenchmarkRecord:
    base = dict(
        provider="skyreels",
        model_version="V3",
        gpu="RTX4090",
        vram_total_gb=24.0,
        cuda_version="12.4",
        resolution="1280x720",
        fps=24,
        video_length_seconds=15.0,
        inference_seconds=492.0,
        peak_vram_gb=21.4,
        cpu_usage_percent=18.0,
        output_file_size_mb=118.0,
        generation_settings={"steps": 30, "seed": 42},
        timestamp="2026-06-27T00:00:00Z",
    )
    base.update(over)
    return BenchmarkRecord(**base)


def test_csv_roundtrip(tmp_path):
    p = append_csv(_record(), tmp_path / "runs.csv")
    text = p.read_text()
    assert "provider" in text.splitlines()[0]
    assert "skyreels" in text


def test_json_write(tmp_path):
    p = write_json(_record(), tmp_path / "run.json")
    assert '"provider": "skyreels"' in p.read_text()


def test_report_with_comparison():
    sky = _record(inference_seconds=492.0, peak_vram_gb=21.4, output_file_size_mb=118.0)
    multitalk = _record(
        provider="multitalk",
        model_version="baseline",
        inference_seconds=712.0,
        peak_vram_gb=18.6,
        output_file_size_mb=100.0,
    )
    report = render_report(sky, baseline=multitalk)
    assert "Benchmark Report" in report
    assert "Faster" in report
    assert "VRAM" in report
