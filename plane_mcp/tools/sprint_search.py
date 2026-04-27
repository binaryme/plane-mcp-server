"""Phase 3 — sprint awareness + advanced search.

Three ergonomic tools for day-to-day workflows:
  * list_my_work_items — "what's on my plate?"
  * get_cycle_progress — sprint burndown data (already computed by Plane)
  * search_work_items_advanced — filter by state_group, priority, label, assignee, dates
"""

from typing import Any

from fastmcp import FastMCP

from plane_mcp import _raw


def register_sprint_search_tools(mcp: FastMCP) -> None:
    """Register phase-3 tools with the MCP server."""

    @mcp.tool()
    def list_my_work_items(
        project_id: str,
        state_group: str | None = None,
        priority: str | None = None,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        List work items assigned to the current user on a project.

        Combines `/api/v1/users/me/` + `/projects/.../issues/?assignees=<id>`.
        Ideal for "what am I working on?" and standup summaries.

        Args:
            project_id: UUID of the project.
            state_group: Optional group filter (backlog|unstarted|started|completed|cancelled).
            priority: Optional priority filter (urgent|high|medium|low|none).
            per_page: Max results (default 50).
        """
        # 1. Resolve current user — /users/me/ is workspace-agnostic.
        slug = _raw.workspace_slug()
        me = _raw.get("users/me/")
        user_id = me.get("id") if isinstance(me, dict) else None
        if not user_id:
            raise RuntimeError("Could not resolve current user id from /users/me/")

        params: dict[str, Any] = {"assignees": user_id, "per_page": per_page}
        if state_group:
            params["state_group"] = state_group
        if priority:
            params["priority"] = priority

        path = f"workspaces/{slug}/projects/{project_id}/issues/"
        response = _raw.get(path, params=params)
        results = (
            response.get("results", [])
            if isinstance(response, dict)
            else response
        )
        return {
            "user_id": user_id,
            "display_name": me.get("display_name"),
            "count": len(results),
            "filters": {"state_group": state_group, "priority": priority},
            "items": [
                {
                    "id": it.get("id"),
                    "sequence_id": it.get("sequence_id"),
                    "name": it.get("name"),
                    "priority": it.get("priority"),
                    "state_id": it.get("state"),
                    "updated_at": it.get("updated_at"),
                    "target_date": it.get("target_date"),
                }
                for it in results
            ],
        }

    @mcp.tool()
    def get_cycle_progress(project_id: str, cycle_id: str) -> dict[str, Any]:
        """
        Return progress metrics for a cycle (sprint).

        Plane pre-computes per-state counts on the cycle resource, so this
        is a single request. Useful for burndown reports and standup sync.

        Args:
            project_id: UUID of the project.
            cycle_id: UUID of the cycle.
        """
        slug = _raw.workspace_slug()
        path = f"workspaces/{slug}/projects/{project_id}/cycles/{cycle_id}/"
        c = _raw.get(path)
        total = c.get("total_issues") or 0
        completed = c.get("completed_issues") or 0
        pct = round((completed / total) * 100, 1) if total else 0.0
        return {
            "id": c.get("id"),
            "name": c.get("name"),
            "start_date": c.get("start_date"),
            "end_date": c.get("end_date"),
            "owned_by": c.get("owned_by"),
            "total_issues": total,
            "completed_issues": completed,
            "started_issues": c.get("started_issues") or 0,
            "unstarted_issues": c.get("unstarted_issues") or 0,
            "backlog_issues": c.get("backlog_issues") or 0,
            "cancelled_issues": c.get("cancelled_issues") or 0,
            "progress_pct": pct,
        }

    @mcp.tool()
    def search_work_items_advanced(
        project_id: str,
        state_group: str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        label_id: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        Filter work items by multiple criteria in a single call.

        Supersedes the basic `search_work_items` tool (which only does free-text
        and returned empty results during real usage). Uses Plane's native
        query params on `/projects/.../issues/`.

        Args:
            project_id: UUID of the project.
            state_group: backlog|unstarted|started|completed|cancelled
            priority: urgent|high|medium|low|none
            assignee_id: UUID of the assignee (use list_workspace_members to resolve).
            label_id: UUID of the label (use list_project_labels to resolve).
            created_after: ISO date — issues created on/after this date.
            created_before: ISO date — issues created on/before this date.
            updated_after: ISO date — issues updated on/after this date (great for standups).
            per_page: Max results (default 50).
        """
        slug = _raw.workspace_slug()
        params: dict[str, Any] = {"per_page": per_page}
        if state_group:
            params["state_group"] = state_group
        if priority:
            params["priority"] = priority
        if assignee_id:
            params["assignees"] = assignee_id
        if label_id:
            params["labels"] = label_id
        if created_after:
            params["created_at__gte"] = created_after
        if created_before:
            params["created_at__lte"] = created_before
        if updated_after:
            params["updated_at__gte"] = updated_after

        path = f"workspaces/{slug}/projects/{project_id}/issues/"
        response = _raw.get(path, params=params)
        results = (
            response.get("results", [])
            if isinstance(response, dict)
            else response
        )
        return {
            "count": len(results),
            "total_count": (
                response.get("total_count")
                if isinstance(response, dict)
                else len(results)
            ),
            "filters": {k: v for k, v in params.items() if k != "per_page"},
            "items": [
                {
                    "id": it.get("id"),
                    "sequence_id": it.get("sequence_id"),
                    "name": it.get("name"),
                    "priority": it.get("priority"),
                    "state_id": it.get("state"),
                    "assignees": it.get("assignees"),
                    "labels": it.get("labels"),
                    "created_at": it.get("created_at"),
                    "updated_at": it.get("updated_at"),
                }
                for it in results
            ],
        }
