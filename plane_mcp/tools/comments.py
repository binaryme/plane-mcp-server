"""Work item comment tools.

Self-hosted Plane uses the legacy `/issues/` URL for comments (confirmed
via curl: `/work-items/{id}/comments/` returns 404, `/issues/{id}/comments/`
returns 200). We use the raw-HTTP helper rather than the SDK to stay
compatible with legacy deployments.
"""

from typing import Any

from fastmcp import FastMCP

from plane_mcp import _raw


def register_comment_tools(mcp: FastMCP) -> None:
    """Register work-item comment tools with the MCP server."""

    @mcp.tool()
    def list_work_item_comments(
        project_id: str, work_item_id: str
    ) -> list[dict[str, Any]]:
        """
        List all comments on a work item.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the work item.
        """
        slug = _raw.workspace_slug()
        path = f"workspaces/{slug}/projects/{project_id}/issues/{work_item_id}/comments/"
        response = _raw.get(path)
        results = response.get("results", response) if isinstance(response, dict) else response
        return [
            {
                "id": c.get("id"),
                "comment_html": c.get("comment_html"),
                "comment_stripped": c.get("comment_stripped"),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
                "actor": c.get("actor"),
                "created_by": c.get("created_by"),
            }
            for c in results
        ]

    @mcp.tool()
    def create_work_item_comment(
        project_id: str,
        work_item_id: str,
        comment_html: str,
    ) -> dict[str, Any]:
        """
        Post a new comment on a work item.

        Ideal for QA notes, implementation summaries, and cross-linking
        PRs/docs to tickets.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the work item.
            comment_html: Comment body as HTML (e.g., "<p>Ready for QA. See PR #123.</p>").
        """
        slug = _raw.workspace_slug()
        path = f"workspaces/{slug}/projects/{project_id}/issues/{work_item_id}/comments/"
        data = _raw.post(path, {"comment_html": comment_html})
        return {
            "id": data.get("id"),
            "comment_html": data.get("comment_html"),
            "created_at": data.get("created_at"),
        }

    @mcp.tool()
    def update_work_item_comment(
        project_id: str,
        work_item_id: str,
        comment_id: str,
        comment_html: str,
    ) -> dict[str, Any]:
        """Edit an existing comment. Useful for fixing typos or expanding QA notes."""
        slug = _raw.workspace_slug()
        path = (
            f"workspaces/{slug}/projects/{project_id}/issues/"
            f"{work_item_id}/comments/{comment_id}/"
        )
        data = _raw.patch(path, {"comment_html": comment_html})
        return {
            "id": data.get("id"),
            "comment_html": data.get("comment_html"),
            "updated_at": data.get("updated_at"),
        }

    @mcp.tool()
    def delete_work_item_comment(
        project_id: str, work_item_id: str, comment_id: str
    ) -> dict[str, bool]:
        """Delete a comment. Irreversible — prefer editing when possible."""
        slug = _raw.workspace_slug()
        path = (
            f"workspaces/{slug}/projects/{project_id}/issues/"
            f"{work_item_id}/comments/{comment_id}/"
        )
        _raw.delete(path)
        return {"deleted": True}
