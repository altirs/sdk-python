from __future__ import annotations
from ._version import __version__


import re
from typing import Any

import httpx

from .types import (
    BatchResponse,
    BatchResultItem,
    CheckOptions,
    CheckPayload,
    CheckResponse,
    AltirsConfig,
    HallucinationOptions,
    PiiOptions,
    Violation,
)

_CAMEL_RE = re.compile(r"([a-z0-9])([A-Z])")


def _to_snake(name: str) -> str:
    return _CAMEL_RE.sub(r"\1_\2", name).lower()


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _serialize(obj: Any) -> Any:
    """Convert a dataclass (or primitive) to a camelCase dict for JSON."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if hasattr(obj, "__dataclass_fields__"):
        result: dict[str, Any] = {}
        for key in obj.__dataclass_fields__:
            value = getattr(obj, key)
            if value is not None:
                result[_to_camel(key)] = _serialize(value)
        return result
    return obj


def _parse_violation(data: dict[str, Any]) -> Violation:
    return Violation(
        type=data["type"],
        category=data["category"],
        severity=data["severity"],
        description=data["description"],
    )


def _parse_check_response(data: dict[str, Any]) -> CheckResponse:
    return CheckResponse(
        safe=data["safe"],
        blocked=data["blocked"],
        score=data["score"],
        violations=[_parse_violation(v) for v in data.get("violations", [])],
        request_id=data["requestId"],
        latency_ms=data["latencyMs"],
        masked_input=data.get("maskedInput"),
        masked_response=data.get("maskedResponse"),
        recommendation=data.get("recommendation"),
    )


def _parse_batch_result_item(data: dict[str, Any]) -> BatchResultItem:
    return BatchResultItem(
        index=data["index"],
        safe=data["safe"],
        blocked=data["blocked"],
        score=data["score"],
        violations=[_parse_violation(v) for v in data.get("violations", [])],
        latency_ms=data["latencyMs"],
        masked_input=data.get("maskedInput"),
        masked_response=data.get("maskedResponse"),
        recommendation=data.get("recommendation"),
    )


def _parse_batch_response(data: dict[str, Any]) -> BatchResponse:
    return BatchResponse(
        results=[_parse_batch_result_item(r) for r in data["results"]],
        total=data["total"],
        request_id=data["requestId"],
        latency_ms=data["latencyMs"],
    )


class AltirsError(Exception):
    """Error raised when the Altirs API returns a non-2xx response."""

    def __init__(self, message: str, status: int, request_id: str) -> None:
        super().__init__(message)
        self.status = status
        self.request_id = request_id


class Altirs:
    """Client for the Guardrails-as-a-Service API."""

    def __init__(self, config: AltirsConfig) -> None:
        if not config.api_key:
            raise ValueError("Altirs SDK: api_key is required")

        self._api_key = config.api_key
        self._base_url = config.base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=config.timeout,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": self._api_key,
                "X-SDK-Version": f"python/{__version__}",
            },
        )

    def check(self, payload: CheckPayload) -> CheckResponse:
        """Run guardrail checks on a single input/response pair."""
        data = self._request("/v1/guardrail/check", _serialize(payload))
        return _parse_check_response(data)

    def batch(self, items: list[CheckPayload]) -> BatchResponse:
        """Run guardrail checks on multiple input/response pairs (max 20)."""
        body = {"items": [_serialize(item) for item in items]}
        data = self._request("/v1/guardrail/batch", body)
        return _parse_batch_response(data)

    def is_safe(self, input: str) -> bool:
        """Convenience: returns True if the input passes all guardrail checks."""
        result = self.check(CheckPayload(input=input))
        return result.safe

    def mask_pii(self, text: str) -> str:
        """Convenience: mask PII in the given text and return the masked version."""
        result = self.check(
            CheckPayload(
                input=text,
                checks=["pii"],
                options=CheckOptions(pii=PiiOptions(mask=True)),
            )
        )
        return result.masked_input or text

    def _request(self, path: str, body: Any) -> dict[str, Any]:
        try:
            resp = self._client.post(path, json=body)
        except httpx.TimeoutException as exc:
            raise AltirsError(
                f"Request timed out after {self._client.timeout}s",
                408,
                "timeout",
            ) from exc
        except httpx.HTTPError as exc:
            raise AltirsError(str(exc), 0, "unknown") from exc

        data: dict[str, Any] = resp.json()

        if not resp.is_success:
            raise AltirsError(
                data.get("error", f"Request failed with status {resp.status_code}"),
                resp.status_code,
                data.get("requestId", "unknown"),
            )

        return data

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Altirs:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
