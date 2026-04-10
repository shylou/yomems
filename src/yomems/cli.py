from __future__ import annotations

import argparse
import json
from pathlib import Path

from yomems.models import MemoryObject
from yomems.store import MemoryStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yomems")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a memory store")
    init_parser.add_argument("--root", default=".yomems")

    remember_parser = subparsers.add_parser("remember", help="Build a memory entry from flags and suggest/propose/save it")
    remember_parser.add_argument("--root", default=".yomems")
    remember_parser.add_argument("--mode", choices=["suggest", "propose", "save"], default="suggest")
    remember_parser.add_argument("--id", required=True)
    remember_parser.add_argument("--kind", required=True)
    remember_parser.add_argument("--scope", required=True)
    remember_parser.add_argument("--project", default="")
    remember_parser.add_argument("--task-id", default="")
    remember_parser.add_argument("--topic", default="")
    remember_parser.add_argument("--tags", default="")
    remember_parser.add_argument("--priority", default="medium")
    remember_parser.add_argument("--status", default="active")
    remember_parser.add_argument("--confidence", default="confirmed")
    remember_parser.add_argument("--summary", required=True)
    remember_parser.add_argument("--title", default="")
    remember_parser.add_argument("--details", default="")
    remember_parser.add_argument("--context-text", default="")
    remember_parser.add_argument("--decision-text", default="")
    remember_parser.add_argument("--consequences", default="")
    remember_parser.add_argument("--usage", default="")
    remember_parser.add_argument("--problem", default="")
    remember_parser.add_argument("--next-steps", default="")
    remember_parser.add_argument("--findings", default="")
    remember_parser.add_argument("--document", default="")
    remember_parser.add_argument("--source", action="append", default=[])

    propose_parser = subparsers.add_parser("propose", help="Write a candidate memory object from JSON")
    propose_parser.add_argument("--root", default=".yomems")
    propose_parser.add_argument("--input", required=True)

    suggest_parser = subparsers.add_parser("suggest", help="Render a user-facing save suggestion from JSON")
    suggest_parser.add_argument("--input", required=True)
    suggest_parser.add_argument("--lang", choices=["zh", "en"], default="zh")

    prepare_parser = subparsers.add_parser("prepare", help="Check for duplicates and prepare a save suggestion")
    prepare_parser.add_argument("--root", default=".yomems")
    prepare_parser.add_argument("--input", required=True)
    prepare_parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    prepare_parser.add_argument("--limit", type=int, default=5)

    check_parser = subparsers.add_parser("check", help="Check whether similar memory already exists")
    check_parser.add_argument("--root", default=".yomems")
    check_parser.add_argument("--input", required=True)
    check_parser.add_argument("--limit", type=int, default=5)

    save_parser = subparsers.add_parser("save", help="Commit a memory object from JSON")
    save_parser.add_argument("--root", default=".yomems")
    save_parser.add_argument("--input", required=True)

    archive_parser = subparsers.add_parser("archive", help="Archive a committed memory object")
    archive_parser.add_argument("--root", default=".yomems")
    archive_parser.add_argument("--id", required=True)
    archive_parser.add_argument("--project", default="")

    supersede_parser = subparsers.add_parser("supersede", help="Mark a committed memory object as superseded")
    supersede_parser.add_argument("--root", default=".yomems")
    supersede_parser.add_argument("--id", required=True)
    supersede_parser.add_argument("--project", default="")

    refresh_parser = subparsers.add_parser("refresh-index", help="Rebuild derived indexes from markdown files")
    refresh_parser.add_argument("--root", default=".yomems")

    approve_parser = subparsers.add_parser("approve", help="Approve and commit a candidate memory object")
    approve_parser.add_argument("--root", default=".yomems")
    approve_parser.add_argument("--id", required=True)
    approve_parser.add_argument("--project", default="")

    reject_parser = subparsers.add_parser("reject", help="Reject and remove a candidate memory object")
    reject_parser.add_argument("--root", default=".yomems")
    reject_parser.add_argument("--id", required=True)
    reject_parser.add_argument("--project", default="")

    query_parser = subparsers.add_parser("query", help="Query memory objects")
    query_parser.add_argument("--root", default=".yomems")
    query_parser.add_argument("--project", default="")
    query_parser.add_argument("--kind", default="")
    query_parser.add_argument("--tag", default="")
    query_parser.add_argument("--topic", default="")
    query_parser.add_argument("--keyword", default="")
    query_parser.add_argument("--scope", default="")
    query_parser.add_argument("--task-id", default="")
    query_parser.add_argument("--status", default="active")
    query_parser.add_argument("--limit", type=int, default=20)

    context_parser = subparsers.add_parser("context", help="Build a compact context pack")
    context_parser.add_argument("--root", default=".yomems")
    context_parser.add_argument("--project", default="")
    context_parser.add_argument("--intent", required=True)
    context_parser.add_argument("--task-id", default="")

    wake_parser = subparsers.add_parser("wake", help="Return compact context plus keyword-matched memory")
    wake_parser.add_argument("--root", default=".yomems")
    wake_parser.add_argument("--project", default="")
    wake_parser.add_argument("--intent", default="project-onboard")
    wake_parser.add_argument("--task-id", default="")
    wake_parser.add_argument("--keyword", default="")
    wake_parser.add_argument("--kind", default="")
    wake_parser.add_argument("--limit", type=int, default=3)

    candidates_parser = subparsers.add_parser("candidates", help="List proposed memory candidates")
    candidates_parser.add_argument("--root", default=".yomems")
    candidates_parser.add_argument("--project", default="")
    candidates_parser.add_argument("--limit", type=int, default=20)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        store = MemoryStore(Path(args.root))
        store.init_layout()
        print(json.dumps({"status": "ok", "root": str(store.root)}, indent=2))
        return 0

    if args.command == "remember":
        memory = memory_from_args(args)
        if args.mode == "suggest":
            print(render_save_suggestion_zh(memory))
            return 0
        store = MemoryStore(Path(args.root))
        if args.mode == "propose":
            store.propose(memory)
            print(json.dumps({"status": "ok", "mode": "candidate", "id": memory.id}, indent=2))
            return 0
        store.save(memory)
        print(json.dumps({"status": "ok", "mode": "committed", "id": memory.id}, indent=2))
        return 0

    if args.command == "propose":
        store = MemoryStore(Path(args.root))
        payload = json.loads(Path(args.input).read_text())
        memory = MemoryObject.from_dict(payload)
        store.propose(memory)
        print(json.dumps({"status": "ok", "mode": "candidate", "id": memory.id}, indent=2))
        return 0

    if args.command == "suggest":
        payload = json.loads(Path(args.input).read_text())
        memory = MemoryObject.from_dict(payload)
        memory.validate()
        if args.lang == "zh":
            print(render_save_suggestion_zh(memory))
        else:
            print(render_save_suggestion_en(memory))
        return 0

    if args.command == "prepare":
        store = MemoryStore(Path(args.root))
        payload = json.loads(Path(args.input).read_text())
        memory = MemoryObject.from_dict(payload)
        matches = store.find_similar(memory, limit=args.limit)
        if matches:
            print(json.dumps({"status": "duplicate", "matches": matches}, indent=2))
            return 0
        prompt = render_save_suggestion_zh(memory) if args.lang == "zh" else render_save_suggestion_en(memory)
        print(
            json.dumps(
                {
                    "status": "ready",
                    "prompt": prompt,
                    "memory": {
                        "id": memory.id,
                        "kind": memory.kind,
                        "scope": memory.scope,
                        "project": memory.project,
                        "task_id": memory.task_id,
                        "topic": memory.topic,
                        "summary": memory.content,
                    },
                },
                indent=2,
            )
        )
        return 0

    if args.command == "check":
        store = MemoryStore(Path(args.root))
        payload = json.loads(Path(args.input).read_text())
        memory = MemoryObject.from_dict(payload)
        matches = store.find_similar(memory, limit=args.limit)
        print(json.dumps({"status": "ok", "matches": matches}, indent=2))
        return 0

    if args.command == "save":
        store = MemoryStore(Path(args.root))
        payload = json.loads(Path(args.input).read_text())
        memory = MemoryObject.from_dict(payload)
        store.save(memory)
        print(json.dumps({"status": "ok", "mode": "committed", "id": memory.id}, indent=2))
        return 0

    if args.command == "archive":
        store = MemoryStore(Path(args.root))
        memory = store.archive(args.id, project=args.project)
        print(json.dumps({"status": "ok", "archived": memory.id}, indent=2))
        return 0

    if args.command == "supersede":
        store = MemoryStore(Path(args.root))
        memory = store.supersede(args.id, project=args.project)
        print(json.dumps({"status": "ok", "superseded": memory.id}, indent=2))
        return 0

    if args.command == "refresh-index":
        store = MemoryStore(Path(args.root))
        store.refresh_indexes()
        print(json.dumps({"status": "ok", "refreshed": str(store.root)}, indent=2))
        return 0

    if args.command == "approve":
        store = MemoryStore(Path(args.root))
        memory = store.approve(args.id, project=args.project)
        print(json.dumps({"status": "ok", "approved": memory.id}, indent=2))
        return 0

    if args.command == "reject":
        store = MemoryStore(Path(args.root))
        rejected_id = store.reject(args.id, project=args.project)
        print(json.dumps({"status": "ok", "rejected": rejected_id}, indent=2))
        return 0

    if args.command == "query":
        store = MemoryStore(Path(args.root))
        payload = store.query(
            project=args.project,
            kind=args.kind,
            tag=args.tag,
            topic=args.topic,
            keyword=args.keyword,
            scope=args.scope,
            task_id=args.task_id,
            status=args.status,
            limit=args.limit,
        )
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "context":
        store = MemoryStore(Path(args.root))
        payload = store.context(project=args.project, intent=args.intent, task_id=args.task_id)
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "wake":
        store = MemoryStore(Path(args.root))
        match_kind = args.kind
        if not match_kind:
            match_candidates = store.query(
                project=args.project,
                keyword=args.keyword,
                limit=max(args.limit * 3, 10),
            )
            filtered = [item for item in match_candidates if item.get("kind") != "active_task"]
            payload = {
                "context": store.context(project=args.project, intent=args.intent, task_id=args.task_id),
                "matches": filtered[: args.limit],
            }
            print(json.dumps(payload, indent=2))
            return 0
        payload = {
            "context": store.context(project=args.project, intent=args.intent, task_id=args.task_id),
            "matches": store.query(
                project=args.project,
                kind=match_kind,
                keyword=args.keyword,
                task_id=args.task_id if match_kind == "active_task" else "",
                limit=args.limit,
            ),
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "candidates":
        store = MemoryStore(Path(args.root))
        payload = store.query_candidates(project=args.project, limit=args.limit)
        print(json.dumps(payload, indent=2))
        return 0

    parser.error("unsupported command")
    return 2


def render_save_suggestion_zh(memory: MemoryObject) -> str:
    topic = memory.topic or "未指定"
    return (
        "建议保存一条记忆：\n\n"
        f"类型：{memory.kind}\n"
        f"主题：{topic}\n"
        f"摘要：{memory.content}\n\n"
        "是否保存到 .yomems？"
    )


def render_save_suggestion_en(memory: MemoryObject) -> str:
    topic = memory.topic or "unspecified"
    return (
        "Suggested memory to save:\n\n"
        f"Type: {memory.kind}\n"
        f"Topic: {topic}\n"
        f"Summary: {memory.content}\n\n"
        "Save this to .yomems?"
    )


def memory_from_args(args: argparse.Namespace) -> MemoryObject:
    tags = [item.strip() for item in args.tags.split(",") if item.strip()]
    metadata = {
        "title": args.title,
        "details": args.details,
        "context": args.context_text,
        "decision": args.decision_text,
        "consequences": args.consequences,
        "usage": args.usage,
        "problem": args.problem,
        "next_steps": args.next_steps,
        "findings": args.findings,
        "document": args.document,
    }
    return MemoryObject(
        id=args.id,
        kind=args.kind,
        scope=args.scope,
        content=args.summary,
        project=args.project,
        task_id=args.task_id,
        topic=args.topic,
        tags=tags,
        priority=args.priority,
        status=args.status,
        confidence=args.confidence,
        source=args.source,
        metadata={key: value for key, value in metadata.items() if value},
    )
