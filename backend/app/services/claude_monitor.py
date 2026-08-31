"""Read Claude Code's local session metadata without exposing its contents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ACTIVE_WINDOW_SECONDS = 30


@dataclass(frozen=True)
class ClaudeAgent:
    """A safe, content-free view of one Claude Code session."""

    id: str
    kind: str
    status: str
    last_activity_at: datetime | None
    tool_calls: int
    stopped_by_user: bool


@dataclass(frozen=True)
class ClaudeMonitorSnapshot:
    available: bool
    session_id: str | None
    updated_at: datetime
    agents: list[ClaudeAgent]


class ClaudeCodeMonitor:
    """Discover the latest Claude Code session for a local project.

    Claude Code keeps stream-json transcripts under ``~/.claude/projects``.
    This reader intentionally extracts only event types, timestamps and tool
    counts; prompts, replies, tool inputs and results never leave disk.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        projects_root: Path | None = None,
        active_window_seconds: int = ACTIVE_WINDOW_SECONDS,
    ) -> None:
        # This module lives in backend/app/services; the Claude Code project is
        # the repository root, regardless of the directory used to run Uvicorn.
        default_project_root = Path(__file__).resolve().parents[3]
        self.project_root = (project_root or default_project_root).resolve()
        self.projects_root = projects_root or Path.home() / ".claude" / "projects"
        self.active_window_seconds = active_window_seconds

    def snapshot(self) -> ClaudeMonitorSnapshot:
        now = datetime.now(UTC)
        project_dir = self.projects_root / self._project_directory_name()
        if not project_dir.is_dir():
            return ClaudeMonitorSnapshot(False, None, now, [])

        session_files = list(project_dir.glob("*.jsonl"))
        if not session_files:
            return ClaudeMonitorSnapshot(False, None, now, [])

        session_file = max(session_files, key=lambda item: item.stat().st_mtime)
        agents = [self._read_agent(session_file, "main", now)]
        subagents_dir = project_dir / session_file.stem / "subagents"
        for subagent_file in sorted(subagents_dir.glob("*.jsonl")):
            agents.append(self._read_agent(subagent_file, "subagent", now))

        return ClaudeMonitorSnapshot(True, session_file.stem, now, agents)

    def _project_directory_name(self) -> str:
        return str(self.project_root).lower().replace(":", "-").replace("\\", "-").replace("/", "-")

    def _read_agent(self, session_file: Path, kind: str, now: datetime) -> ClaudeAgent:
        latest_event_at: datetime | None = None
        tool_calls = 0
        try:
            with session_file.open("r", encoding="utf-8") as transcript:
                for line in transcript:
                    event = self._parse_event(line)
                    if event is None:
                        continue
                    event_at = self._parse_timestamp(event.get("timestamp"))
                    if event_at and (latest_event_at is None or event_at > latest_event_at):
                        latest_event_at = event_at
                    tool_calls += self._tool_call_count(event)
        except OSError:
            pass

        stopped_by_user = self._was_stopped_by_user(session_file)
        status = "stopped" if stopped_by_user else self._activity_status(latest_event_at, now)
        return ClaudeAgent(
            id="main" if kind == "main" else session_file.stem.removeprefix("agent-"),
            kind=kind,
            status=status,
            last_activity_at=latest_event_at,
            tool_calls=tool_calls,
            stopped_by_user=stopped_by_user,
        )

    @staticmethod
    def _parse_event(line: str) -> dict[str, Any] | None:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return None
        return event if isinstance(event, dict) else None

    @staticmethod
    def _parse_timestamp(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _tool_call_count(event: dict[str, Any]) -> int:
        message = event.get("message")
        if not isinstance(message, dict):
            return 0
        content = message.get("content")
        if not isinstance(content, list):
            return 0
        return sum(1 for item in content if isinstance(item, dict) and item.get("type") == "tool_use")

    @staticmethod
    def _was_stopped_by_user(session_file: Path) -> bool:
        meta_file = session_file.with_suffix(".meta.json")
        if not meta_file.is_file():
            return False
        try:
            metadata = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return bool(metadata.get("stoppedByUser")) if isinstance(metadata, dict) else False

    def _activity_status(self, event_at: datetime | None, now: datetime) -> str:
        if event_at is None:
            return "idle"
        return "working" if (now - event_at).total_seconds() <= self.active_window_seconds else "idle"
