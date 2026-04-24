# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Dependency management uses `uv` (see `uv.lock`). Python >= 3.10.

```bash
uv sync --extra dev              # install runtime + dev deps
uv run pytest                    # run full test suite
uv run pytest tests/test_env.py::test_env_loading_integration   # run a single test
uv run black plane_mcp/          # format
uv run ruff check plane_mcp/     # lint
```

Running the server locally:

```bash
uv run plane-mcp-server stdio    # stdio transport (requires PLANE_API_KEY + PLANE_WORKSPACE_SLUG)
uv run plane-mcp-server http     # HTTP + SSE on port 8211
# also: python -m plane_mcp <stdio|http>
```

Docker: `docker build -t plane-mcp . && docker run -p 8211:8211 plane-mcp` (entrypoint defaults to `http`).

## Architecture

This is a FastMCP-based MCP server exposing Plane (project management) APIs as MCP tools. Three transports share the same tool registry.

### Entry point and transports — `plane_mcp/__main__.py`

`main()` loads `.env` from the project root, then dispatches on argv[1]:

- `stdio` — requires `PLANE_API_KEY` + `PLANE_WORKSPACE_SLUG` env vars; runs `get_stdio_mcp().run()`.
- `http` — mounts **three** MCP apps under a single Starlette app on port 8211:
  - `/http/` → OAuth-authenticated streamable HTTP MCP (`get_oauth_mcp("/http")`)
  - `/http/api-key/` → header/PAT-authenticated HTTP MCP (`get_header_mcp()`)
  - `/` → OAuth-authenticated **SSE** MCP (legacy, same provider as `/http/`)
  - OAuth well-known routes are registered at the root for both `/mcp` and `/sse`.
  - A `combined_lifespan` context manager nests the three apps' lifespans so Starlette initializes them all.

### Server factories — `plane_mcp/server.py`

Three factories (`get_oauth_mcp`, `get_header_mcp`, `get_stdio_mcp`) each build a `FastMCP` instance and call `register_tools(mcp)`. They differ only in the auth provider attached. OAuth mode uses Redis-backed `client_storage` if `REDIS_HOST`/`REDIS_PORT` are set, otherwise `MemoryStore`.

### Authentication — `plane_mcp/auth/`

Two providers, both emit a FastMCP `AccessToken` with an `auth_method` claim that downstream code reads to decide how to authenticate against Plane:

- `PlaneOAuthProvider` (`plane_oauth_provider.py`) — extends FastMCP's `OAuthProxy` to Plane's `/auth/o/authorize-app/` and `/auth/o/token/`. The inner `PlaneOAuthTokenVerifier` verifies by calling `GET /api/v1/users/me/` and then `GET /auth/o/app-installation/` to extract the user's `workspace_slug`. Emits `auth_method="oauth"`.
- `PlaneHeaderAuthProvider` (`plane_header_auth_provider.py`) — trivial PAT verifier that reads the `x-workspace-slug` HTTP header (the token itself comes from the Authorization header via FastMCP). Emits `auth_method="api_key_header"`.

Stdio mode has no auth provider; it reads `PLANE_API_KEY` + `PLANE_WORKSPACE_SLUG` directly from env.

### Client resolution — `plane_mcp/client.py`

`get_plane_client_context()` is called at the top of every tool. It reconciles the three auth paths into a single `PlaneClient`:

1. Reads env vars as defaults (`PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG`, `PLANE_BASE_URL`).
2. If a FastMCP `AccessToken` is active (HTTP transports), overrides workspace_slug from token claims and branches on `auth_method`: `api_key_env` / `api_key_header` → constructs `PlaneClient(api_key=...)`; otherwise (`oauth`) → constructs `PlaneClient(access_token=...)`.

**Key invariant**: tool functions always go through `get_plane_client_context()`. Do not read `PLANE_*` env vars directly from within a tool — that bypasses the OAuth/header token flow and will break in HTTP mode.

### Tool registration — `plane_mcp/tools/`

`register_tools()` (in `tools/__init__.py`) invokes one `register_<domain>_tools(mcp)` per module. Each module defines its tools as nested functions inside `register_*_tools`, decorated with `@mcp.tool()`. Tools call `get_plane_client_context()` then delegate to `plane-sdk` (`plane.api.*`) using Pydantic models from `plane.models.*` for request/response typing. Adding a new domain = new file in `tools/`, new registrar in `tools/__init__.py`.

### Legacy API patch — `plane_mcp/patch.py`

**Critical and load-bearing for this fork.** The official `plane-sdk` (0.2.2) targets the current Plane REST API at `/work-items/`, but this deployment targets a Plane instance that still exposes the legacy `/issues/` endpoints. `patch.py` monkey-patches `plane.api.work_items.base.WorkItems.{create,retrieve,retrieve_by_identifier,update,delete,list,search}` to rewrite URLs to `/issues/...`. It's imported (twice — intentionally? both imports remain) at the top of `__main__.py` so the patch is applied before any tool runs. Every patched method logs `[PATCH] ...` to stderr.

If you upgrade `plane-sdk`, verify the patched method signatures still match; `tests/test_issues_patch.py` guards the URL rewrites for `create` and `list`.

## Configuration

Environment variables are loaded from `.env` at the project root (loaded by `main()`, not at import time — tools reading env at import won't see them).

Stdio mode (required): `PLANE_API_KEY`, `PLANE_WORKSPACE_SLUG`. Optional: `PLANE_BASE_URL` (default `https://api.plane.so`).

HTTP mode OAuth: `PLANE_OAUTH_PROVIDER_CLIENT_ID`, `PLANE_OAUTH_PROVIDER_CLIENT_SECRET`, `PLANE_OAUTH_PROVIDER_BASE_URL` (public URL where the server is reachable — the `/http` suffix is appended automatically for the OAuth mount).

HTTP mode header/PAT: no server-side env required; clients pass `Authorization: Bearer <token>` and `X-Workspace-slug: <slug>` per request.

Optional: `REDIS_HOST` + `REDIS_PORT` (OAuth client storage), `FASTMCP_LOG_LEVEL`, `FASTMCP_PORT`.
