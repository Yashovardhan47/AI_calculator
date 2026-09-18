from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..auth.dependencies import current_user
from ..storage import get_store


router = APIRouter(prefix="/api/v1", tags=["workspace"])


class WorkflowRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1_000)
    workflow_definition: dict[str, Any]


@router.get("/history")
def list_history(
    user: Annotated[dict, Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict:
    return {"items": get_store().list_history(str(user["id"]), limit)}


@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(history_id: str, user: Annotated[dict, Depends(current_user)]) -> None:
    if not get_store().delete_history_item(str(user["id"]), history_id):
        raise HTTPException(status_code=404, detail={"message": "History item not found."})


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(user: Annotated[dict, Depends(current_user)]) -> None:
    get_store().clear_history(str(user["id"]))


@router.get("/workflows")
def list_workflows(user: Annotated[dict, Depends(current_user)]) -> dict:
    return {"items": get_store().list_workflows(str(user["id"]))}


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
def save_workflow(payload: WorkflowRequest, user: Annotated[dict, Depends(current_user)]) -> dict:
    return get_store().save_workflow(
        str(user["id"]),
        payload.name.strip(),
        payload.description.strip() if payload.description else None,
        payload.workflow_definition,
    )


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: str, user: Annotated[dict, Depends(current_user)]) -> None:
    if not get_store().delete_workflow(str(user["id"]), workflow_id):
        raise HTTPException(status_code=404, detail={"message": "Workflow not found."})
