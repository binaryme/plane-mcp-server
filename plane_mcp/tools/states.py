"""Project state tools — list/create/update workflow states.

States are the "columns" of the Plane board: Backlog, In Progress, QA, Done.
These tools let the MCP client resolve state UUIDs by name (the big pain
point in v0.2.0 was having to guess which "started" UUID was "QA" vs
"In Progress").
"""

from typing import Any

from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context


def register_state_tools(mcp: FastMCP) -> None:
    """Register project-state tools with the MCP server."""

    @mcp.tool()
    def list_project_states(project_id: str) -> list[dict[str, Any]]:
        """
        List all workflow states (board columns) for a project.

        Returns a flat list of state dicts with: id, name, color, group,
        sequence, default. The `group` field is one of
        {backlog, unstarted, started, completed, cancelled}.

        Use this to resolve a state UUID by name before calling
        update_work_item / move_work_item_to_state, or to discover which
        custom states exist in a project's workflow.

        Args:
            project_id: UUID of the project.
        """
        client, workspace_slug = get_plane_client_context()
        response = client.states.list(
            workspace_slug=workspace_slug,
            project_id=project_id,
        )
        # Newer SDK returns PaginatedStateResponse with `results`; older
        # self-hosted returns a raw list. Handle both shapes.
        results = getattr(response, "results", None)
        if results is None:
            results = response
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "color": s.color,
                "group": s.group,
                "sequence": getattr(s, "sequence", None),
                "default": getattr(s, "default", False),
            }
            for s in results
        ]

    @mcp.tool()
    def get_state_by_name(project_id: str, state_name: str) -> dict[str, Any] | None:
        """
        Find a state by its display name (case-insensitive).

        Convenience wrapper around list_project_states for the common
        case "move ticket to QA" / "move ticket to Done" — avoids a second
        roundtrip when the caller only has the name.

        Returns the first match or None.

        Args:
            project_id: UUID of the project.
            state_name: State name to match (e.g., "QA", "En progreso").
        """
        client, workspace_slug = get_plane_client_context()
        response = client.states.list(
            workspace_slug=workspace_slug,
            project_id=project_id,
        )
        results = getattr(response, "results", None) or response
        needle = state_name.strip().lower()
        for s in results:
            if s.name.strip().lower() == needle:
                return {
                    "id": str(s.id),
                    "name": s.name,
                    "color": s.color,
                    "group": s.group,
                }
        return None
