from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from yomems.models import MemoryObject, now_iso


KIND_TO_DIRECTORY = {
    "identity_fact": "identity",
    "project_fact": "facts",
    "project_decision": "decisions",
    "lesson": "lessons",
    "active_task": "tasks",
    "investigation": "investigations",
}

PRIMARY_DIRECTORIES = (
    "identity",
    "projects",
    "investigations",
    "archive",
)


class MemoryStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    @property
    def package_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def index_path(self) -> Path:
        return self.root / ".index.json"

    @property
    def candidate_index_path(self) -> Path:
        return self.root / ".candidates.json"

    def init_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in PRIMARY_DIRECTORIES:
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self._write_text(
            self.root / "INDEX.md",
            "# YOMems Index\n\nNo committed memory yet.\n",
        )
        self._write_text(
            self.root / "active-context.md",
            "# Active Context\n\nNo active task memory yet.\n",
        )
        self._write_text(
            self.root / "TOPICS.md",
            "# Topics\n\nNo indexed topics yet.\n",
        )
        self._write_json(self.index_path, {"entries": []})
        self._write_json(self.candidate_index_path, {"entries": []})

    def save(self, memory: MemoryObject) -> None:
        memory = self._normalized_memory(memory)
        memory.validate()
        path = self._memory_path(memory)
        self._write_markdown(path, memory)
        self._rebuild_indexes()

    def refresh_indexes(self) -> None:
        self._rebuild_indexes()

    def propose(self, memory: MemoryObject) -> None:
        memory = self._normalized_memory(memory)
        memory.validate_candidate()
        memory.status = "draft"
        path = self._candidate_path(memory)
        self._write_markdown(path, memory)
        self._rebuild_indexes()

    def approve(self, candidate_id: str, project: str = "") -> MemoryObject:
        candidate = self._find_candidate(candidate_id, project)
        if not candidate:
            raise ValueError(f"candidate not found: {candidate_id}")
        memory = MemoryObject.from_dict(candidate)
        memory.status = "active"
        candidate_path = Path(candidate["path"])
        if candidate_path.exists():
            candidate_path.unlink()
        self.save(memory)
        self._rebuild_indexes()
        return memory

    def reject(self, candidate_id: str, project: str = "") -> str:
        candidate = self._find_candidate(candidate_id, project)
        if not candidate:
            raise ValueError(f"candidate not found: {candidate_id}")
        candidate_path = Path(candidate["path"])
        if candidate_path.exists():
            candidate_path.unlink()
        self._rebuild_indexes()
        return str(candidate["id"])

    def archive(self, memory_id: str, project: str = "") -> MemoryObject:
        return self._update_committed_status(memory_id, "archived", project)

    def supersede(self, memory_id: str, project: str = "") -> MemoryObject:
        return self._update_committed_status(memory_id, "superseded", project)

    def query(
        self,
        project: str = "",
        kind: str = "",
        tag: str = "",
        topic: str = "",
        keyword: str = "",
        scope: str = "",
        task_id: str = "",
        status: str = "active",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        entries = self._load_committed_index()
        if project:
            project = self._normalize_project_name(project)
            entries = [
                item for item in entries
                if item.get("project", "") in {"", project}
            ]
        if kind:
            entries = [item for item in entries if item.get("kind") == kind]
        if tag:
            entries = [item for item in entries if tag in item.get("tags", [])]
        if topic:
            topic = self._normalize_topic(topic)
            entries = [item for item in entries if item.get("topic") == topic]
        if keyword:
            keyword_lower = keyword.lower()
            entries = [
                item for item in entries
                if keyword_lower in item.get("content", "").lower()
                or keyword_lower in item.get("details", "").lower()
                or keyword_lower in item.get("findings", "").lower()
                or keyword_lower in item.get("document", "").lower()
                or keyword_lower in item.get("title", "").lower()
                or keyword_lower in item.get("topic", "").lower()
                or any(keyword_lower in tag_value.lower() for tag_value in item.get("tags", []))
            ]
        if scope:
            entries = [item for item in entries if item.get("scope") == scope]
        if task_id:
            entries = [item for item in entries if item.get("task_id") == task_id]
        if status:
            entries = [item for item in entries if item.get("status") == status]
        entries.sort(
            key=lambda item: self._query_sort_key(item, topic=topic, keyword=keyword, task_id=task_id),
            reverse=True,
        )
        return [
            self._with_match_metadata(item, tag=tag, topic=topic, keyword=keyword, task_id=task_id)
            for item in entries[:limit]
        ]

    def query_candidates(self, project: str = "", limit: int = 20) -> list[dict[str, Any]]:
        entries = self._load_candidate_index()
        if project:
            project = self._normalize_project_name(project)
            entries = [
                item for item in entries
                if item.get("project", "") in {"", project}
            ]
        entries.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return entries[:limit]

    def find_similar(
        self,
        memory: MemoryObject,
        include_candidates: bool = True,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        memory = self._normalized_memory(memory)
        entries = self.query(
            project=memory.project,
            kind=memory.kind,
            topic=memory.topic,
            limit=max(limit * 3, 10),
        )
        if include_candidates:
            entries.extend(self.query_candidates(project=memory.project, limit=max(limit * 3, 10)))

        filtered: list[dict[str, Any]] = []
        normalized_summary = self._normalize_text(memory.content)
        normalized_topic = self._normalize_text(memory.topic)
        summary_tokens = self._tokenize(normalized_summary)

        for item in entries:
            if item.get("id") == memory.id:
                continue
            item_topic = self._normalize_text(item.get("topic", ""))
            item_summary = self._normalize_text(item.get("content", ""))
            if normalized_summary and item_summary == normalized_summary:
                filtered.append(item)
                continue
            if normalized_summary and normalized_summary in item_summary:
                filtered.append(item)
                continue
            if item_summary and item_summary in normalized_summary:
                filtered.append(item)
                continue
            if normalized_topic and item_topic == normalized_topic:
                item_tokens = self._tokenize(item_summary)
                if self._looks_like_duplicate_summary(summary_tokens, item_tokens):
                    filtered.append(item)
                    continue
        deduped: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for item in filtered:
            item_id = item.get("id", "")
            if item_id and item_id not in seen_ids:
                deduped.append(item)
                seen_ids.add(item_id)
        return deduped[:limit]

    def context(self, project: str = "", intent: str = "project-onboard", task_id: str = "") -> dict[str, Any]:
        context: dict[str, Any] = {
            "intent": intent,
            "identity": [],
            "project": [],
            "task": [],
            "lessons": [],
        }
        if intent == "preferences":
            context["identity"] = self.query(project=project, kind="identity_fact", scope="global", limit=5)
            return context

        context["identity"] = self.query(project=project, kind="identity_fact", scope="global", limit=3)
        context["project"] = self.query(project=project, kind="project_decision", limit=3)
        context["lessons"] = self.query(project=project, kind="lesson", limit=3)

        if intent == "continue-task":
            context["task"] = self.query(
                project=project,
                kind="active_task",
                task_id=task_id,
                limit=1,
            ) or self.query(project=project, kind="active_task", limit=1)
        elif intent == "review-context":
            context["task"] = self.query(project=project, kind="active_task", task_id=task_id, limit=1)
            context["project"] = self.query(project=project, limit=5)
        elif intent == "project-onboard":
            context["project"] = self.query(project=project, limit=5)

        return context

    def _memory_path(self, memory: MemoryObject) -> Path:
        directory = KIND_TO_DIRECTORY[memory.kind]
        if memory.kind == "identity_fact":
            return self.root / directory / f"{memory.id}.md"
        return self._project_root(memory.project) / directory / f"{memory.id}.md"

    def _candidate_path(self, memory: MemoryObject) -> Path:
        return self._project_root(memory.project) / "candidates" / f"{memory.id}.md"

    def _project_root(self, project: str) -> Path:
        project_name = self._normalize_project_name(project)
        return self.root / "projects" / project_name

    def _normalized_memory(self, memory: MemoryObject) -> MemoryObject:
        memory.id = self._normalize_id(memory.id, memory.kind)
        memory.topic = self._normalize_topic(memory.topic)
        if memory.scope in {"project", "task"}:
            memory.project = self._normalize_project_name(memory.project)
        return memory

    def _title_for(self, memory: MemoryObject) -> str:
        title = str(memory.metadata.get("title", "")).strip()
        if title:
            return title
        return memory.id.replace("-", " ").replace("_", " ").strip().title()

    def _details_for(self, memory: MemoryObject) -> str:
        return str(memory.metadata.get("details", "")).strip()

    def _write_markdown(self, path: Path, memory: MemoryObject) -> None:
        title = self._title_for(memory)
        details = self._details_for(memory)
        template = self._load_template(memory.kind)
        replacements = {
            "id": memory.id,
            "kind": memory.kind,
            "scope": memory.scope,
            "project": memory.project,
            "task_id": memory.task_id,
            "topic": memory.topic,
            "tags": ", ".join(memory.tags),
            "priority": memory.priority,
            "status": memory.status,
            "confidence": memory.confidence,
            "updated_at": memory.updated_at,
            "source": ", ".join(memory.source),
            "title": title,
            "summary": memory.content.strip(),
            "details": details or "Not recorded yet.",
            "context": str(memory.metadata.get("context", "")).strip() or details or "Decision context not recorded yet.",
            "decision": str(memory.metadata.get("decision", "")).strip() or memory.content.strip(),
            "consequences": str(memory.metadata.get("consequences", "")).strip() or "Consequences not recorded yet.",
            "fact": details or memory.content.strip(),
            "usage": str(memory.metadata.get("usage", "")).strip() or "Usage notes not recorded yet.",
            "problem": str(memory.metadata.get("problem", "")).strip() or "Problem pattern not recorded yet.",
            "lesson": details or memory.content.strip(),
            "next_time": str(memory.metadata.get("next_steps", "")).strip() or "Next-step guidance not recorded yet.",
            "next_steps": str(memory.metadata.get("next_steps", "")).strip() or "Next steps not recorded yet.",
            "findings": str(memory.metadata.get("findings", "")).strip() or "Key findings not recorded yet.",
            "document": str(memory.metadata.get("document", "")).strip() or details or "Full document not recorded yet.",
            "sources_block": self._sources_block(memory.source),
        }
        rendered = template
        for key, value in replacements.items():
            rendered = rendered.replace("{" + key + "}", value)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write_text(path, rendered.rstrip() + "\n")

    def _load_template(self, kind: str) -> str:
        template_path = self.package_root / "templates" / f"{kind}.md"
        if template_path.exists():
            return template_path.read_text()
        fallback = self.package_root / "templates" / "identity_fact.md"
        return fallback.read_text()

    def _sources_block(self, source_items: list[str]) -> str:
        if not source_items:
            return "- None recorded"
        return "\n".join(f"- {item}" for item in source_items)

    def _parse_markdown(self, path: Path) -> dict[str, Any]:
        text = path.read_text()
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
        if not match:
            raise ValueError(f"invalid memory markdown: {path}")
        meta_text = match.group(1)
        body = match.group(2)
        metadata: dict[str, str] = {}
        for line in meta_text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

        title_match = re.search(r"^# (.+)$", body, re.MULTILINE)
        summary = self._section_body(body, "Summary")
        details = self._section_body(body, "Details")
        context = self._section_body(body, "Context")
        decision = self._section_body(body, "Decision")
        consequences = self._section_body(body, "Consequences")
        fact = self._section_body(body, "Fact")
        usage = self._section_body(body, "Usage")
        problem = self._section_body(body, "Problem Pattern")
        lesson = self._section_body(body, "Lesson")
        next_steps = self._section_body(body, "Next Steps")
        next_time = self._section_body(body, "Next Time")
        findings = self._section_body(body, "Key Findings")
        document = self._section_body(body, "Document", stop_titles=("Sources",))

        tags = [item.strip() for item in metadata.get("tags", "").split(",") if item.strip()]
        source = [item.strip() for item in metadata.get("source", "").split(",") if item.strip()]
        return {
            "id": metadata.get("id", path.stem),
            "kind": metadata.get("kind", ""),
            "scope": metadata.get("scope", ""),
            "project": metadata.get("project", ""),
            "task_id": metadata.get("task_id", ""),
            "topic": metadata.get("topic", ""),
            "tags": tags,
            "priority": metadata.get("priority", "medium"),
            "status": metadata.get("status", "active"),
            "confidence": metadata.get("confidence", "confirmed"),
            "updated_at": metadata.get("updated_at", ""),
            "content": summary,
            "source": source,
            "title": title_match.group(1).strip() if title_match else path.stem,
            "details": details,
            "context": context,
            "decision": decision,
            "consequences": consequences,
            "fact": fact,
            "usage": usage,
            "problem": problem,
            "lesson": lesson,
            "next_steps": next_steps,
            "next_time": next_time,
            "findings": findings,
            "document": document,
            "path": str(path),
        }

    def _section_body(self, body: str, title: str, stop_titles: tuple[str, ...] = ()) -> str:
        start = re.search(rf"^## {re.escape(title)}\n", body, re.MULTILINE)
        if not start:
            return ""
        content_start = start.end()
        stop_patterns = [rf"^## {re.escape(stop_title)}\n" for stop_title in stop_titles]
        if not stop_patterns:
            stop_patterns = [r"^## [^\n]+\n"]
        next_positions: list[int] = []
        for pattern in stop_patterns:
            for match in re.finditer(pattern, body[content_start:], re.MULTILINE):
                next_positions.append(content_start + match.start())
                break
        content_end = min(next_positions) if next_positions else len(body)
        return body[content_start:content_end].strip()

    def _rebuild_indexes(self) -> None:
        committed = self._scan_markdown(self.root, include_candidates=False)
        candidates = self._scan_markdown(self.root, candidates_only=True)
        self._write_json(self.index_path, {"entries": committed})
        self._write_json(self.candidate_index_path, {"entries": candidates})
        self._rebuild_index_markdown(committed)
        self._rebuild_active_context(committed)
        self._rebuild_topics_markdown(committed)

    def _scan_markdown(
        self,
        root: Path,
        include_candidates: bool = False,
        candidates_only: bool = False,
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        if not root.exists():
            return entries

        if candidates_only:
            legacy_candidates = self.root / "candidates"
            if legacy_candidates.exists():
                for path in sorted(legacy_candidates.glob("*.md")):
                    entries.append(self._parse_markdown(path))
            projects_root = self.root / "projects"
            if projects_root.exists():
                for project_dir in sorted(p for p in projects_root.iterdir() if p.is_dir()):
                    candidate_dir = project_dir / "candidates"
                    if not candidate_dir.exists():
                        continue
                    for path in sorted(candidate_dir.glob("*.md")):
                        entries.append(self._parse_markdown(path))
            return entries

        for directory in ("identity", "facts", "decisions", "lessons", "tasks", "investigations"):
            dir_path = self.root / directory
            if not dir_path.exists():
                continue
            for path in sorted(dir_path.glob("*.md")):
                entries.append(self._parse_markdown(path))

        projects_root = self.root / "projects"
        if projects_root.exists():
            for project_dir in sorted(p for p in projects_root.iterdir() if p.is_dir()):
                for directory in ("facts", "decisions", "lessons", "tasks", "investigations"):
                    dir_path = project_dir / directory
                    if not dir_path.exists():
                        continue
                    for path in sorted(dir_path.glob("*.md")):
                        entries.append(self._parse_markdown(path))

        if include_candidates:
            legacy_candidates = self.root / "candidates"
            if legacy_candidates.exists():
                for path in sorted(legacy_candidates.glob("*.md")):
                    entries.append(self._parse_markdown(path))
            if projects_root.exists():
                for project_dir in sorted(p for p in projects_root.iterdir() if p.is_dir()):
                    candidate_dir = project_dir / "candidates"
                    if not candidate_dir.exists():
                        continue
                    for path in sorted(candidate_dir.glob("*.md")):
                        entries.append(self._parse_markdown(path))
        return entries

    def _rebuild_index_markdown(self, committed: list[dict[str, Any]]) -> None:
        grouped = {
            "Project Decisions": [item for item in committed if item.get("kind") == "project_decision" and item.get("status") == "active"],
            "Project Facts": [item for item in committed if item.get("kind") == "project_fact" and item.get("status") == "active"],
            "Lessons": [item for item in committed if item.get("kind") == "lesson" and item.get("status") == "active"],
            "Investigations": [item for item in committed if item.get("kind") == "investigation" and item.get("status") == "active"],
            "Identity": [item for item in committed if item.get("kind") == "identity_fact" and item.get("status") == "active"],
        }
        lines = ["# YOMems Index", ""]
        if not any(grouped.values()):
            lines.append("No committed memory yet.")
        else:
            for heading, items in grouped.items():
                if not items:
                    continue
                lines.append(f"## {heading}")
                for item in self._sorted_index_items(items)[:20]:
                    topic = item.get("topic", "")
                    project = item.get("project", "")
                    project_part = f" [{project}]" if project else ""
                    topic_part = f" [{topic}]" if topic else ""
                    lines.append(f"- `{item['id']}`{project_part}{topic_part}: {item.get('content', '')}")
                lines.append("")
        self._write_text(self.root / "INDEX.md", "\n".join(lines).rstrip() + "\n")

    def _rebuild_active_context(self, committed: list[dict[str, Any]]) -> None:
        tasks = [item for item in committed if item.get("kind") == "active_task" and item.get("status") == "active"]
        lines = ["# Active Context", ""]
        if not tasks:
            lines.append("No active task memory yet.")
        else:
            for task in self._sorted_index_items(tasks)[:5]:
                lines.append(f"## {task.get('title', task['id'])}")
                lines.append(f"- ID: `{task['id']}`")
                if task.get("project"):
                    lines.append(f"- Project: `{task['project']}`")
                if task.get("task_id"):
                    lines.append(f"- Task ID: `{task['task_id']}`")
                lines.append(f"- Summary: {task.get('content', '')}")
                if task.get("details"):
                    lines.append(f"- Details: {task['details']}")
                lines.append("")
        self._write_text(self.root / "active-context.md", "\n".join(lines).rstrip() + "\n")

    def _rebuild_topics_markdown(self, committed: list[dict[str, Any]]) -> None:
        topic_map: dict[str, list[dict[str, Any]]] = {}
        for item in committed:
            if item.get("status") != "active":
                continue
            topic = item.get("topic", "").strip()
            if not topic:
                continue
            topic_map.setdefault(topic, []).append(item)

        lines = ["# Topics", ""]
        if not topic_map:
            lines.append("No indexed topics yet.")
            self._write_text(self.root / "TOPICS.md", "\n".join(lines).rstrip() + "\n")
            return

        for topic in sorted(topic_map):
            items = topic_map[topic]
            lines.append(f"## {topic}")
            for kind in ("project_decision", "project_fact", "lesson", "investigation", "active_task", "identity_fact"):
                kind_items = self._sorted_index_items([item for item in items if item.get("kind") == kind])
                if not kind_items:
                    continue
                label = {
                    "project_decision": "Decisions",
                    "project_fact": "Facts",
                    "lesson": "Lessons",
                    "investigation": "Investigations",
                    "active_task": "Tasks",
                    "identity_fact": "Identity",
                }[kind]
                lines.append(f"### {label}")
                for item in kind_items[:10]:
                    project = item.get("project", "")
                    project_part = f" [{project}]" if project else ""
                    lines.append(f"- `{item['id']}`{project_part}: {item.get('content', '')}")
                lines.append("")
        self._write_text(self.root / "TOPICS.md", "\n".join(lines).rstrip() + "\n")

    def _load_committed_index(self) -> list[dict[str, Any]]:
        if not self.index_path.exists():
            self._rebuild_indexes()
        return json.loads(self.index_path.read_text()).get("entries", [])

    def _load_candidate_index(self) -> list[dict[str, Any]]:
        if not self.candidate_index_path.exists():
            self._rebuild_indexes()
        return json.loads(self.candidate_index_path.read_text()).get("entries", [])

    def _load_committed_index_fresh(self) -> list[dict[str, Any]]:
        self._rebuild_indexes()
        return self._load_committed_index()

    def _find_candidate(self, candidate_id: str, project: str = "") -> dict[str, Any]:
        entries = self._load_candidate_index()
        if project:
            project = self._normalize_project_name(project)
        for item in entries:
            if project and item.get("project", "") != project:
                continue
            if self._candidate_id_matches(candidate_id, item):
                return item
        return {}

    def _find_committed(self, memory_id: str, project: str = "") -> dict[str, Any]:
        entries = self._load_committed_index_fresh()
        if project:
            project = self._normalize_project_name(project)
        for item in entries:
            if project and item.get("project", "") != project:
                continue
            if self._candidate_id_matches(memory_id, item):
                return item
        return {}

    def _candidate_id_matches(self, candidate_id: str, item: dict[str, Any]) -> bool:
        item_id = item.get("id", "")
        if not item_id:
            return False
        if candidate_id == item_id:
            return True
        item_kind = item.get("kind", "")
        if not item_kind:
            return False
        return self._normalize_id(candidate_id, item_kind) == item_id

    def _update_committed_status(
        self,
        memory_id: str,
        status: str,
        project: str = "",
    ) -> MemoryObject:
        item = self._find_committed(memory_id, project)
        if not item:
            raise ValueError(f"memory not found: {memory_id}")
        memory = self._memory_from_item(item)
        memory.status = status
        memory.updated_at = now_iso()
        path = Path(item["path"])
        self._write_markdown(path, memory)
        self._rebuild_indexes()
        return memory

    def _memory_from_item(self, item: dict[str, Any]) -> MemoryObject:
        metadata = {
            "title": item.get("title", ""),
            "details": item.get("details", ""),
            "context": item.get("context", ""),
            "decision": item.get("decision", ""),
            "consequences": item.get("consequences", ""),
            "usage": item.get("usage", ""),
            "problem": item.get("problem", ""),
            "next_steps": item.get("next_steps", ""),
            "findings": item.get("findings", ""),
            "document": item.get("document", ""),
        }
        return MemoryObject(
            id=str(item.get("id", "")).strip(),
            kind=str(item.get("kind", "")).strip(),
            scope=str(item.get("scope", "")).strip(),
            content=str(item.get("content", "")).strip(),
            project=str(item.get("project", "")).strip(),
            task_id=str(item.get("task_id", "")).strip(),
            topic=str(item.get("topic", "")).strip(),
            tags=[str(tag).strip() for tag in item.get("tags", []) if str(tag).strip()],
            priority=str(item.get("priority", "medium")).strip() or "medium",
            status=str(item.get("status", "active")).strip() or "active",
            confidence=str(item.get("confidence", "confirmed")).strip() or "confirmed",
            updated_at=str(item.get("updated_at", "")).strip() or now_iso(),
            source=[str(source).strip() for source in item.get("source", []) if str(source).strip()],
            metadata={key: value for key, value in metadata.items() if str(value).strip()},
        )

    def _priority_rank(self, value: str) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(value, 0)

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())

    def _tokenize(self, value: str) -> set[str]:
        return {token for token in re.split(r"[^a-z0-9]+", value) if token}

    def _looks_like_duplicate_summary(self, left: set[str], right: set[str]) -> bool:
        if not left or not right:
            return False
        overlap = left & right
        if len(overlap) < 4:
            return False
        baseline = min(len(left), len(right))
        if baseline == 0:
            return False
        return (len(overlap) / baseline) >= 0.8

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
        slug = re.sub(r"-{2,}", "-", slug).strip("-")
        return slug

    def _normalize_project_name(self, value: str) -> str:
        return self._slugify(value)

    def _kind_prefix(self, kind: str) -> str:
        return {
            "identity_fact": "pref",
            "project_fact": "fact",
            "project_decision": "dec",
            "lesson": "lesson",
            "active_task": "task",
            "investigation": "inv",
        }.get(kind, "mem")

    def _normalize_id(self, value: str, kind: str) -> str:
        slug = self._slugify(value)
        prefix = self._kind_prefix(kind)
        if slug.startswith(prefix + "-"):
            return slug
        return f"{prefix}-{slug}" if slug else prefix

    def _normalize_topic(self, value: str) -> str:
        return self._slugify(value)

    def _query_sort_key(
        self,
        item: dict[str, Any],
        topic: str = "",
        keyword: str = "",
        task_id: str = "",
    ) -> tuple[int, int, int, str]:
        topic_bonus = 1 if topic and item.get("topic", "") == topic else 0
        task_bonus = 1 if task_id and item.get("task_id", "") == task_id else 0
        keyword_bonus = 0
        if keyword:
            keyword_lower = keyword.lower()
            if keyword_lower in item.get("title", "").lower():
                keyword_bonus = 3
            elif keyword_lower in item.get("content", "").lower():
                keyword_bonus = 2
            elif keyword_lower in item.get("details", "").lower() or keyword_lower in item.get("findings", "").lower():
                keyword_bonus = 1
            elif keyword_lower in item.get("document", "").lower():
                keyword_bonus = 1
        return (
            topic_bonus + task_bonus,
            keyword_bonus,
            self._priority_rank(item.get("priority", "medium")),
            item.get("updated_at", ""),
        )

    def _with_match_metadata(
        self,
        item: dict[str, Any],
        tag: str = "",
        topic: str = "",
        keyword: str = "",
        task_id: str = "",
    ) -> dict[str, Any]:
        enriched = dict(item)
        matched_on: list[str] = []
        if task_id and item.get("task_id", "") == task_id:
            matched_on.append("task_id")
        if topic and item.get("topic", "") == topic:
            matched_on.append("topic")
        if tag and tag in item.get("tags", []):
            matched_on.append("tag")
        if keyword:
            keyword_lower = keyword.lower()
            if keyword_lower in item.get("title", "").lower():
                matched_on.append("title")
            if keyword_lower in item.get("content", "").lower():
                matched_on.append("summary")
            if keyword_lower in item.get("details", "").lower():
                matched_on.append("details")
            if keyword_lower in item.get("findings", "").lower():
                matched_on.append("findings")
            if keyword_lower in item.get("document", "").lower():
                matched_on.append("document")
            if keyword_lower in item.get("topic", "").lower():
                matched_on.append("topic_keyword")
            if any(keyword_lower in tag_value.lower() for tag_value in item.get("tags", [])):
                matched_on.append("tag_keyword")
        enriched["matched_on"] = matched_on
        return enriched

    def _sorted_index_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            items,
            key=lambda item: (
                self._priority_rank(item.get("priority", "medium")),
                item.get("updated_at", ""),
                item.get("id", ""),
            ),
            reverse=True,
        )

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")

    def _write_text(self, path: Path, payload: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload)
