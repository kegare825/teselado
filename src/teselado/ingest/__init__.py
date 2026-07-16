"""Data ingestion: synthetic generation, loaders, and schema validation."""

from teselado.ingest.loaders import (
    dataset_summary,
    load_metadata,
    load_orders,
    load_orders_df,
    load_restaurants_df,
)
from teselado.ingest.schema import ORDER_COLUMNS, RESTAURANT_COLUMNS
from teselado.ingest.synthetic import CITY_BBOXES, list_cities, write_sample_dataset

__all__ = [
    "CITY_BBOXES",
    "ORDER_COLUMNS",
    "RESTAURANT_COLUMNS",
    "dataset_summary",
    "list_cities",
    "load_metadata",
    "load_orders",
    "load_orders_df",
    "load_restaurants_df",
    "write_sample_dataset",
]
