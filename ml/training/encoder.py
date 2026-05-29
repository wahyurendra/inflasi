"""Re-export of :mod:`app.services.feature_encoder` for the training package.

Single source of truth — training and inference share the same encoding so
``commodity_id`` (string) always maps to the same ``commodity_id_code`` (int).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# The training container doesn't necessarily ship apps/api-gateway on its
# PYTHONPATH. Resolve the file by relative path and load it as a module.
_HERE = Path(__file__).resolve().parent
_ENCODER_PATH = (_HERE.parent.parent / "apps" / "api-gateway" / "app" / "services" / "feature_encoder.py").resolve()

if not _ENCODER_PATH.exists():
    raise ImportError(f"feature_encoder.py not found at {_ENCODER_PATH}")

_spec = importlib.util.spec_from_file_location("feature_encoder", _ENCODER_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"could not load spec for {_ENCODER_PATH}")
_module = importlib.util.module_from_spec(_spec)
sys.modules["feature_encoder"] = _module
_spec.loader.exec_module(_module)

encode_codes = _module.encode_codes
CODE_COLUMNS = _module.CODE_COLUMNS

__all__ = ["encode_codes", "CODE_COLUMNS"]
