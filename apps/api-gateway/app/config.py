from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL (async for SQLAlchemy). Reads ANALYTICS_DATABASE_URL env var.
    # In production this points at the in-cluster TimescaleDB (inflasi-pg).
    analytics_database_url: str

    # Redis (cache + Streams)
    redis_url: str = "redis://localhost:6379/0"

    # ML gateway (in-cluster). Validation pipeline cross-checks anomalies here.
    ml_gateway_url: str = "http://inflasi-ml:8080"

    # Pipeline settings
    pihps_base_url: str = "https://www.bi.go.id/hargapangan"
    bps_base_url: str = "https://webapi.bps.go.id/v1"
    bmkg_base_url: str = "https://data.bmkg.go.id"

    # Firebase Admin — verifies ID tokens from the web/Android clients (see
    # app/core/firebase.py). Read through pydantic (not os.getenv) so the value in
    # .env is actually picked up: pydantic-settings loads .env into this object only,
    # it does NOT export to os.environ. Falls back to GOOGLE_APPLICATION_CREDENTIALS
    # / workload-identity ADC when left blank.
    firebase_credentials_file: str = ""

    # API keys
    bps_api_key: str = ""
    eia_api_key: str = ""  # EIA energy data (https://www.eia.gov/opendata/register.php)

    # OpenAI — used by BlogGenerator to turn daily analytics into a narrative
    # article. When the key is blank, the generator falls back to a deterministic
    # template so the analytics batch never depends on an external API.
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"
    blog_generation_enabled: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
