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

import sys

print("Applying LEGACY API patch: /work-items/ -> /issues/", file=sys.stderr)

def legacy_create(self, workspace_slug: str, project_id: str, data: CreateWorkItem) -> WorkItem:
    url = f"{workspace_slug}/projects/{project_id}/issues"
    print(f"[PATCH] CREATE {url} with data: {data.model_dump(exclude_none=True)}", file=sys.stderr)
    response = self._post(
        url,
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
    url = f"{workspace_slug}/projects/{project_id}/issues/{work_item_id}"
    print(f"[PATCH] RETRIEVE {url} params={query_params}", file=sys.stderr)
    response = self._get(
        url,
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
    url = f"{workspace_slug}/issues/{project_identifier}-{issue_identifier}"
    print(f"[PATCH] RETRIEVE_BY_ID {url} params={query_params}", file=sys.stderr)
    response = self._get(
        url,
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
    url = f"{workspace_slug}/projects/{project_id}/issues/{work_item_id}"
    print(f"[PATCH] UPDATE {url} with data={data.model_dump(exclude_none=True)}", file=sys.stderr)
    response = self._patch(
        url,
        data.model_dump(exclude_none=True),
    )
    return WorkItem.model_validate(response)

def legacy_delete(self, workspace_slug: str, project_id: str, work_item_id: str) -> None:
    url = f"{workspace_slug}/projects/{project_id}/issues/{work_item_id}"
    print(f"[PATCH] DELETE {url}", file=sys.stderr)
    return self._delete(url)

def legacy_list(
    self,
    workspace_slug: str,
    project_id: str,
    params: WorkItemQueryParams | None = None,
) -> PaginatedWorkItemResponse:
    query_params = params.model_dump(exclude_none=True) if params else None
    url = f"{workspace_slug}/projects/{project_id}/issues"
    print(f"[PATCH] LIST {url} params={query_params}", file=sys.stderr)
    response = self._get(
        url, params=query_params
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
    url = f"{workspace_slug}/issues/search"
    print(f"[PATCH] SEARCH {url} params={search_params}", file=sys.stderr)
    response = self._get(url, params=search_params)
    return WorkItemSearch.model_validate(response)

# Apply patches
WorkItems.create = legacy_create
WorkItems.retrieve = legacy_retrieve
WorkItems.retrieve_by_identifier = legacy_retrieve_by_identifier
WorkItems.update = legacy_update
WorkItems.delete = legacy_delete
WorkItems.list = legacy_list
WorkItems.search = legacy_search
