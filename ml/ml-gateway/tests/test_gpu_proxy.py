import asyncio
import os
import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.models.loaders.tft_loader import TFTLoader
from app.models.ocr import OCREngine


class _SyncResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"p10": [1.0], "p50": [2.0], "p90": [3.0], "version": "test"}


class _SyncClient:
    def __init__(self, **_: object) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def post(self, url: str, json: dict) -> _SyncResponse:
        assert url == "http://gpu:8080/internal/gpu/tft/predict"
        assert json["horizon"] == 1
        assert json["features"][0]["date"].startswith("2026-08-04")
        return _SyncResponse()


class _AsyncResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"available": True, "match": True}


class _AsyncClient:
    def __init__(self, **_: object) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def post(self, url: str, json: dict) -> _AsyncResponse:
        assert url == "http://gpu:8080/ocr/verify"
        assert json["reported_price"] == 12000
        return _AsyncResponse()


class GPUProxyTests(unittest.TestCase):
    def test_tft_delegates_to_gpu_service(self) -> None:
        frame = pd.DataFrame([{"date": pd.Timestamp("2026-08-04"), "price": 10.0}])
        with (
            patch.dict(os.environ, {"GPU_GATEWAY_URL": "http://gpu:8080"}),
            patch("httpx.Client", _SyncClient),
        ):
            result = TFTLoader().predict(frame, 1)
        self.assertEqual(result["p50"], [2.0])

    def test_ocr_delegates_to_gpu_service(self) -> None:
        async def run() -> dict:
            with (
                patch.dict(os.environ, {"GPU_GATEWAY_URL": "http://gpu:8080"}),
                patch("httpx.AsyncClient", _AsyncClient),
            ):
                return await OCREngine().verify(
                    "https://example.test/receipt.jpg", 12000,
                )

        self.assertEqual(
            asyncio.run(run()),
            {"available": True, "match": True},
        )

    def test_gpu_readiness_requires_cuda(self) -> None:
        from app import main

        client = TestClient(main.app)
        no_gpu = {"device": "cpu", "gpu": False, "torch": True}
        with (
            patch.dict(os.environ, {"REQUIRE_GPU": "true"}),
            patch.object(main, "get_device_info", return_value=no_gpu),
        ):
            self.assertEqual(client.get("/ready").status_code, 503)

    def test_cpu_readiness_does_not_require_cuda(self) -> None:
        from app import main

        client = TestClient(main.app)
        no_gpu = {"device": "cpu", "gpu": False, "torch": False}
        with (
            patch.dict(os.environ, {"REQUIRE_GPU": "false"}),
            patch.object(main, "get_device_info", return_value=no_gpu),
        ):
            self.assertEqual(client.get("/ready").status_code, 200)


if __name__ == "__main__":
    unittest.main()
