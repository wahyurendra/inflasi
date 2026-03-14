from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase PostgreSQL (async for SQLAlchemy)
    database_url: str = "postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
    database_url_sync: str = "postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

    # Pipeline settings
    pihps_base_url: str = "https://www.bi.go.id/hargapangan"
    bps_base_url: str = "https://webapi.bps.go.id/v1"
    bmkg_base_url: str = "https://data.bmkg.go.id"

    # API keys
    bps_api_key: str = ""
    eia_api_key: str = ""  # EIA energy data (https://www.eia.gov/opendata/register.php)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
