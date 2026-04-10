from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


ALLOWED_KINDS = {
    "identity_fact",
    "project_fact",
    "project_decision",
    "lesson",
    "active_task",
    "investigation",
}

ALLOWED_SCOPES = {
    "global",
    "project",
    "task",
}

ALLOWED_STATUSES = {
    "draft",
    "active",
    "superseded",
    "archived",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class MemoryObject:
    id: str
    kind: str
    scope: str
    content: str
    project: str = ""
    task_id: str = ""
    topic: str = ""
    tags: list[str] = field(default_factory=list)
    priority: str = "medium"
    status: str = "active"
    confidence: str = "confirmed"
    updated_at: str = field(default_factory=now_iso)
    source: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryObject":
        return cls(
            id=str(data.get("id", "")).strip(),
            kind=str(data.get("kind", "")).strip(),
            scope=str(data.get("scope", "")).strip(),
            content=str(data.get("content", "")).strip(),
            project=str(data.get("project", "")).strip(),
            task_id=str(data.get("task_id", "")).strip(),
            topic=str(data.get("topic", "")).strip(),
            tags=[str(item).strip() for item in data.get("tags", []) if str(item).strip()],
            priority=str(data.get("priority", "medium")).strip() or "medium",
            status=str(data.get("status", "active")).strip() or "active",
            confidence=str(data.get("confidence", "confirmed")).strip() or "confirmed",
            updated_at=str(data.get("updated_at", "")).strip() or now_iso(),
            source=[str(item).strip() for item in data.get("source", []) if str(item).strip()],
            metadata=dict(data.get("metadata", {})),
        )

    def validate(self) -> None:
        if not self.id:
            raise ValueError("memory object id is required")
        if self.kind not in ALLOWED_KINDS:
            raise ValueError(f"unsupported memory kind: {self.kind}")
        if self.scope not in ALLOWED_SCOPES:
            raise ValueError(f"unsupported memory scope: {self.scope}")
        if not self.content:
            raise ValueError("memory object content is required")
        if self.scope in {"project", "task"} and not self.project:
            raise ValueError("project is required for project/task-scoped memory")
        if self.scope == "task" and not self.task_id:
            raise ValueError("task_id is required for task-scoped memory")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"unsupported memory status: {self.status}")

    def validate_candidate(self) -> None:
        self.validate()
        if self.kind == "active_task":
            raise ValueError("active_task should use committed writes, not candidate promotion")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "scope": self.scope,
            "project": self.project,
            "task_id": self.task_id,
            "topic": self.topic,
            "tags": self.tags,
            "priority": self.priority,
            "status": self.status,
            "confidence": self.confidence,
            "updated_at": self.updated_at,
            "content": self.content,
            "source": self.source,
            "metadata": self.metadata,
        }
