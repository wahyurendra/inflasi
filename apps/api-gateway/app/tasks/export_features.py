"""Export `feature_store_daily` into a parquet/CSV snapshot for offline training.

Used by `retrain_models` to freeze the exact dataset a run trained on so future
backtests can be reproduced. Two modes:

* **CSV** — works anywhere with stdlib; streams in chunks so a multi-year export
  doesn't load the whole table into memory.
* **Parquet** — only when `pyarrow` (or `pandas`) is importable. Otherwise we
  silently fall back to CSV. The training image already pins pyarrow.

Output paths are absolute. The caller decides whether to upload to MinIO; that
upload is the training image's concern, not this task's.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("export_features")


@dataclass
class ExportResult:
    path: str
    rows: int
    format: str
    split: str | None
    start: date | None
    end: date | None


async def export_feature_store(
    db: AsyncSession,
    *,
    output_dir: str | Path,
    split: str | None = None,
    start: date | None = None,
    end: date | None = None,
    fmt: str = "csv",
    chunk_size: int = 5000,
) -> ExportResult:
    """Stream `feature_store_daily` into a file. Returns the absolute path + row count.

    `split`/`start`/`end` are optional filters. When `fmt="parquet"` and pyarrow
    is missing the function transparently falls back to CSV.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    where: list[str] = ["1=1"]
    params: dict = {}
    if split:
        where.append("split = :split")
        params["split"] = split
    if start:
        where.append("date >= :start")
        params["start"] = start
    if end:
        where.append("date <= :end")
        params["end"] = end

    sql = (
        "SELECT * FROM feature_store_daily "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY date, commodity_id, region_id"
    )

    suffix = "parquet" if fmt == "parquet" else "csv"
    stamp = (split or "all") + "_" + date.today().isoformat()
    out_path = output_dir / f"feature_store_{stamp}.{suffix}"

    rows_written = 0

    if fmt == "parquet":
        try:
            import importlib

            importlib.import_module("pandas")
            importlib.import_module("pyarrow")
        except Exception:
            logger.warning("pyarrow not importable; falling back to CSV export")
            fmt = "csv"
            suffix = "csv"
            out_path = output_dir / f"feature_store_{stamp}.{suffix}"

    if fmt == "parquet":
        import pandas as pd

        frames: list[pd.DataFrame] = []
        result = await db.stream(text(sql), params)
        async for partition in result.partitions(chunk_size):
            df_chunk = pd.DataFrame(
                [dict(r._mapping) for r in partition],
            )
            frames.append(df_chunk)
            rows_written += len(df_chunk)
        if frames:
            df = pd.concat(frames, ignore_index=True)
            df.to_parquet(out_path, index=False)
        else:
            # touch a header-only file so downstream tooling doesn't 404 on it.
            out_path.write_bytes(b"")
    else:
        result = await db.stream(text(sql), params)
        first = True
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            async for partition in result.partitions(chunk_size):
                for row in partition:
                    row_map = row._mapping
                    if first:
                        writer.writerow(list(row_map.keys()))
                        first = False
                    writer.writerow(list(row_map.values()))
                    rows_written += 1

    logger.info(
        "exported %s rows to %s (split=%s, range=%s..%s)",
        rows_written, out_path, split, start, end,
    )
    return ExportResult(
        path=str(out_path.resolve()),
        rows=rows_written,
        format=fmt,
        split=split,
        start=start,
        end=end,
    )
