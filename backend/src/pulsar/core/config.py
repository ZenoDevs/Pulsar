from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel


class AISettings(BaseModel):
    enabled: bool = False


class Settings(BaseModel):
    ai: AISettings = AISettings()


def load_settings() -> Settings:
    """Load settings from config.yaml file."""
    config_path = Path(__file__).parent.parent.parent.parent.parent / "config.yaml"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}
        return Settings(**yaml_data)

    return Settings()


settings = load_settings()

# CORS settings for FastAPI
CORS_ALLOW_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
