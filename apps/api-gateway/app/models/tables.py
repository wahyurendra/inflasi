"""SQLAlchemy ORM models — mapped from prisma/schema.prisma."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Dimension Tables ─────────────────────────────────────────

class DimRegion(Base):
    __tablename__ = "dim_region"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kode_wilayah: Mapped[str] = mapped_column(String(10), unique=True)
    nama_provinsi: Mapped[str] = mapped_column(String(100))
    nama_kab_kota: Mapped[str | None] = mapped_column(String(100))
    level_wilayah: Mapped[str] = mapped_column(String(20))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DimCommodity(Base):
    __tablename__ = "dim_commodity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kode_komoditas: Mapped[str] = mapped_column(String(20), unique=True)
    nama_komoditas: Mapped[str] = mapped_column(String(100))
    nama_display: Mapped[str] = mapped_column(String(100))
    kategori: Mapped[str] = mapped_column(String(50))
    satuan: Mapped[str] = mapped_column(String(20))
    is_strategis: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mvp: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DimCalendar(Base):
    __tablename__ = "dim_calendar"

    tanggal: Mapped[date] = mapped_column(Date, primary_key=True)
    tahun: Mapped[int] = mapped_column(Integer)
    bulan: Mapped[int] = mapped_column(Integer)
    minggu_ke: Mapped[int] = mapped_column(Integer)
    hari_ke: Mapped[int] = mapped_column(Integer)
    nama_hari: Mapped[str] = mapped_column(String(20))
    is_weekend: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hari_libur: Mapped[bool] = mapped_column(Boolean, default=False)
    nama_libur: Mapped[str | None] = mapped_column(String(100))
    musim: Mapped[str | None] = mapped_column(String(50))
    # Extended ML features (added 0003_calendar_features)
    day_of_week: Mapped[int | None] = mapped_column(Integer)
    week_of_year: Mapped[int | None] = mapped_column(Integer)
    quarter: Mapped[int | None] = mapped_column(Integer)
    is_month_start: Mapped[bool | None] = mapped_column(Boolean)
    is_month_end: Mapped[bool | None] = mapped_column(Boolean)
    ramadan_flag: Mapped[bool | None] = mapped_column(Boolean)
    lebaran_minus_21: Mapped[bool | None] = mapped_column(Boolean)
    lebaran_minus_14: Mapped[bool | None] = mapped_column(Boolean)
    lebaran_minus_7: Mapped[bool | None] = mapped_column(Boolean)
    lebaran_plus_7: Mapped[bool | None] = mapped_column(Boolean)
    nataru_minus_14: Mapped[bool | None] = mapped_column(Boolean)
    idul_adha_window: Mapped[bool | None] = mapped_column(Boolean)
    school_holiday_flag: Mapped[bool | None] = mapped_column(Boolean)
    harvest_flag: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Fact Tables ──────────────────────────────────────────────

class FactInflationMonthly(Base):
    __tablename__ = "fact_inflation_monthly"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periode: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    level_wilayah: Mapped[str] = mapped_column(String(20))
    ihk: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    inflasi_mtm: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    inflasi_ytd: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    inflasi_yoy: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    kelompok: Mapped[str | None] = mapped_column(String(100))
    commodity_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    andil: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sumber: Mapped[str] = mapped_column(String(50), default="BPS")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("periode", "region_id", "kelompok", "commodity_id", name="uq_inflation"),
    )


class FactPriceDaily(Base):
    __tablename__ = "fact_price_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    harga: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    harga_kemarin: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    perubahan_harian: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    perubahan_mingguan: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    perubahan_bulanan: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sumber: Mapped[str] = mapped_column(String(50), default="PIHPS_BI")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    region: Mapped["DimRegion"] = relationship(lazy="selectin")
    commodity: Mapped["DimCommodity"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tanggal", "region_id", "commodity_id", name="uq_price_daily"),
    )


class FactSupplyStock(Base):
    __tablename__ = "fact_supply_stock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    stok: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    cadangan: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    status: Mapped[str | None] = mapped_column(String(20))
    sumber: Mapped[str] = mapped_column(String(50), default="BAPANAS")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tanggal", "region_id", "commodity_id", name="uq_supply_stock"),
    )


class FactMacroDriver(Base):
    __tablename__ = "fact_macro_driver"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date, unique=True)
    kurs_usd_idr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    kurs_change_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    harga_bbm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    sumber_kurs: Mapped[str] = mapped_column(String(50), default="BI_JISDOR")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FactClimate(Base):
    __tablename__ = "fact_climate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    curah_hujan: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    suhu_rata: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    anomali_cuaca: Mapped[str | None] = mapped_column(String(100))
    warning_level: Mapped[str | None] = mapped_column(String(20))
    sumber: Mapped[str] = mapped_column(String(50), default="BMKG")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tanggal", "region_id", name="uq_climate"),
    )


# ── Analytics Tables ─────────────────────────────────────────

class AnalyticsRiskScore(Base):
    __tablename__ = "analytics_risk_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    skor_kenaikan_7d: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    skor_kenaikan_30d: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    skor_volatilitas: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    skor_deviasi_wilayah: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    skor_cuaca: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    skor_stok: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    risk_score_total: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    risk_category: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    region: Mapped["DimRegion"] = relationship(lazy="selectin")
    commodity: Mapped["DimCommodity"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tanggal", "region_id", "commodity_id", name="uq_risk_score"),
    )


class AnalyticsAlert(Base):
    __tablename__ = "analytics_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    alert_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    judul: Mapped[str] = mapped_column(String(200))
    deskripsi: Mapped[str] = mapped_column(Text)
    nilai_aktual: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    nilai_threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    region: Mapped["DimRegion"] = relationship(lazy="selectin")
    commodity: Mapped["DimCommodity"] = relationship(lazy="selectin")


class AnalyticsInsight(Base):
    __tablename__ = "analytics_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    tipe: Mapped[str] = mapped_column(String(20))
    judul: Mapped[str] = mapped_column(String(200))
    konten: Mapped[str] = mapped_column(Text)
    data_snapshot: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AnalyticsForecast(Base):
    __tablename__ = "analytics_forecast"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    horizon: Mapped[int] = mapped_column(Integer)
    yhat: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    yhat_lower: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    yhat_upper: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    model_version: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    region: Mapped["DimRegion"] = relationship(lazy="selectin")
    commodity: Mapped["DimCommodity"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tanggal", "region_id", "commodity_id", "horizon", name="uq_forecast"),
    )


class AnalyticsAnomaly(Base):
    __tablename__ = "analytics_anomaly"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    anomaly_score: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    is_anomaly: Mapped[bool] = mapped_column(Boolean)
    features: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tanggal", "region_id", "commodity_id", name="uq_anomaly"),
    )


# ── External Data Tables ─────────────────────────────────────

class ExtFaoFoodPrice(Base):
    __tablename__ = "ext_fao_food_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periode: Mapped[date] = mapped_column(Date, unique=True)
    index_overall: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    index_cereals: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    index_veg_oil: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    index_dairy: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    index_meat: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    index_sugar: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ExtCommodityPrice(Base):
    __tablename__ = "ext_commodity_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periode: Mapped[date] = mapped_column(Date)
    commodity: Mapped[str] = mapped_column(String(50))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit: Mapped[str] = mapped_column(String(30))
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sumber: Mapped[str] = mapped_column(String(50), default="WORLD_BANK")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("periode", "commodity", name="uq_commodity_price"),
    )


class ExtExchangeRate(Base):
    __tablename__ = "ext_exchange_rate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date, unique=True)
    kurs_jual: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    kurs_beli: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    kurs_tengah: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sumber: Mapped[str] = mapped_column(String(50), default="ECB")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ExtEnergyPrice(Base):
    __tablename__ = "ext_energy_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    commodity: Mapped[str] = mapped_column(String(30))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sumber: Mapped[str] = mapped_column(String(50), default="EIA")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tanggal", "commodity", name="uq_energy_price"),
    )


class ExtSupplyChainIndex(Base):
    __tablename__ = "ext_supply_chain_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    periode: Mapped[date] = mapped_column(Date, unique=True)
    gscpi: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ExtNewsSignal(Base):
    __tablename__ = "ext_news_signal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tanggal: Mapped[date] = mapped_column(Date)
    kategori: Mapped[str] = mapped_column(String(50))
    judul: Mapped[str] = mapped_column(String(500))
    sumber: Mapped[str] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(String(500))
    sentimen: Mapped[str | None] = mapped_column(String(20))
    relevansi: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    ringkasan: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Auth & User Tables ───────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    # Firebase Auth UID — primary identity link (see app/core/firebase.py).
    firebase_uid: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    email_verified: Mapped[datetime | None] = mapped_column(DateTime)
    hashed_password: Mapped[str | None] = mapped_column(String)  # legacy; unused under Firebase auth
    image: Mapped[str | None] = mapped_column(String)
    role: Mapped[str] = mapped_column(
        postgresql.ENUM("ADMIN", "GOVERNMENT_ANALYST", "CONTRIBUTOR", "REPORTER", name="UserRole", create_type=False),
        default="REPORTER",
    )
    region_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dim_region.id"))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    region: Mapped["DimRegion | None"] = relationship(lazy="selectin")


class PriceReport(Base):
    __tablename__ = "price_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_commodity.id"))
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("dim_region.id"))
    harga: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    satuan: Mapped[str] = mapped_column(String(20))
    nama_pasar: Mapped[str] = mapped_column(String(200))
    kota: Mapped[str | None] = mapped_column(String(100))
    kecamatan: Mapped[str | None] = mapped_column(String(100))
    tanggal: Mapped[date] = mapped_column(Date)
    catatan: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        postgresql.ENUM("PENDING", "APPROVED", "FLAGGED", "REJECTED", name="ReportStatus", create_type=False),
        default="PENDING",
    )
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    reviewed_by: Mapped[str | None] = mapped_column(String)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(lazy="selectin")
    commodity: Mapped["DimCommodity"] = relationship(lazy="selectin")
    region: Mapped["DimRegion"] = relationship(lazy="selectin")
    photos: Mapped[list["ReportPhoto"]] = relationship(lazy="selectin")


class ReportPhoto(Base):
    __tablename__ = "report_photos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    report_id: Mapped[str] = mapped_column(String, ForeignKey("price_reports.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    data: Mapped[dict | None] = mapped_column(JSON)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserPoints(Base):
    __tablename__ = "user_points"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), unique=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    monthly_points: Mapped[int] = mapped_column(Integer, default=0)
    total_reports: Mapped[int] = mapped_column(Integer, default=0)
    approved_reports: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_report_date: Mapped[date | None] = mapped_column(Date)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(lazy="selectin")


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(200))
    icon: Mapped[str] = mapped_column(String(50))
    threshold: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    badge_id: Mapped[str] = mapped_column(String, ForeignKey("badges.id"))
    earned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    badge: Mapped["Badge"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "badge_id"),
    )
