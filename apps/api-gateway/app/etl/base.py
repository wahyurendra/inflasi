import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class DataPipeline(ABC):
    """Base class untuk semua ETL pipeline."""

    name: str = "base"

    @abstractmethod
    async def extract(self) -> Any:
        """Ambil data dari sumber eksternal."""
        ...

    @abstractmethod
    async def validate(self, raw: Any) -> bool:
        """Validasi data: schema, range, completeness."""
        ...

    @abstractmethod
    async def transform(self, raw: Any) -> Any:
        """Normalisasi dan transformasi data."""
        ...

    @abstractmethod
    async def load(self, clean: Any) -> None:
        """Simpan data ke database."""
        ...

    async def run(self) -> dict:
        """Execute full ETL pipeline."""
        start = datetime.now()
        logger.info(f"[{self.name}] Pipeline started at {start}")

        try:
            raw = await self.extract()
            logger.info(f"[{self.name}] Extracted {len(raw) if hasattr(raw, '__len__') else '?'} records")

            if not await self.validate(raw):
                logger.error(f"[{self.name}] Validation failed")
                return {"status": "error", "reason": "validation_failed", "pipeline": self.name}

            clean = await self.transform(raw)
            logger.info(f"[{self.name}] Transformed {len(clean) if hasattr(clean, '__len__') else '?'} records")

            await self.load(clean)

            duration = (datetime.now() - start).total_seconds()
            logger.info(f"[{self.name}] Pipeline completed in {duration:.1f}s")

            return {
                "status": "ok",
                "pipeline": self.name,
                "records": len(clean) if hasattr(clean, "__len__") else 0,
                "duration_seconds": duration,
            }

        except Exception as e:
            logger.exception(f"[{self.name}] Pipeline failed: {e}")
            return {"status": "error", "reason": str(e), "pipeline": self.name}
