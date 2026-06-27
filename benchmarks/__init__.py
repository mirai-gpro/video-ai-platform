"""Benchmark capture and reporting (proposal §§12-13).

Provides the canonical ``BenchmarkRecord`` schema, CSV/JSON persistence, and a
human-readable report renderer used to compare Providers objectively. Full
auto-capture wiring into the Pipeline lands in Phase 3; the schema and writers
are part of the reviewed design so early runs already produce comparable data.
"""

from benchmarks.record import BenchmarkRecord
from benchmarks.report import render_report
from benchmarks.store import append_csv, write_json

__all__ = ["BenchmarkRecord", "append_csv", "render_report", "write_json"]
