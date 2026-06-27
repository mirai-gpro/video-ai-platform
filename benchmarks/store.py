"""Persistence for benchmark records: CSV (append) and JSON (per-run)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from benchmarks.record import BenchmarkRecord


def append_csv(record: BenchmarkRecord, path: str | Path) -> Path:
    """Append a record to a CSV file, writing the header if new."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    is_new = not p.exists()
    row = record.to_dict()
    row["generation_settings"] = json.dumps(row["generation_settings"], sort_keys=True)

    with p.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(BenchmarkRecord.CSV_COLUMNS))
        if is_new:
            writer.writeheader()
        writer.writerow({k: row[k] for k in BenchmarkRecord.CSV_COLUMNS})
    return p


def write_json(record: BenchmarkRecord, path: str | Path) -> Path:
    """Write a single record as pretty JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True))
    return p
