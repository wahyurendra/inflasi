import os
import unittest
from unittest.mock import patch

from ml.training.common import TrainingConfig, register_model
from ml.training.export_dataset import fetch_feature_store_csv


class _Response:
    text = "date,price,target_h7\n2026-08-05,10000,10100\n"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"id": 1, "model_name": "test"}


class _Client:
    calls: list[tuple[str, str, dict]] = []

    def __init__(self, **_: object) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def get(self, url: str) -> _Response:
        self.calls.append(("GET", url, {}))
        return _Response()

    def post(self, url: str, json: dict, headers: dict) -> _Response:
        self.calls.append(("POST", url, headers))
        return _Response()


class TrainingServiceAPITests(unittest.TestCase):
    def setUp(self) -> None:
        _Client.calls.clear()
        self.cfg = TrainingConfig(api_gateway_url="http://inflasi-api:8080")

    def test_export_uses_real_api_prefix(self) -> None:
        with patch("httpx.Client", _Client):
            frame = fetch_feature_store_csv(self.cfg)
        self.assertEqual(len(frame), 1)
        self.assertEqual(
            _Client.calls[0][1],
            "http://inflasi-api:8080/api/forecast/dataset/export",
        )

    def test_registration_uses_internal_service_token(self) -> None:
        token = "d" * 64
        with (
            patch.dict(os.environ, {"TRAINING_SERVICE_TOKEN": token}),
            patch("httpx.Client", _Client),
        ):
            result = register_model(
                self.cfg,
                model_name="test",
                model_type="lightgbm",
                target_type="price",
                artifact_path="gs://train-ml/models/test.joblib",
                horizon=7,
            )
        self.assertEqual(result["id"], 1)
        method, url, headers = _Client.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://inflasi-api:8080/api/internal/models")
        self.assertEqual(headers, {"X-Training-Token": token})


if __name__ == "__main__":
    unittest.main()
