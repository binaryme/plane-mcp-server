"""Tools for Plane MCP Server."""

from fastmcp import FastMCP

from plane_mcp.tools.comments import register_comment_tools
from plane_mcp.tools.cycles import register_cycle_tools
from plane_mcp.tools.initiatives import register_initiative_tools
from plane_mcp.tools.intake import register_intake_tools
from plane_mcp.tools.labels import register_label_tools
from plane_mcp.tools.modules import register_module_tools
from plane_mcp.tools.projects import register_project_tools
from plane_mcp.tools.sprint_search import register_sprint_search_tools
from plane_mcp.tools.states import register_state_tools
from plane_mcp.tools.users import register_user_tools
from plane_mcp.tools.work_item_activity import register_activity_tools
from plane_mcp.tools.work_item_attachments import register_attachment_tools
from plane_mcp.tools.work_item_links import register_work_item_link_tools
from plane_mcp.tools.work_item_properties import register_work_item_property_tools
from plane_mcp.tools.work_items import register_work_item_tools
from plane_mcp.tools.workflows import register_workflow_tools
from plane_mcp.tools.workspace_members import register_workspace_member_tools


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    register_project_tools(mcp)
    register_work_item_tools(mcp)
    register_cycle_tools(mcp)
    register_user_tools(mcp)
    register_module_tools(mcp)
    register_initiative_tools(mcp)
    register_intake_tools(mcp)
    register_work_item_property_tools(mcp)

    # AllSign extensions (Phase 1) — states, labels, comments, workspace members.
    register_state_tools(mcp)
    register_label_tools(mcp)
    register_comment_tools(mcp)
    register_workspace_member_tools(mcp)

    # AllSign extensions (Phase 2) — activity, attachments, external links,
    # and composite workflow helpers (move-by-name, bulk transitions).
    register_activity_tools(mcp)
    register_attachment_tools(mcp)
    register_work_item_link_tools(mcp)
    register_workflow_tools(mcp)

    # AllSign extensions (Phase 3) — sprint awareness + advanced search.
    register_sprint_search_tools(mcp)
