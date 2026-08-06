from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"


class Settings(BaseSettings):
    """
    Global application configuration.
    """

    app_name: str = "Nexus AI Gateway"

    environment: str = Field(default="development")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    log_level: str = Field(default="INFO")

    providers_config: Path = CONFIG_DIR / "providers.yaml"
    router_config: Path = CONFIG_DIR / "router.yaml"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    def load_router(self) -> dict:
        with open(self.router_config, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_providers(self) -> dict:
        with open(self.providers_config, encoding="utf-8") as f:
            return yaml.safe_load(f)


settings = Settings()
