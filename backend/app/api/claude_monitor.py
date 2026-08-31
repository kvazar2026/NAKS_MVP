"""Local, privacy-preserving Claude Code activity endpoint."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.claude_monitor import ClaudeCodeMonitor

router = APIRouter(prefix="/api/v1/agent-monitor", tags=["agent-monitor"])


class AgentStatusResponse(BaseModel):
    id: str
    kind: str
    status: str
    last_activity_at: datetime | None
    tool_calls: int
    stopped_by_user: bool


class ClaudeMonitorResponse(BaseModel):
    available: bool
    session_id: str | None
    updated_at: datetime
    agents: list[AgentStatusResponse]


def get_monitor() -> ClaudeCodeMonitor:
    return ClaudeCodeMonitor()


@router.get("/claude-code", response_model=ClaudeMonitorResponse)
def get_claude_code_activity(
    monitor: Annotated[ClaudeCodeMonitor, Depends(get_monitor)],
) -> ClaudeMonitorResponse:
    snapshot = monitor.snapshot()
    return ClaudeMonitorResponse(
        available=snapshot.available,
        session_id=snapshot.session_id,
        updated_at=snapshot.updated_at,
        agents=[AgentStatusResponse(**agent.__dict__) for agent in snapshot.agents],
    )
