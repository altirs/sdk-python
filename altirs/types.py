from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["high", "medium", "low"]

CheckName = Literal["content_safety", "pii", "prompt_injection", "hallucination"]


@dataclass
class Violation:
    type: str
    category: str
    severity: Severity
    description: str


@dataclass
class PiiOptions:
    mask: bool | None = None


@dataclass
class HallucinationOptions:
    context: str | None = None


@dataclass
class CheckOptions:
    pii: PiiOptions | None = None
    hallucination: HallucinationOptions | None = None


@dataclass
class CheckPayload:
    input: str | None = None
    response: str | None = None
    checks: list[CheckName] | None = None
    options: CheckOptions | None = None


@dataclass
class CheckResponse:
    safe: bool
    blocked: bool
    score: float
    violations: list[Violation]
    request_id: str
    latency_ms: int
    masked_input: str | None = None
    masked_response: str | None = None
    recommendation: str | None = None


@dataclass
class BatchPayload:
    items: list[CheckPayload]


@dataclass
class BatchResultItem:
    index: int
    safe: bool
    blocked: bool
    score: float
    violations: list[Violation]
    latency_ms: int
    masked_input: str | None = None
    masked_response: str | None = None
    recommendation: str | None = None


@dataclass
class BatchResponse:
    results: list[BatchResultItem]
    total: int
    request_id: str
    latency_ms: int


@dataclass
class ErrorResponse:
    error: str
    request_id: str


@dataclass
class AltirsConfig:
    api_key: str
    base_url: str = "https://altirs.ai/api"
    timeout: int = 30
