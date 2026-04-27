"""Label tools — list/create labels for tagging work items."""

from typing import Any

from fastmcp import FastMCP

from plane_mcp.client import get_plane_client_context


def register_label_tools(mcp: FastMCP) -> None:
    """Register label tools with the MCP server."""

    @mcp.tool()
    def list_project_labels(project_id: str) -> list[dict[str, Any]]:
        """
        List all labels available on a project.

        Labels are reusable tags (e.g., "bug", "frontend", "QA") attached
        to work items via the `labels` field on update_work_item.

        Args:
            project_id: UUID of the project.
        """
        client, workspace_slug = get_plane_client_context()
        response = client.labels.list(
            workspace_slug=workspace_slug, project_id=project_id
        )
        results = getattr(response, "results", None) or response
        return [
            {
                "id": str(lb.id),
                "name": lb.name,
                "color": lb.color,
                "description": getattr(lb, "description", ""),
            }
            for lb in results
        ]

    @mcp.tool()
    def create_project_label(
        project_id: str,
        name: str,
        color: str = "#5957AB",
        description: str = "",
    ) -> dict[str, Any]:
        """
        Create a new label on a project.

        Args:
            project_id: UUID of the project.
            name: Label name (unique per project).
            color: Hex color (default AllSign purple).
            description: Optional description.
        """
        client, workspace_slug = get_plane_client_context()
        from plane.models.labels import CreateLabel

        lb = client.labels.create(
            workspace_slug=workspace_slug,
            project_id=project_id,
            data=CreateLabel(name=name, color=color, description=description),
        )
        return {
            "id": str(lb.id),
            "name": lb.name,
            "color": lb.color,
            "description": getattr(lb, "description", ""),
        }

    @mcp.tool()
    def get_label_by_name(project_id: str, label_name: str) -> dict[str, Any] | None:
        """
        Find a label by its name (case-insensitive). Returns None if not found.

        Convenience helper so the caller can attach labels to work items
        without a separate list+filter roundtrip.
        """
        client, workspace_slug = get_plane_client_context()
        response = client.labels.list(
            workspace_slug=workspace_slug, project_id=project_id
        )
        results = getattr(response, "results", None) or response
        needle = label_name.strip().lower()
        for lb in results:
            if lb.name.strip().lower() == needle:
                return {"id": str(lb.id), "name": lb.name, "color": lb.color}
        return None
