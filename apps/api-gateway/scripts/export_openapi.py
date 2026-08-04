"""Export or validate the API Gateway OpenAPI contract.

Usage from ``apps/api-gateway``::

    python scripts/export_openapi.py
    python scripts/export_openapi.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = API_ROOT / "docs" / "openapi.json"


def _render_schema() -> str:
    sys.path.insert(0, str(API_ROOT))
    from app.main import app

    schema = app.openapi()
    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    if len(operation_ids) != len(set(operation_ids)):
        duplicates = sorted({item for item in operation_ids if operation_ids.count(item) > 1})
        raise RuntimeError(f"duplicate OpenAPI operationId values: {duplicates}")
    if "FirebaseBearer" not in schema.get("components", {}).get("securitySchemes", {}):
        raise RuntimeError("FirebaseBearer security scheme is missing")
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the INFLASI OpenAPI contract")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the checked-in contract differs from the application schema",
    )
    args = parser.parse_args()

    rendered = _render_schema()
    output = args.output.resolve()
    if args.check:
        if not output.exists():
            print(f"OpenAPI contract does not exist: {output}", file=sys.stderr)
            return 1
        if output.read_text(encoding="utf-8") != rendered:
            print(
                f"OpenAPI contract is stale: run `python scripts/export_openapi.py` ({output})",
                file=sys.stderr,
            )
            return 1
        print(f"OpenAPI contract is up to date: {output}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Wrote OpenAPI contract: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
