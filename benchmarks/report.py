"""Human-readable benchmark report (proposal §13).

Renders a single run, optionally with a comparison against a baseline record
(e.g. OmniAvatar 1.3B baseline vs an optimized setting, or two models once a second
Provider exists) showing relative speed, VRAM, and bitrate.
"""

from __future__ import annotations

from benchmarks.record import BenchmarkRecord


def _fmt_duration(seconds: float) -> str:
    m, s = divmod(int(round(seconds)), 60)
    return f"{m}m {s:02d}s" if m else f"{s}s"


def _bitrate_mbps(rec: BenchmarkRecord) -> float:
    if rec.video_length_seconds <= 0:
        return 0.0
    return (rec.output_file_size_mb * 8) / rec.video_length_seconds


def render_report(rec: BenchmarkRecord, baseline: BenchmarkRecord | None = None) -> str:
    lines = [
        "Benchmark Report",
        "",
        f"Model      : {rec.provider} {rec.model_version}",
        f"Provider   : {rec.provider}",
        f"GPU        : {rec.gpu}",
        f"VRAM Peak  : {rec.peak_vram_gb:.1f} GB",
        f"Time       : {_fmt_duration(rec.inference_seconds)}",
        f"Resolution : {rec.resolution}",
        f"FPS        : {rec.fps}",
        f"Duration   : {rec.video_length_seconds:.0f} sec",
        f"Output Size: {rec.output_file_size_mb:.0f} MB",
    ]

    if baseline is not None:
        lines += ["", f"Comparison (vs {baseline.provider} {baseline.model_version})"]
        lines += _comparison_lines(rec, baseline)

    return "\n".join(lines)


def _comparison_lines(rec: BenchmarkRecord, base: BenchmarkRecord) -> list[str]:
    out: list[str] = []

    if base.inference_seconds > 0:
        faster = (base.inference_seconds - rec.inference_seconds) / base.inference_seconds
        verb = "Faster" if faster >= 0 else "Slower"
        out.append(f"  {'✓' if faster >= 0 else '✗'} {abs(faster) * 100:.0f}% {verb}")

    vram_delta = rec.peak_vram_gb - base.peak_vram_gb
    out.append(f"  {'✓' if vram_delta <= 0 else '⚠'} VRAM {vram_delta:+.1f} GB")

    base_br, rec_br = _bitrate_mbps(base), _bitrate_mbps(rec)
    if base_br > 0:
        br_delta = (rec_br - base_br) / base_br
        out.append(f"  ✓ Bitrate {br_delta * 100:+.0f}%")

    return out
