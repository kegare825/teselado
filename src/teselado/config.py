from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. No SQL or external credentials."""

    model_config = SettingsConfigDict(env_prefix="TESELADO_")

    data_dir: Path = Path("data/sample")
    output_dir: Path = Path("outputs")
    k_min: int = 3
    k_max: int = 8
    grid_step: float = 0.001
    city: str = "demo"
