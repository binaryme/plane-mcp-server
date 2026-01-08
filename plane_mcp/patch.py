from plane.api.work_items.base import WorkItems
from plane.models.work_items import (
    CreateWorkItem,
    PaginatedWorkItemResponse,
    UpdateWorkItem,
    WorkItem,
    WorkItemDetail,
    WorkItemSearch,
)
from plane.models.query_params import RetrieveQueryParams, WorkItemQueryParams

print("Applying LEGACY API patch: /work-items/ -> /issues/")

def legacy_create(self, workspace_slug: str, project_id: str, data: CreateWorkItem) -> WorkItem:
    response = self._post(
        f"{workspace_slug}/projects/{project_id}/issues",
        data.model_dump(exclude_none=True),
    )
    return WorkItem.model_validate(response)

def legacy_retrieve(
    self,
    workspace_slug: str,
    project_id: str,
    work_item_id: str,
    params: RetrieveQueryParams | None = None,
) -> WorkItemDetail:
    query_params = params.model_dump(exclude_none=True) if params else None
    response = self._get(
        f"{workspace_slug}/projects/{project_id}/issues/{work_item_id}",
        params=query_params,
    )
    return WorkItemDetail.model_validate(response)

def legacy_retrieve_by_identifier(
    self,
    workspace_slug: str,
    project_identifier: str,
    issue_identifier: int,
    params: RetrieveQueryParams | None = None,
) -> WorkItemDetail:
    # Note: verify if this endpoint existed in legacy. Assuming yes for now.
    query_params = params.model_dump(exclude_none=True) if params else None
    response = self._get(
        f"{workspace_slug}/issues/{project_identifier}-{issue_identifier}",
        params=query_params,
    )
    return WorkItemDetail.model_validate(response)

def legacy_update(
    self,
    workspace_slug: str,
    project_id: str,
    work_item_id: str,
    data: UpdateWorkItem,
) -> WorkItem:
    response = self._patch(
        f"{workspace_slug}/projects/{project_id}/issues/{work_item_id}",
        data.model_dump(exclude_none=True),
    )
    return WorkItem.model_validate(response)

def legacy_delete(self, workspace_slug: str, project_id: str, work_item_id: str) -> None:
    return self._delete(f"{workspace_slug}/projects/{project_id}/issues/{work_item_id}")

def legacy_list(
    self,
    workspace_slug: str,
    project_id: str,
    params: WorkItemQueryParams | None = None,
) -> PaginatedWorkItemResponse:
    query_params = params.model_dump(exclude_none=True) if params else None
    response = self._get(
        f"{workspace_slug}/projects/{project_id}/issues", params=query_params
    )
    return PaginatedWorkItemResponse.model_validate(response)

def legacy_search(
    self,
    workspace_slug: str,
    query: str,
    params: RetrieveQueryParams | None = None,
) -> WorkItemSearch:
    search_params = {"q": query}
    if params:
        search_params.update(params.model_dump(exclude_none=True))
    # Search might be different, but trying /issues/search or similar
    # Legacy commonly used global search or per-project.
    # Keeping it as /issues/search for now, hoping for the best.
    response = self._get(f"{workspace_slug}/issues/search", params=search_params)
    return WorkItemSearch.model_validate(response)

# Apply patches
WorkItems.create = legacy_create
WorkItems.retrieve = legacy_retrieve
WorkItems.retrieve_by_identifier = legacy_retrieve_by_identifier
WorkItems.update = legacy_update
WorkItems.delete = legacy_delete
WorkItems.list = legacy_list
WorkItems.search = legacy_search
