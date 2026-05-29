"""Driver for `MonthlyFeatureBuilder` — invoked monthly after BPS data lands.

Defaults to incremental rebuild: only periods missing from
`feature_store_monthly` (or older than 1 month back from today) are recomputed.
A full rebuild is available via `--full`.

K8s schedule: 1× per month, 06:00 WIB on the 3rd (BPS typically publishes
between the 1st and 3rd). The CronJob lives in
`infra/k8s/projects/inflasi-api/cronjobs.yaml`.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import asdict
from datetime import date

from app.database import async_session
from app.services.monthly_feature_builder import MonthlyFeatureBuilder

logger = logging.getLogger("build_monthly_features")


async def run(
    *,
    start: date | None = None,
    end: date | None = None,
    region_ids: list[int] | None = None,
    full: bool = False,
) -> dict:
    if not full and start is None:
        # Incremental: re-process anything within the trailing window so late-
        # arriving BPS revisions get picked up.
        start = date(date.today().year - 2, 1, 1)

    async with async_session() as db:
        builder = MonthlyFeatureBuilder(db)
        summary = await builder.build(
            start=start, end=end, region_ids=region_ids,
        )
    logger.info("monthly feature build done: %s", asdict(summary))
    return asdict(summary)


def _parse_ids(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    return [int(x) for x in raw.split(",") if x.strip()]


def _main() -> None:
    parser = argparse.ArgumentParser(description="Build feature_store_monthly rows.")
    parser.add_argument("--start", default=None, help="YYYY-MM (inclusive)")
    parser.add_argument("--end", default=None, help="YYYY-MM (inclusive)")
    parser.add_argument("--region-ids", default=None,
                        help="Comma-separated dim_region.id values.")
    parser.add_argument("--full", action="store_true",
                        help="Rebuild every period in fact_inflation_monthly.")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    def parse(p: str | None) -> date | None:
        if not p:
            return None
        y, m = p.split("-")[:2]
        return date(int(y), int(m), 1)

    asyncio.run(run(
        start=parse(args.start),
        end=parse(args.end),
        region_ids=_parse_ids(args.region_ids),
        full=args.full,
    ))


if __name__ == "__main__":
    _main()
