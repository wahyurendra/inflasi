"""Receipt/label OCR price verification. PaddleOCR is imported lazily; when the OCR
stack isn't installed (CPU-only image) it returns available=False so callers treat the
score as neutral instead of failing."""

import logging
import re

logger = logging.getLogger("ocr")


class OCREngine:
    def __init__(self) -> None:
        self._ocr = None

    def _engine(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(use_angle_cls=True, lang="id", show_log=False)
        return self._ocr

    async def verify(self, image_url: str, reported_price: float, tolerance: float = 0.1) -> dict:
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
