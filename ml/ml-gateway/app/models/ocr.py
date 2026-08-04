"""Receipt/label OCR price verification. PaddleOCR is imported lazily; when the OCR
stack isn't installed (CPU-only image) it returns available=False so callers treat the
score as neutral instead of failing."""

import logging
import os
import re

logger = logging.getLogger("ocr")


class OCREngine:
    def __init__(self, *, allow_remote: bool = True) -> None:
        self._ocr = None
        remote = os.environ.get("GPU_GATEWAY_URL", "") if allow_remote else ""
        self.remote_url = remote.rstrip("/")

    def _engine(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="id",
                show_log=False,
                use_gpu=True,
            )
        return self._ocr

    async def verify(self, image_url: str, reported_price: float, tolerance: float = 0.1) -> dict:
        if self.remote_url:
            return await self._verify_remote(image_url, reported_price, tolerance)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                content = resp.content
        except Exception:
            return {"available": True, "match": None, "error": "image_fetch_failed"}

        try:
            import cv2
            import numpy as np

            img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
            result = self._engine().ocr(img, cls=True)
            texts = [line[1][0] for block in (result or []) for line in (block or [])]
            prices = [float(re.sub(r"[^\d]", "", t)) for t in texts if re.search(r"\d{3,}", t)]
            match = any(abs(p - reported_price) / max(reported_price, 1) <= tolerance for p in prices)
            return {"available": True, "match": match, "extracted": prices[:10]}
        except Exception:
            logger.exception("OCR failed")
            return {"available": False, "match": None, "error": "ocr_unavailable"}

    async def _verify_remote(
        self,
        image_url: str,
        reported_price: float,
        tolerance: float,
    ) -> dict:
        """Proxy OCR to the GPU pod; fail closed when it is preempted for training."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.remote_url}/ocr/verify",
                    json={
                        "image_url": image_url,
                        "reported_price": reported_price,
                        "tolerance": tolerance,
                    },
                )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {
                "available": False,
                "match": None,
                "error": "invalid_gpu_response",
            }
        except Exception as exc:
            logger.warning("remote OCR unavailable (%s): %s", self.remote_url, exc)
            return {
                "available": False,
                "match": None,
                "error": "gpu_gateway_unavailable",
            }
