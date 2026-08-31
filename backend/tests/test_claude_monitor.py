import json
from pathlib import Path

from app.services.claude_monitor import ClaudeCodeMonitor


def write_event(path: Path, timestamp: str, content_type: str) -> None:
    event = {
        "timestamp": timestamp,
        "message": {"content": [{"type": content_type}]},
    }
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")


def test_snapshot_reads_main_and_subagent_without_transcript_content(tmp_path):
    project = tmp_path / "p"
    project.mkdir()
    projects_root = tmp_path.parent / "claude-projects"
    monitor = ClaudeCodeMonitor(project, projects_root, active_window_seconds=30)
    project_dir = projects_root / monitor._project_directory_name()
    project_dir.mkdir(parents=True)

    main = project_dir / "session-1.jsonl"
    write_event(main, "2026-08-31T17:00:00Z", "tool_use")
    subagents = project_dir / "session-1" / "subagents"
    subagents.mkdir(parents=True)
    subagent = subagents / "agent-abc123.jsonl"
    write_event(subagent, "2026-08-31T17:00:10Z", "tool_use")

    snapshot = monitor.snapshot()

    assert snapshot.available is True
    assert snapshot.session_id == "session-1"
    assert [(agent.id, agent.kind, agent.tool_calls) for agent in snapshot.agents] == [
        ("main", "main", 1),
        ("abc123", "subagent", 1),
    ]


def test_stopped_subagent_is_not_reported_as_working(tmp_path):
    project = tmp_path / "p"
    project.mkdir()
    projects_root = tmp_path.parent / "claude-projects"
    monitor = ClaudeCodeMonitor(project, projects_root)
    project_dir = projects_root / monitor._project_directory_name()
    project_dir.mkdir(parents=True)
    main = project_dir / "session-1.jsonl"
    write_event(main, "2026-08-31T17:00:00Z", "text")
    subagents = project_dir / "session-1" / "subagents"
    subagents.mkdir(parents=True)
    subagent = subagents / "agent-abc123.jsonl"
    write_event(subagent, "2026-08-31T17:00:10Z", "tool_use")
    subagent.with_suffix(".meta.json").write_text(
        json.dumps({"stoppedByUser": True}), encoding="utf-8"
    )

    snapshot = monitor.snapshot()

    assert snapshot.agents[1].status == "stopped"
    assert snapshot.agents[1].stopped_by_user is True


def test_monitor_endpoint_is_registered(client):
    response = client.get("/api/v1/agent-monitor/claude-code")

    assert response.status_code == 200
    assert {"available", "session_id", "updated_at", "agents"} <= response.json().keys()
