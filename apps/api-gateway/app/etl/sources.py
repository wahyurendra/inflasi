"""Canonical ``fact_price_daily.sumber`` values used for source-priority routing.

Single source of truth so the validation worker's "crowd never overwrites official"
guard stays in lockstep with the strings the ETL pipelines actually write. When a
new official pipeline ships (e.g. BAPANAS), add it to ``OFFICIAL`` here — no other
file needs to change.
"""

from __future__ import annotations

OFFICIAL: frozenset[str] = frozenset({"PIHPS_BI", "BPS", "BAPANAS"})
CROWD: str = "CROWD"
