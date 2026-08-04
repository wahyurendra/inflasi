"""OpenAPI customisation shared by Swagger UI and exported API contracts."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI


_ERROR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["detail"],
    "properties": {
        "detail": {
            "description": "Pesan error yang aman ditampilkan kepada client.",
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "object"}},
            ],
        },
    },
}


def _error_response(description: str, detail: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {"detail": detail},
            },
        },
    }


def install_openapi(app: FastAPI) -> None:
    """Install deterministic OpenAPI additions without changing API behaviour.

    FastAPI already derives paths, parameters and Pydantic schemas from the
    application. This layer documents the Firebase bearer token and common
    error responses that otherwise remain implicit in Swagger UI.
    """

    default_openapi: Callable[[], dict[str, Any]] = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = default_openapi()
        components = schema.setdefault("components", {})
        components.setdefault("schemas", {})["ErrorResponse"] = _ERROR_SCHEMA

        responses = components.setdefault("responses", {})
        responses.update(
            {
                "UnauthorizedError": _error_response(
                    "Firebase ID token tidak ada, tidak valid, atau kedaluwarsa.",
                    "Tidak terautentikasi",
                ),
                "ForbiddenError": _error_response(
                    "User terautentikasi tetapi role-nya tidak memiliki akses.",
                    "admin role required",
                ),
            }
        )

        # Security is generated per operation by FastAPI from Depends(HTTPBearer).
        # Add the corresponding response contracts only to protected operations;
        # public endpoints must remain callable without clicking Authorize.
        for path_item in schema.get("paths", {}).values():
            for operation in path_item.values():
                if not isinstance(operation, dict) or not operation.get("security"):
                    continue
                operation_responses = operation.setdefault("responses", {})
                operation_responses.setdefault(
                    "401", {"$ref": "#/components/responses/UnauthorizedError"}
                )
                operation_responses.setdefault(
                    "403", {"$ref": "#/components/responses/ForbiddenError"}
                )

        schema["x-api-audience"] = ["web", "android", "internal-services"]
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
