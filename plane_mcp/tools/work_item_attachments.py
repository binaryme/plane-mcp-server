"""Work item attachments — read-only for now (listing + get)."""

from typing import Any

from fastmcp import FastMCP

from plane_mcp import _raw


def register_attachment_tools(mcp: FastMCP) -> None:
    """Register work-item attachment tools."""

    @mcp.tool()
    def list_work_item_attachments(
        project_id: str, work_item_id: str
    ) -> list[dict[str, Any]]:
        """
        List attachments on a work item.

        Returns each attachment's id, filename, size, mime type, download
        URL, and uploader. Self-hosted Plane uses the `issue-attachments`
        endpoint (asset v2).

        Note: upload requires multipart/form-data with a pre-signed URL
        exchange — not implemented here yet. To attach a file, use the
        Plane UI for now.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the work item.
        """
        slug = _raw.workspace_slug()
        path = (
            f"workspaces/{slug}/projects/{project_id}/issues/{work_item_id}"
            f"/issue-attachments/"
        )
        response = _raw.get(path)
        results = (
            response.get("results", response) if isinstance(response, dict) else response
        )
        return [
            {
                "id": a.get("id"),
                "attributes": a.get("attributes"),  # dict: filename, size, mime
                "asset": a.get("asset"),
                "asset_url": a.get("asset_url"),
                "created_by": a.get("created_by"),
                "created_at": a.get("created_at"),
            }
            for a in results
        ]
