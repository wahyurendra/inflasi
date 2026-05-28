from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.price_calculator import PriceCalculator
from app.services.risk_scorer import RiskScorer
from app.services.ranking import RankingService

router = APIRouter()


@router.get("/prices/changes")
async def get_price_changes(
    commodity_code: str = Query(..., description="Kode komoditas"),
    region_code: str = Query("00", description="Kode wilayah"),
    tanggal: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Hitung perubahan harga harian/mingguan/bulanan."""
    calc = PriceCalculator(db)
    return await calc.get_price_changes(commodity_code, region_code, tanggal or date.today())


@router.get("/prices/volatility")
async def get_volatility(
    commodity_code: str = Query(...),
    region_code: str = Query("00"),
    window: int = Query(14),
    db: AsyncSession = Depends(get_db),
):
    """Hitung volatilitas harga (Coefficient of Variation)."""
    calc = PriceCalculator(db)
    return await calc.get_volatility(commodity_code, region_code, window)


@router.get("/risk-scores")
async def get_risk_scores(
    tanggal: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get risk scores untuk semua komoditas-wilayah."""
    scorer = RiskScorer(db)
    return await scorer.get_all_scores(tanggal or date.today())


@router.get("/commodities/ranking")
async def get_commodity_ranking(
    sort: str = Query("weekly_change", description="weekly_change|daily_change|volatility"),
    limit: int = Query(8),
    db: AsyncSession = Depends(get_db),
):
    """Ranking komoditas berdasarkan perubahan harga."""
    ranking = RankingService(db)
    return await ranking.get_commodity_ranking(sort, limit)


@router.get("/regions/ranking")
async def get_region_ranking(
    sort: str = Query("pressure", description="pressure|risk_score"),
    limit: int = Query(10),
    db: AsyncSession = Depends(get_db),
):
    """Ranking wilayah berdasarkan tekanan harga."""
    ranking = RankingService(db)
    return await ranking.get_region_ranking(sort, limit)


@router.post("/calculate")
async def run_daily_calculation(
    tanggal: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Jalankan kalkulasi harian (perubahan harga, risk score, dll)."""
    target = tanggal or date.today()
    calc = PriceCalculator(db)
    scorer = RiskScorer(db)

    await calc.calculate_all_changes(target)
    await scorer.calculate_all_scores(target)

    return {"status": "ok", "tanggal": target.isoformat()}
