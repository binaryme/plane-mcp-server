"""Workspace member tools — look up users to assign work items by name."""

from typing import Any

from fastmcp import FastMCP

from plane_mcp import _raw


def register_workspace_member_tools(mcp: FastMCP) -> None:
    """Register workspace member tools with the MCP server."""

    @mcp.tool()
    def list_workspace_members() -> list[dict[str, Any]]:
        """
        List all members of the active workspace.

        Returns each member's user id, display name, email, role, and
        avatar URL. Use this to resolve a human name (e.g., "Israel") to
        the user UUID expected by create_work_item / update_work_item's
        `assignees` param.
        """
        slug = _raw.workspace_slug()
        response = _raw.get(f"workspaces/{slug}/members/")
        results = (
            response.get("results", response) if isinstance(response, dict) else response
        )
        out: list[dict[str, Any]] = []
        for m in results:
            member = m.get("member") or m
            out.append(
                {
                    "id": str(member.get("id")),
                    "display_name": member.get("display_name")
                    or member.get("first_name")
                    or member.get("email"),
                    "first_name": member.get("first_name"),
                    "last_name": member.get("last_name"),
                    "email": member.get("email"),
                    "avatar_url": member.get("avatar_url") or member.get("avatar"),
                    "role": m.get("role"),
                }
            )
        return out

    @mcp.tool()
    def get_member_by_name(name_or_email: str) -> dict[str, Any] | None:
        """
        Find a workspace member by name fragment OR email (case-insensitive).

        Matches on display_name, first_name, last_name, or email (substring).
        Returns the first match or None.
        """
        needle = name_or_email.strip().lower()
        if not needle:
            return None
        slug = _raw.workspace_slug()
        response = _raw.get(f"workspaces/{slug}/members/")
        results = (
            response.get("results", response) if isinstance(response, dict) else response
        )
        for m in results:
            member = m.get("member") or m
            haystack = " ".join(
                str(member.get(k, "")).lower()
                for k in ("display_name", "first_name", "last_name", "email")
            )
            if needle in haystack:
                return {
                    "id": str(member.get("id")),
                    "display_name": member.get("display_name"),
                    "email": member.get("email"),
                }
        return None
