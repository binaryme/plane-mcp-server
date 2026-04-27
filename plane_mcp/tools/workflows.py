"""Cross-cutting workflow helpers — move-by-name + bulk state transitions.

These wrappers compose existing primitives to eliminate the three most
common pain points when driving Plane from an LLM:

  1. "I know the state is called 'QA' but I need its UUID." → move_work_item_to_state
  2. "I want to move 12 tickets at once." → bulk_move_work_items_to_state
  3. "What are this project's board columns?" → already in states.list_project_states
"""

from typing import Any

from fastmcp import FastMCP

from plane_mcp import _raw
from plane_mcp.client import get_plane_client_context


def _resolve_state_id(project_id: str, state_name: str) -> str | None:
    client, workspace_slug = get_plane_client_context()
    response = client.states.list(
        workspace_slug=workspace_slug, project_id=project_id
    )
    results = getattr(response, "results", None) or response
    needle = state_name.strip().lower()
    for s in results:
        if s.name.strip().lower() == needle:
            return str(s.id)
    return None


def register_workflow_tools(mcp: FastMCP) -> None:
    """Register composite workflow helper tools."""

    @mcp.tool()
    def move_work_item_to_state(
        project_id: str,
        work_item_id: str,
        state_name: str,
    ) -> dict[str, Any]:
        """
        Move a single work item to a state resolved by NAME (not UUID).

        Saves a `list_project_states` → filter dance on every transition.
        Matches state name case-insensitively.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the work item.
            state_name: Human-readable state name (e.g., "QA", "En progreso", "Hecho").

        Returns:
            dict with `resolved_state_id`, `from_state_id` (pre-change), `success`.

        Raises:
            ValueError: If state_name doesn't match any state on the project.
        """
        state_id = _resolve_state_id(project_id, state_name)
        if not state_id:
            raise ValueError(
                f"State '{state_name}' not found on project {project_id}. "
                f"Use list_project_states to see available names."
            )
        slug = _raw.workspace_slug()
        path = f"workspaces/{slug}/projects/{project_id}/issues/{work_item_id}/"
        # Read prior state for audit trail in the response.
        try:
            prior = _raw.get(path)
            from_state = prior.get("state") if isinstance(prior, dict) else None
        except Exception:  # noqa: BLE001
            from_state = None

        _raw.patch(path, {"state": state_id})
        return {
            "success": True,
            "work_item_id": work_item_id,
            "resolved_state_id": state_id,
            "state_name": state_name,
            "from_state_id": from_state,
        }

    @mcp.tool()
    def bulk_move_work_items_to_state(
        project_id: str,
        work_item_ids: list[str],
        state_name: str,
    ) -> dict[str, Any]:
        """
        Move N work items to the same state in a single call.

        Resolves `state_name` once, then PATCHes each work item sequentially.
        Returns counts and a per-id status breakdown so the caller can retry
        failures.

        Ideal for backlog grooming ("move these 12 tickets to Cancelled")
        or sprint cleanup ("move everything in En Progreso to QA").

        Args:
            project_id: UUID of the project.
            work_item_ids: List of work-item UUIDs.
            state_name: Target state name (case-insensitive).
        """
        if not work_item_ids:
            return {"success": True, "count": 0, "results": []}

        state_id = _resolve_state_id(project_id, state_name)
        if not state_id:
            raise ValueError(
                f"State '{state_name}' not found on project {project_id}."
            )

        slug = _raw.workspace_slug()
        results: list[dict[str, Any]] = []
        succeeded = 0
        for wid in work_item_ids:
            path = f"workspaces/{slug}/projects/{project_id}/issues/{wid}/"
            try:
                _raw.patch(path, {"state": state_id})
                results.append({"id": wid, "ok": True})
                succeeded += 1
            except Exception as e:  # noqa: BLE001
                results.append({"id": wid, "ok": False, "error": str(e)[:200]})

        return {
            "success": succeeded == len(work_item_ids),
            "count": len(work_item_ids),
            "succeeded": succeeded,
            "failed": len(work_item_ids) - succeeded,
            "resolved_state_id": state_id,
            "state_name": state_name,
            "results": results,
        }

    @mcp.tool()
    def bulk_update_work_item_priority(
        project_id: str,
        work_item_ids: list[str],
        priority: str,
    ) -> dict[str, Any]:
        """
        Set the same priority on N work items.

        Args:
            project_id: UUID of the project.
            work_item_ids: List of work-item UUIDs.
            priority: One of: urgent, high, medium, low, none.
        """
        allowed = {"urgent", "high", "medium", "low", "none"}
        if priority not in allowed:
            raise ValueError(
                f"priority must be one of {sorted(allowed)}, got {priority!r}"
            )
        slug = _raw.workspace_slug()
        results: list[dict[str, Any]] = []
        succeeded = 0
        for wid in work_item_ids:
            path = f"workspaces/{slug}/projects/{project_id}/issues/{wid}/"
            try:
                _raw.patch(path, {"priority": priority})
                results.append({"id": wid, "ok": True})
                succeeded += 1
            except Exception as e:  # noqa: BLE001
                results.append({"id": wid, "ok": False, "error": str(e)[:200]})
        return {
            "success": succeeded == len(work_item_ids),
            "count": len(work_item_ids),
            "succeeded": succeeded,
            "failed": len(work_item_ids) - succeeded,
            "priority": priority,
            "results": results,
        }
