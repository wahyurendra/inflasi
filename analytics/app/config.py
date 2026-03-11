from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/inflasi"
    database_url_sync: str = "postgresql://user:password@localhost:5432/inflasi"

    # Pipeline settings
    pihps_base_url: str = "https://www.bi.go.id/hargapangan"
    bps_base_url: str = "https://webapi.bps.go.id/v1"
    bmkg_base_url: str = "https://data.bmkg.go.id"

    # API keys (if needed)
    bps_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
