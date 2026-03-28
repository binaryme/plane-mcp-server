
import pytest
from unittest.mock import MagicMock, patch
from plane.api.work_items.base import WorkItems
# Import main to ensure patch is applied (although we might need to manually trigger it if using mocks heavily)
# Actually, just importing patch.py should do it, but we want to test the side effects.
import plane_mcp.patch 
from plane.models.work_items import CreateWorkItem

def test_legacy_create_patch():
    """
    Test that WorkItems.create uses the /issues endpoint.
    """
    # Create a mock instance of WorkItems
    # The patch replaces WorkItems.create with legacy_create
    
    # We need to mock the _post method on the instance to check the URL
    
    # Mocking Client/API class structure is a bit complex in plane-sdk
    # Let's mock a WorkItems instance
    
    wi = WorkItems(client=MagicMock())
    wi._post = MagicMock(return_value={
        "id": "123", 
        "name": "Test Issue", 
        "project": "proj-1",
        "workspace": "work-1",
        "created_by": "user-1"
    })
    
    data = CreateWorkItem(name="Test Issue", project_id="proj-1")
    
    # Call the method
    # workspace_slug='slug', project_id='pid', data=data
    # Note: legacy_create signature: (self, workspace_slug: str, project_id: str, data: CreateWorkItem)
    
    wi.create(workspace_slug="my-workspace", project_id="my-project", data=data)
    
    # Check the call args of _post
    wi._post.assert_called_once()
    args, _ = wi._post.call_args
    url = args[0]
    
    assert "/issues" in url
    assert "/work-items" not in url
    assert url == "my-workspace/projects/my-project/issues"

def test_legacy_list_patch():
    """
    Test that WorkItems.list uses the /issues endpoint.
    """
    wi = WorkItems(client=MagicMock())
    wi._get = MagicMock(return_value={
        "results": [],
        "total_count": 0
    })
    
    wi.list(workspace_slug="my-workspace", project_id="my-project")
    
    wi._get.assert_called_once()
    args, _ = wi._get.call_args
    url = args[0]
    
    assert "/issues" in url
    assert "/work-items" not in url
    assert url == "my-workspace/projects/my-project/issues"
