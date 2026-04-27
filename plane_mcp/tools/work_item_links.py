"""Work item external links — Linear, Figma, GitHub PRs, docs.

Self-hosted Plane exposes `/issues/{id}/links/` for arbitrary URL attachments.
Use these instead of the work-item-to-work-item "relations" endpoint (which
is not available on this Plane version).
"""

from typing import Any

from fastmcp import FastMCP

from plane_mcp import _raw


def register_work_item_link_tools(mcp: FastMCP) -> None:
    """Register work-item external-link tools."""

    @mcp.tool()
    def list_work_item_links(
        project_id: str, work_item_id: str
    ) -> list[dict[str, Any]]:
        """List external URLs attached to a work item."""
        slug = _raw.workspace_slug()
        path = (
            f"workspaces/{slug}/projects/{project_id}/issues/{work_item_id}/links/"
        )
        response = _raw.get(path)
        results = (
            response.get("results", response) if isinstance(response, dict) else response
        )
        return [
            {
                "id": l.get("id"),
                "title": l.get("title"),
                "url": l.get("url"),
                "created_by": l.get("created_by"),
                "created_at": l.get("created_at"),
            }
            for l in results
        ]

    @mcp.tool()
    def create_work_item_link(
        project_id: str,
        work_item_id: str,
        url: str,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Attach an external URL to a work item (PR, Figma, doc, etc.).

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the work item.
            url: The external URL.
            title: Optional display title (defaults to URL if omitted).
        """
        slug = _raw.workspace_slug()
        path = (
            f"workspaces/{slug}/projects/{project_id}/issues/{work_item_id}/links/"
        )
        body: dict[str, Any] = {"url": url}
        if title:
            body["title"] = title
        data = _raw.post(path, body)
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "url": data.get("url"),
            "created_at": data.get("created_at"),
        }
