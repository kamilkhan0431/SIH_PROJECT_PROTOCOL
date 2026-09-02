from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./slopesense.db"
    jwt_secret: str = "slopesense-demo-secret"
    jwt_alg: str = "HS256"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    data_dir: str = str(Path(__file__).resolve().parents[3] / "data")
    model_path: str = str(Path(__file__).resolve().parents[3] / "ml" / "model.joblib")
    upload_dir: str = str(Path(__file__).resolve().parents[1] / "uploads")
    sms_provider: str = "stub"
    msg91_key: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


settings = Settings()
