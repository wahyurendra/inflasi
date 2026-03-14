-- ===========================================
-- Hapus semua dummy/sample data dari database
-- Dimension tables (dim_region, dim_commodity, dim_calendar) TETAP DIPERTAHANKAN
-- ===========================================

-- 1. Crowdsourced & User data
TRUNCATE TABLE report_photos CASCADE;
TRUNCATE TABLE price_reports CASCADE;
TRUNCATE TABLE user_badges CASCADE;
TRUNCATE TABLE user_points CASCADE;
TRUNCATE TABLE notifications CASCADE;
TRUNCATE TABLE badges CASCADE;

-- 2. Analytics tables
TRUNCATE TABLE analytics_anomaly CASCADE;
TRUNCATE TABLE analytics_forecast CASCADE;
TRUNCATE TABLE analytics_insights CASCADE;
TRUNCATE TABLE analytics_alerts CASCADE;
TRUNCATE TABLE analytics_risk_score CASCADE;

-- 3. Fact tables (sample data)
TRUNCATE TABLE fact_price_daily CASCADE;
TRUNCATE TABLE fact_inflation_monthly CASCADE;
TRUNCATE TABLE fact_supply_stock CASCADE;
TRUNCATE TABLE fact_macro_driver CASCADE;
TRUNCATE TABLE fact_climate CASCADE;

-- 4. External datasets
TRUNCATE TABLE ext_fao_food_price CASCADE;
TRUNCATE TABLE ext_commodity_price CASCADE;
TRUNCATE TABLE ext_exchange_rate CASCADE;
TRUNCATE TABLE ext_energy_price CASCADE;
TRUNCATE TABLE ext_supply_chain_index CASCADE;
TRUNCATE TABLE ext_news_signal CASCADE;

-- 5. Auth (sessions only, keep users)
TRUNCATE TABLE sessions CASCADE;
TRUNCATE TABLE verification_tokens CASCADE;
