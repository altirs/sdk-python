"""Altirs SDK — Python client for the Guardrails-as-a-Service API."""

from .client import Altirs, AltirsError
from .types import (
    BatchPayload,
    BatchResponse,
    BatchResultItem,
    CheckName,
    CheckOptions,
    CheckPayload,
    CheckResponse,
    ErrorResponse,
    AltirsConfig,
    HallucinationOptions,
    PiiOptions,
    Severity,
    Violation,
)

__all__ = [
    "Altirs",
    "AltirsError",
    "AltirsConfig",
    "CheckPayload",
    "CheckResponse",
    "CheckName",
    "CheckOptions",
    "PiiOptions",
    "HallucinationOptions",
    "BatchPayload",
    "BatchResponse",
    "BatchResultItem",
    "ErrorResponse",
    "Violation",
    "Severity",
]
