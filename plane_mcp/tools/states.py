"""Project state tools — list/create/update workflow states.

States are the "columns" of the Plane board: Backlog, In Progress, QA, Done.
These tools let the MCP client resolve state UUIDs by name (the big pain
point in v0.2.0 was having to guess which "started" UUID was "QA" vs
"In Progress").
"""

from typing import Any

from fastmcp import FastMCP
from plane.models.states import CreateState

from plane_mcp.client import get_plane_client_context

# Default workflow states. This self-hosted Plane does NOT auto-provision
# states when a project is created via the API — and a project with zero
# states silently drops every issue you create against it (the API echoes
# back a 200 + object but never persists the row, because it has no default
# state to assign). seed_default_states() prevents that footgun.
DEFAULT_STATES: list[dict[str, Any]] = [
    {"name": "Backlog", "color": "#586172", "group": "backlog"},
    {"name": "Siguiente en cola", "color": "#4F8BFF", "group": "unstarted", "default": True},
    {"name": "En progreso", "color": "#F5B23D", "group": "started"},
    {"name": "QA", "color": "#34D8F0", "group": "started"},
    {"name": "Hecho", "color": "#16E0A3", "group": "completed"},
    {"name": "Cancelled", "color": "#FF5D5D", "group": "cancelled"},
]


def _coerce_results(response: Any) -> list[Any]:
    """Normalize a list endpoint response to a plain list.

    Newer SDK returns a paginated object with `.results`; older self-hosted
    returns a raw list. Critically, an EMPTY `.results` is still the correct
    answer — never fall through to the paginated wrapper itself (iterating it
    yields field tuples → `'tuple' object has no attribute 'name'`).
    """
    results = getattr(response, "results", None)
    return results if results is not None else response


def seed_default_states(client: Any, workspace_slug: str, project_id: str) -> list[Any]:
    """Create the default workflow states for a freshly-created project.

    Idempotent-ish: if the project already has states, this is a no-op.
    Returns the list of created (or pre-existing) State objects.
    """
    existing = _coerce_results(
        client.states.list(workspace_slug=workspace_slug, project_id=project_id)
    )
    if existing:
        return list(existing)

    created = []
    for spec in DEFAULT_STATES:
        created.append(
            client.states.create(
                workspace_slug=workspace_slug,
                project_id=project_id,
                data=CreateState(**spec),
            )
        )
    return created


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
        results = _coerce_results(response)
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
        results = _coerce_results(response)
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

    @mcp.tool()
    def create_state(
        project_id: str,
        name: str,
        group: str,
        color: str = "#586172",
        description: str | None = None,
        default: bool | None = None,
    ) -> dict[str, Any]:
        """
        Create a workflow state (board column) in a project.

        Args:
            project_id: UUID of the project.
            name: State name (e.g., "QA", "En progreso").
            group: One of {backlog, unstarted, started, completed, cancelled}.
            color: Hex color.
            description: Optional description.
            default: Mark this as the project's default state for new issues.
        """
        client, workspace_slug = get_plane_client_context()
        s = client.states.create(
            workspace_slug=workspace_slug,
            project_id=project_id,
            data=CreateState(
                name=name, group=group, color=color,
                description=description, default=default,
            ),
        )
        return {"id": str(s.id), "name": s.name, "group": s.group, "default": getattr(s, "default", False)}

    @mcp.tool()
    def seed_project_default_states(project_id: str) -> list[dict[str, Any]]:
        """
        Provision the standard workflow states for a project that has none.

        Use this to repair a project created via the API on a self-hosted
        Plane that did not auto-create states (symptom: every issue you create
        silently fails to persist). No-op if the project already has states.

        Args:
            project_id: UUID of the project.
        """
        client, workspace_slug = get_plane_client_context()
        states = seed_default_states(client, workspace_slug, project_id)
        return [
            {"id": str(s.id), "name": s.name, "group": s.group}
            for s in states
        ]
