import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

# Importing an endpoint constructs application settings; no connection is opened.
os.environ.setdefault(
    "ANALYTICS_DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test",
)

from app.api.endpoints.internal_models import _require_training_token


class TrainingServiceAuthTests(unittest.TestCase):
    def test_missing_server_token_is_service_unavailable(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as raised:
                _require_training_token("client-token")
        self.assertEqual(raised.exception.status_code, 503)

    def test_wrong_token_is_unauthorized(self) -> None:
        with patch.dict(os.environ, {"TRAINING_SERVICE_TOKEN": "a" * 64}):
            with self.assertRaises(HTTPException) as raised:
                _require_training_token("b" * 64)
        self.assertEqual(raised.exception.status_code, 401)

    def test_matching_strong_token_is_accepted(self) -> None:
        token = "c" * 64
        with patch.dict(os.environ, {"TRAINING_SERVICE_TOKEN": token}):
            _require_training_token(token)


if __name__ == "__main__":
    unittest.main()
