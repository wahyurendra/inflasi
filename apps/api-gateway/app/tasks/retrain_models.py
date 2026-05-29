"""Retraining orchestrator — records a model_training_runs row, exports the
training-window snapshot, and invokes the matching trainer.

Two execution modes are supported. Both register the same audit trail row so
the dashboard sees a consistent timeline.

* **In-process (MVP)** — spawns `python -m ml.training.train_<model_type>` as a
  subprocess. The trainer image lives in `ml/training/`; in the api-gateway
  image those imports are not satisfied, so this path will record FAILED on
  ImportError and surface the message via the run's `notes` column. That's
  exactly what we want for the MVP: visible failures rather than silent ones.
* **External trigger** — pass `dry_run=True` and the function only writes the
  run row. A separate operator (or future K8s Job pattern) executes the
  training and POSTs the resulting artifact to `/admin/models`.

The subprocess shell-out is intentional. Pulling lightgbm / prophet / pytorch
into the api image to "import-run" trainers would bloat every API replica with
a multi-GB ML toolchain for a code path that runs once a week.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import shlex
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date, timedelta

from app.database import async_session
from app.db.repositories.model_repo import ModelRepo
from app.tasks.export_features import export_feature_store

logger = logging.getLogger("retrain_models")

SUPPORTED_MODEL_TYPES = {"lightgbm", "prophet", "sarimax", "tft", "ensemble"}
DEFAULT_TRAIN_WINDOW_DAYS = 365  # ≈ 1 year of history for the training split


@dataclass
class RetrainResult:
    run_id: int
    status: str  # SUCCESS | FAILED | SKIPPED
    model_type: str
    horizon: int | None
    duration_seconds: float
    snapshot_path: str | None
    snapshot_rows: int
    stdout_tail: str
    stderr_tail: str
    notes: str


def _module_for(model_type: str) -> str:
    return f"ml.training.train_{model_type}"


async def run_retrain(
    *,
    model_type: str,
    horizon: int | None = None,
    target_type: str = "price",
    train_window_days: int = DEFAULT_TRAIN_WINDOW_DAYS,
    run_name: str | None = None,
    notes: str | None = None,
    extra_args: list[str] | None = None,
    dry_run: bool = False,
    snapshot_format: str = "csv",
) -> RetrainResult:
    """Drive a single training run end-to-end.

    Steps:
      1. Insert a model_training_runs row with status=RUNNING.
      2. Export the train-window slice of `feature_store_daily` to a temp file.
      3. Invoke the matching `ml.training.train_<model_type>` module via subprocess.
      4. Update the run row with SUCCESS/FAILED, tails, notes.

    Returns even on failure — caller can inspect the result and the audit row.
    """
    if model_type not in SUPPORTED_MODEL_TYPES:
        raise ValueError(
            f"unsupported model_type={model_type!r}; expected one of {sorted(SUPPORTED_MODEL_TYPES)}",
        )

    train_end = date.today()
    train_start = train_end - timedelta(days=train_window_days)
    run_name = run_name or f"{model_type}-h{horizon or 'na'}-{train_end.isoformat()}"
    start_t = time.monotonic()

    async with async_session() as db:
        repo = ModelRepo(db)
        run = await repo.create_run(
            run_name=run_name,
            model_type=model_type,
            target_type=target_type,
            horizon=horizon,
            params={
                "train_window_days": train_window_days,
                "train_start": train_start.isoformat(),
                "train_end": train_end.isoformat(),
                "extra_args": list(extra_args or []),
                "dry_run": bool(dry_run),
            },
            notes=notes,
        )
        run.train_start_date = train_start
        run.train_end_date = train_end
        await db.commit()
        run_id = run.id

    snapshot_path: str | None = None
    snapshot_rows = 0
    note_lines: list[str] = []

    try:
        # ── Snapshot ────────────────────────────────────────────
        with tempfile.TemporaryDirectory(prefix="inflasi-retrain-") as tmp:
            try:
                async with async_session() as db:
                    snapshot = await export_feature_store(
                        db,
                        output_dir=tmp,
                        split="train",
                        start=train_start,
                        end=train_end,
                        fmt=snapshot_format,
                    )
                snapshot_path = snapshot.path
                snapshot_rows = snapshot.rows
                note_lines.append(
                    f"snapshot: {snapshot.rows} rows -> {snapshot.path} ({snapshot.format})",
                )
            except Exception as exc:
                note_lines.append(f"snapshot failed: {type(exc).__name__}: {exc}")
                logger.exception("retrain snapshot failed for run %s", run_id)

            if dry_run:
                status = "SKIPPED"
                stdout_tail = stderr_tail = ""
                note_lines.append("dry_run=True; trainer subprocess skipped")
            else:
                stdout_tail, stderr_tail, rc = await _spawn_trainer(
                    model_type=model_type, horizon=horizon, extra_args=extra_args,
                )
                if rc == 0:
                    status = "SUCCESS"
                else:
                    status = "FAILED"
                    note_lines.append(f"trainer exited rc={rc}")
    except Exception as exc:
        status = "FAILED"
        stdout_tail = ""
        stderr_tail = f"{type(exc).__name__}: {exc}"
        note_lines.append(stderr_tail)
        logger.exception("retrain orchestration failed for run %s", run_id)

    duration = round(time.monotonic() - start_t, 2)
    full_note = (notes + "\n" if notes else "") + "\n".join(note_lines)

    async with async_session() as db:
        await ModelRepo(db).finish_run(
            run_id=run_id, status=status, metrics=None, notes=full_note.strip() or None,
        )
        await db.commit()

    return RetrainResult(
        run_id=run_id,
        status=status,
        model_type=model_type,
        horizon=horizon,
        duration_seconds=duration,
        snapshot_path=snapshot_path,
        snapshot_rows=snapshot_rows,
        stdout_tail=_tail(stdout_tail),
        stderr_tail=_tail(stderr_tail),
        notes=full_note.strip(),
    )


async def _spawn_trainer(
    *,
    model_type: str,
    horizon: int | None,
    extra_args: list[str] | None,
) -> tuple[str, str, int]:
    cmd: list[str] = [sys.executable, "-m", _module_for(model_type)]
    if horizon is not None:
        cmd += ["--horizon", str(horizon)]
    if extra_args:
        cmd += list(extra_args)
    logger.info("trainer cmd: %s", " ".join(shlex.quote(c) for c in cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ},
    )
    out_b, err_b = await proc.communicate()
    return (
        (out_b or b"").decode("utf-8", errors="replace"),
        (err_b or b"").decode("utf-8", errors="replace"),
        proc.returncode if proc.returncode is not None else 1,
    )


def _tail(blob: str, lines: int = 40) -> str:
    if not blob:
        return ""
    parts = blob.splitlines()[-lines:]
    return "\n".join(parts)


def _main() -> None:
    parser = argparse.ArgumentParser(description="Run a model retraining task.")
    parser.add_argument("--model-type", required=True, choices=sorted(SUPPORTED_MODEL_TYPES))
    parser.add_argument("--horizon", type=int, default=None)
    parser.add_argument("--target-type", default="price")
    parser.add_argument("--train-window-days", type=int, default=DEFAULT_TRAIN_WINDOW_DAYS)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--snapshot-format", default="csv", choices=["csv", "parquet"])
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--extra", nargs=argparse.REMAINDER, default=None,
                        help="Anything after `--extra` is forwarded to the trainer.")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    extra = args.extra[1:] if (args.extra and args.extra[:1] == ["--"]) else (args.extra or [])
    result = asyncio.run(run_retrain(
        model_type=args.model_type,
        horizon=args.horizon,
        target_type=args.target_type,
        train_window_days=args.train_window_days,
        run_name=args.run_name,
        notes=args.notes,
        extra_args=extra,
        dry_run=args.dry_run,
        snapshot_format=args.snapshot_format,
    ))
    raise SystemExit(0 if result.status in {"SUCCESS", "SKIPPED"} else 1)


if __name__ == "__main__":
    _main()
