"""Work item activity feed — history of state/assignee/field changes."""

from typing import Any

from fastmcp import FastMCP

from plane_mcp import _raw


def register_activity_tools(mcp: FastMCP) -> None:
    """Register work-item activity tools."""

    @mcp.tool()
    def list_work_item_activity(
        project_id: str, work_item_id: str
    ) -> list[dict[str, Any]]:
        """
        List the full activity timeline of a work item.

        Returns each change (state transition, assignee change, label added,
        description edit, etc.) with: verb, field, old_value, new_value,
        actor, timestamp. Useful for triaging stale tickets, QA review
        ("who moved this to Done?"), and daily standups.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the work item.
        """
        slug = _raw.workspace_slug()
        path = f"workspaces/{slug}/projects/{project_id}/issues/{work_item_id}/activities/"
        response = _raw.get(path)
        results = (
            response.get("results", response) if isinstance(response, dict) else response
        )
        return [
            {
                "id": a.get("id"),
                "verb": a.get("verb"),  # created, updated, commented, etc.
                "field": a.get("field"),  # state, assignees, labels, ...
                "old_value": a.get("old_value"),
                "new_value": a.get("new_value"),
                "old_identifier": a.get("old_identifier"),
                "new_identifier": a.get("new_identifier"),
                "actor": a.get("actor"),
                "created_at": a.get("created_at"),
            }
            for a in results
        ]
