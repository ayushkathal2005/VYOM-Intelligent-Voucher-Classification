"""Ingestion and data normalization package for VYOM+."""

from app.ingestion.schema import (
    CanonicalTransaction,
    IngestionResult,
    SchemaWarning,
)
from app.ingestion.parser import (
    parse_transaction_file,
    IngestionError,
)
from app.ingestion.aliases import (
    resolve_canonical_field,
    clean_header_string,
    CANONICAL_ALIASES,
    is_target_column,
    TARGET_LABEL_COLUMNS,
)

__all__ = [
    "CanonicalTransaction",
    "IngestionResult",
    "SchemaWarning",
    "parse_transaction_file",
    "IngestionError",
    "resolve_canonical_field",
    "clean_header_string",
    "CANONICAL_ALIASES",
    "is_target_column",
    "TARGET_LABEL_COLUMNS",
]

