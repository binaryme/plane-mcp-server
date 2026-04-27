"""Raw HTTP helper for Plane API calls not yet covered by the SDK.

Used by tools that need legacy-path endpoints (/issues/ instead of /work-items/)
or endpoints not wrapped by the vendored plane-sdk (comments, activity,
workspace members, attachments, etc.).

Shares the base_url + api_key that the main client is already using, so there's
a single source of truth for auth.
"""

from __future__ import annotations

from typing import Any

import httpx

from plane_mcp.client import get_plane_client_context


def _base_and_headers() -> tuple[str, dict[str, str]]:
    client, _ = get_plane_client_context()
    config = client.config
    # config.base_path already includes /api/v1 suffix.
    base = config.base_path.rstrip("/")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if getattr(config, "api_key", None):
        headers["X-Api-Key"] = config.api_key
    else:
        # Bearer fallback (OAuth) if api_key is absent.
        token = getattr(config, "access_token", None)
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return base, headers


def get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET {base}/{path} — path must be relative (no leading slash)."""
    base, headers = _base_and_headers()
    with httpx.Client(timeout=30.0) as http:
        r = http.get(f"{base}/{path.lstrip('/')}", headers=headers, params=params)
        r.raise_for_status()
        return r.json()


def post(path: str, body: dict[str, Any]) -> Any:
    base, headers = _base_and_headers()
    with httpx.Client(timeout=30.0) as http:
        r = http.post(f"{base}/{path.lstrip('/')}", headers=headers, json=body)
        r.raise_for_status()
        return r.json() if r.content else None


def patch(path: str, body: dict[str, Any]) -> Any:
    base, headers = _base_and_headers()
    with httpx.Client(timeout=30.0) as http:
        r = http.patch(f"{base}/{path.lstrip('/')}", headers=headers, json=body)
        r.raise_for_status()
        return r.json() if r.content else None


def delete(path: str) -> None:
    base, headers = _base_and_headers()
    with httpx.Client(timeout=30.0) as http:
        r = http.delete(f"{base}/{path.lstrip('/')}", headers=headers)
        r.raise_for_status()


def workspace_slug() -> str:
    _, slug = get_plane_client_context()
    return slug
