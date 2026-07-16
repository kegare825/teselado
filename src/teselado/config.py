from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. No SQL or external credentials."""

    model_config = SettingsConfigDict(env_prefix="TESELADO_")

    data_dir: Path = Path("data/sample")
    output_dir: Path = Path("outputs")
    city: str = "demo"
    method: str = "kmeans"  # "kmeans" or "fuzzy"
    k_min: int = 3
    k_max: int = 8
    k: int | None = None
    grid_step: float | None = None
    num_couriers: int = 5
    avg_speed_kmh: float = 25.0
    sla_minutes: float = 30.0
    seed: int = 42
    n_restaurants: int = 50
    n_orders: int = 500
    restaurant_handle_minutes: float = 5.0
    assigner: str = "greedy"
