import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_WAKE = REPO_ROOT / "scripts" / "agent-wake.sh"
AGENT_REMEMBER = REPO_ROOT / "scripts" / "agent-remember.sh"


class YOMemsStoreTests(unittest.TestCase):
    def run_cli(self, *args: str) -> str:
        env = {"PYTHONPATH": str(REPO_ROOT / "src")}
        result = subprocess.run(
            ["python3", "-m", "yomems", *args],
            cwd=str(REPO_ROOT),
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout

    def test_init_creates_layout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            payload = json.loads(self.run_cli("init", "--root", str(root)))
            self.assertEqual(payload["status"], "ok")
            self.assertTrue((root / "INDEX.md").exists())
            self.assertTrue((root / "active-context.md").exists())
            self.assertTrue((root / "identity").is_dir())
            self.assertTrue((root / "projects").is_dir())
            self.assertTrue((root / ".index.json").exists())
            self.assertTrue((root / ".candidates.json").exists())
            self.assertTrue((root / "TOPICS.md").exists())

    def test_save_query_and_context_flow(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            identity_input = Path(tmp_dir) / "identity.json"
            identity_input.write_text(
                json.dumps(
                    {
                        "id": "pref_lang_001",
                        "kind": "identity_fact",
                        "scope": "global",
                        "tags": ["language"],
                        "content": "User prefers Chinese responses while code stays in English."
                    }
                )
            )
            self.run_cli("save", "--root", str(root), "--input", str(identity_input))
            self.assertTrue((root / "identity" / "pref-lang-001.md").exists())

            decision_input = Path(tmp_dir) / "decision.json"
            decision_input.write_text(
                json.dumps(
                    {
                        "id": "dec_ctx_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "routing",
                        "tags": ["routing"],
                        "priority": "high",
                        "content": "Context packs should return compact typed records."
                    }
                )
            )
            self.run_cli("save", "--root", str(root), "--input", str(decision_input))
            self.assertTrue((root / "projects" / "yomems" / "decisions" / "dec-ctx-001.md").exists())
            decision_text = (root / "projects" / "yomems" / "decisions" / "dec-ctx-001.md").read_text()
            self.assertIn("## Context", decision_text)
            self.assertIn("## Decision", decision_text)
            self.assertIn("## Consequences", decision_text)

            task_input = Path(tmp_dir) / "task.json"
            task_input.write_text(
                json.dumps(
                    {
                        "id": "task_yomems_001",
                        "kind": "active_task",
                        "scope": "task",
                        "project": "yomems",
                        "task_id": "task_yomems_001",
                        "tags": ["task"],
                        "content": "Implement compact query flow.",
                        "metadata": {
                            "phase": "Phase 1",
                            "next_action": "Add CLI tests"
                        }
                    }
                )
            )
            self.run_cli("save", "--root", str(root), "--input", str(task_input))
            self.assertTrue((root / "projects" / "yomems" / "tasks" / "task-yomems-001.md").exists())
            task_text = (root / "projects" / "yomems" / "tasks" / "task-yomems-001.md").read_text()
            self.assertIn("## Next Steps", task_text)

            query_payload = json.loads(
                self.run_cli(
                    "query",
                    "--root",
                    str(root),
                    "--project",
                    "yomems",
                    "--kind",
                    "project_decision",
                )
            )
            self.assertEqual(len(query_payload), 1)
            self.assertEqual(query_payload[0]["id"], "dec-ctx-001")
            self.assertEqual(query_payload[0]["path"], str(root / "projects" / "yomems" / "decisions" / "dec-ctx-001.md"))

            context_payload = json.loads(
                self.run_cli(
                    "context",
                    "--root",
                    str(root),
                    "--project",
                    "yomems",
                    "--intent",
                    "continue-task",
                    "--task-id",
                    "task_yomems_001",
                )
            )
            self.assertEqual(context_payload["intent"], "continue-task")
            self.assertEqual(len(context_payload["identity"]), 1)
            self.assertEqual(len(context_payload["project"]), 1)
            self.assertEqual(len(context_payload["task"]), 1)
            self.assertEqual(context_payload["task"][0]["id"], "task-yomems-001")
            active_context = (root / "active-context.md").read_text()
            self.assertIn("Implement compact query flow.", active_context)
            index_text = (root / "INDEX.md").read_text()
            self.assertIn("dec-ctx-001", index_text)
            self.assertIn("[yomems]", index_text)
            topics_text = (root / "TOPICS.md").read_text()
            self.assertIn("## routing", topics_text)
            self.assertIn("[yomems]", topics_text)

    def test_keyword_query_prefers_better_matches(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            first = Path(tmp_dir) / "first.json"
            first.write_text(
                json.dumps(
                    {
                        "id": "dec_task_review_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "task-review",
                        "content": "Task Review uses delivery completion as the routing decision.",
                        "metadata": {
                            "title": "Task Review Routing",
                            "details": "The current task should continue when delivery is incomplete."
                        }
                    }
                )
            )
            second = Path(tmp_dir) / "second.json"
            second.write_text(
                json.dumps(
                    {
                        "id": "lesson_review_001",
                        "kind": "lesson",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "content": "Review findings should not automatically trigger optimization.",
                        "metadata": {
                            "details": "The word task appears only in body details."
                        }
                    }
                )
            )

            self.run_cli("save", "--root", str(root), "--input", str(first))
            self.run_cli("save", "--root", str(root), "--input", str(second))

            payload = json.loads(
                self.run_cli(
                    "query",
                    "--root",
                    str(root),
                    "--project",
                    "yomems",
                    "--keyword",
                    "task",
                )
            )
            self.assertEqual(payload[0]["id"], "dec-task-review-001")
            self.assertIn("title", payload[0]["matched_on"])
            self.assertIn("summary", payload[0]["matched_on"])

    def test_index_and_topics_use_stable_priority_ordering(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            low = Path(tmp_dir) / "low.json"
            low.write_text(
                json.dumps(
                    {
                        "id": "dec_low_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "priority": "low",
                        "updated_at": "2026-04-09T00:00:00Z",
                        "content": "Low priority review rule."
                    }
                )
            )
            high = Path(tmp_dir) / "high.json"
            high.write_text(
                json.dumps(
                    {
                        "id": "dec_high_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "priority": "high",
                        "updated_at": "2026-04-09T00:00:01Z",
                        "content": "High priority review rule."
                    }
                )
            )
            task_low = Path(tmp_dir) / "task_low.json"
            task_low.write_text(
                json.dumps(
                    {
                        "id": "task_low_001",
                        "kind": "active_task",
                        "scope": "task",
                        "project": "yomems",
                        "task_id": "task_low_001",
                        "priority": "low",
                        "updated_at": "2026-04-09T00:00:00Z",
                        "content": "Low priority active task."
                    }
                )
            )
            task_high = Path(tmp_dir) / "task_high.json"
            task_high.write_text(
                json.dumps(
                    {
                        "id": "task_high_001",
                        "kind": "active_task",
                        "scope": "task",
                        "project": "yomems",
                        "task_id": "task_high_001",
                        "priority": "high",
                        "updated_at": "2026-04-09T00:00:01Z",
                        "content": "High priority active task."
                    }
                )
            )

            self.run_cli("save", "--root", str(root), "--input", str(low))
            self.run_cli("save", "--root", str(root), "--input", str(high))
            self.run_cli("save", "--root", str(root), "--input", str(task_low))
            self.run_cli("save", "--root", str(root), "--input", str(task_high))

            index_text = (root / "INDEX.md").read_text()
            self.assertLess(index_text.index("dec-high-001"), index_text.index("dec-low-001"))

            topics_text = (root / "TOPICS.md").read_text()
            self.assertLess(topics_text.index("dec-high-001"), topics_text.index("dec-low-001"))

            active_context = (root / "active-context.md").read_text()
            self.assertLess(active_context.index("task-high-001"), active_context.index("task-low-001"))

    def test_workspace_root_keeps_project_memory_in_separate_buckets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            neutron = Path(tmp_dir) / "neutron.json"
            neutron.write_text(
                json.dumps(
                    {
                        "id": "dec_neutron_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "neutron",
                        "topic": "ml2-ovn-driver",
                        "content": "Neutron ML2 OVN driver owns the translation from ML2 lifecycle to OVN."
                    }
                )
            )
            ovn = Path(tmp_dir) / "ovn.json"
            ovn.write_text(
                json.dumps(
                    {
                        "id": "dec_ovn_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "ovn",
                        "topic": "northbound",
                        "content": "OVN northbound schema holds logical intent."
                    }
                )
            )

            self.run_cli("save", "--root", str(root), "--input", str(neutron))
            self.run_cli("save", "--root", str(root), "--input", str(ovn))

            self.assertTrue((root / "projects" / "neutron" / "decisions" / "dec-neutron-001.md").exists())
            self.assertTrue((root / "projects" / "ovn" / "decisions" / "dec-ovn-001.md").exists())

            neutron_query = json.loads(
                self.run_cli("query", "--root", str(root), "--project", "neutron", "--kind", "project_decision")
            )
            ovn_query = json.loads(
                self.run_cli("query", "--root", str(root), "--project", "ovn", "--kind", "project_decision")
            )

            self.assertEqual([item["project"] for item in neutron_query], ["neutron"])
            self.assertEqual([item["project"] for item in ovn_query], ["ovn"])

    def test_investigation_supports_long_form_project_documents(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            payload = json.loads(
                self.run_cli(
                    "remember",
                    "--root",
                    str(root),
                    "--mode",
                    "save",
                    "--id",
                    "neutron_ovn_driver_architecture",
                    "--kind",
                    "investigation",
                    "--scope",
                    "project",
                    "--project",
                    "neutron",
                    "--topic",
                    "ml2-ovn-driver",
                    "--summary",
                    "ML2 OVN driver is layered around mechanism hooks, OVN translation, and convergence loops.",
                    "--title",
                    "Neutron ML2 OVN Driver Architecture",
                    "--findings",
                    "- Mechanism driver owns lifecycle hooks.\n- OVN client translates Neutron state into OVN operations.",
                    "--document",
                    "## 1. Structure\n\nThe driver combines ML2 callbacks, OVN client translation, OVSDB monitors, startup sync, and periodic maintenance.\n\n## 2. Consistency\n\nRevision numbers and repair loops are part of the normal consistency model.\n\n## 3. Judgment\n\nMaintainability is expensive because the subsystem needs cross-module tracing.",
                    "--source",
                    "neutron/plugins/ml2/drivers/ovn/mech_driver/mech_driver.py",
                )
            )
            self.assertEqual(payload["id"], "inv-neutron-ovn-driver-architecture")

            investigation_path = root / "projects" / "neutron" / "investigations" / "inv-neutron-ovn-driver-architecture.md"
            self.assertTrue(investigation_path.exists())
            investigation_text = investigation_path.read_text()
            self.assertIn("## Key Findings", investigation_text)
            self.assertIn("## Document", investigation_text)

            query_payload = json.loads(
                self.run_cli(
                    "query",
                    "--root",
                    str(root),
                    "--project",
                    "neutron",
                    "--kind",
                    "investigation",
                    "--keyword",
                    "cross-module tracing",
                )
            )
            self.assertEqual(query_payload[0]["id"], "inv-neutron-ovn-driver-architecture")
            self.assertIn("document", query_payload[0]["matched_on"])
            self.assertIn("Maintainability is expensive because the subsystem needs cross-module tracing.", query_payload[0]["document"])

            index_text = (root / "INDEX.md").read_text()
            self.assertIn("Investigations", index_text)

            topics_text = (root / "TOPICS.md").read_text()
            self.assertIn("### Investigations", topics_text)

    def test_suggest_renders_user_facing_save_prompt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            candidate = Path(tmp_dir) / "candidate.json"
            candidate.write_text(
                json.dumps(
                    {
                        "id": "dec_task_review_prompt",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "task-review",
                        "content": "Task Review should route based on delivery completion."
                    }
                )
            )

            output = self.run_cli("suggest", "--input", str(candidate))
            self.assertIn("建议保存一条记忆", output)
            self.assertIn("类型：project_decision", output)
            self.assertIn("主题：task-review", output)
            self.assertIn("是否保存到 .yomems？", output)

    def test_check_finds_similar_existing_memory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            existing = Path(tmp_dir) / "existing.json"
            existing.write_text(
                json.dumps(
                    {
                        "id": "dec_dup_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "content": "Review routing should prefer current-task continuation."
                    }
                )
            )
            candidate = Path(tmp_dir) / "candidate.json"
            candidate.write_text(
                json.dumps(
                    {
                        "id": "dec_dup_002",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "content": "Review routing should prefer current-task continuation."
                    }
                )
            )

            self.run_cli("save", "--root", str(root), "--input", str(existing))
            payload = json.loads(self.run_cli("check", "--root", str(root), "--input", str(candidate)))
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["matches"][0]["id"], "dec-dup-001")

    def test_prepare_returns_duplicate_or_ready_status(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            existing = Path(tmp_dir) / "existing.json"
            existing.write_text(
                json.dumps(
                    {
                        "id": "dec_dup_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "content": "Review routing should prefer current-task continuation."
                    }
                )
            )
            duplicate = Path(tmp_dir) / "duplicate.json"
            duplicate.write_text(
                json.dumps(
                    {
                        "id": "dec_dup_002",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "content": "Review routing should prefer current-task continuation."
                    }
                )
            )
            fresh = Path(tmp_dir) / "fresh.json"
            fresh.write_text(
                json.dumps(
                    {
                        "id": "dec_new_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "content": "Standalone review should not update task state."
                    }
                )
            )

            self.run_cli("save", "--root", str(root), "--input", str(existing))

            duplicate_payload = json.loads(
                self.run_cli("prepare", "--root", str(root), "--input", str(duplicate))
            )
            self.assertEqual(duplicate_payload["status"], "duplicate")
            self.assertEqual(duplicate_payload["matches"][0]["id"], "dec-dup-001")

            fresh_payload = json.loads(
                self.run_cli("prepare", "--root", str(root), "--input", str(fresh))
            )
            self.assertEqual(fresh_payload["status"], "ready")
            self.assertIn("是否保存到 .yomems？", fresh_payload["prompt"])
            self.assertEqual(fresh_payload["memory"]["kind"], "project_decision")

    def test_save_normalizes_id_and_topic_slugs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            entry = Path(tmp_dir) / "entry.json"
            entry.write_text(
                json.dumps(
                    {
                        "id": "Review Routing Decision",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "Task Review",
                        "content": "Use current-task continuation as default review routing."
                    }
                )
            )
            payload = json.loads(self.run_cli("save", "--root", str(root), "--input", str(entry)))
            self.assertEqual(payload["id"], "dec-review-routing-decision")
            self.assertTrue((root / "projects" / "yomems" / "decisions" / "dec-review-routing-decision.md").exists())

            query_payload = json.loads(
                self.run_cli("query", "--root", str(root), "--project", "yomems", "--kind", "project_decision")
            )
            self.assertEqual(query_payload[0]["topic"], "task-review")

    def test_remember_can_suggest_and_save_without_json_file_workflow(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            suggest_output = self.run_cli(
                "remember",
                "--id",
                "dec_remember_001",
                "--kind",
                "project_decision",
                "--scope",
                "project",
                "--project",
                "yomems",
                "--topic",
                "routing",
                "--summary",
                "Remember should let the agent avoid temporary JSON files.",
                "--details",
                "The helper should support direct flag-based entry creation.",
            )
            self.assertIn("建议保存一条记忆", suggest_output)
            self.assertIn("类型：project_decision", suggest_output)

            save_payload = json.loads(
                self.run_cli(
                    "remember",
                    "--root",
                    str(root),
                    "--mode",
                    "save",
                    "--id",
                    "dec_remember_001",
                    "--kind",
                    "project_decision",
                    "--scope",
                    "project",
                    "--project",
                    "yomems",
                    "--topic",
                    "routing",
                    "--summary",
                    "Remember should let the agent avoid temporary JSON files.",
                    "--details",
                    "The helper should support direct flag-based entry creation.",
                )
            )
            self.assertEqual(save_payload["mode"], "committed")
            self.assertTrue((root / "projects" / "yomems" / "decisions" / "dec-remember-001.md").exists())

    def test_wake_combines_context_and_matches(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            task_input = Path(tmp_dir) / "task.json"
            task_input.write_text(
                json.dumps(
                    {
                        "id": "task_wake_001",
                        "kind": "active_task",
                        "scope": "task",
                        "project": "yomems",
                        "task_id": "task_wake_001",
                        "content": "Continue review routing work.",
                        "metadata": {
                            "details": "Current work is focused on review routing.",
                            "next_steps": "Refine wake behavior."
                        }
                    }
                )
            )
            decision_input = Path(tmp_dir) / "decision.json"
            decision_input.write_text(
                json.dumps(
                    {
                        "id": "dec_wake_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "review",
                        "content": "Review routing should prefer current-task continuation.",
                        "metadata": {
                            "title": "Review Routing",
                            "details": "Use current-task repair as the default."
                        }
                    }
                )
            )
            self.run_cli("save", "--root", str(root), "--input", str(task_input))
            self.run_cli("save", "--root", str(root), "--input", str(decision_input))

            payload = json.loads(
                self.run_cli(
                    "wake",
                    "--root",
                    str(root),
                    "--project",
                    "yomems",
                    "--intent",
                    "continue-task",
                    "--task-id",
                    "task_wake_001",
                    "--keyword",
                    "review",
                )
            )
            self.assertIn("context", payload)
            self.assertIn("matches", payload)
            self.assertEqual(payload["context"]["task"][0]["id"], "task-wake-001")
            self.assertEqual(payload["matches"][0]["id"], "dec-wake-001")
            self.assertIn("summary", payload["matches"][0]["matched_on"])
            self.assertIn("topic_keyword", payload["matches"][0]["matched_on"])

    def test_agent_helpers_wrap_common_workflow_calls(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            env = os.environ.copy()
            env["YOMEMS_ROOT"] = str(root)
            env["PYTHONPATH"] = str(REPO_ROOT / "src")

            remember = subprocess.run(
                [
                    "bash",
                    str(AGENT_REMEMBER),
                    "save",
                    "project_decision",
                    "dec_agent_helper_001",
                    "yomems",
                    "wake",
                    "Agent helper should wrap remember save.",
                ],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            self.assertIn("\"mode\": \"committed\"", remember.stdout)

            wake = subprocess.run(
                ["bash", str(AGENT_WAKE), "yomems", "project-onboard", "helper"],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            payload = json.loads(wake.stdout)
            self.assertIn("context", payload)
            self.assertIn("matches", payload)

            prepare = subprocess.run(
                [
                    "bash",
                    str(AGENT_REMEMBER),
                    "prepare",
                    "project_decision",
                    "dec_agent_helper_002",
                    "yomems",
                    "wake",
                    "Agent helper should prepare save prompts after duplicate checks.",
                ],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            prepare_payload = json.loads(prepare.stdout)
            self.assertEqual(prepare_payload["status"], "ready")
            self.assertIn("是否保存到 .yomems？", prepare_payload["prompt"])

    def test_task_scope_requires_task_id(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            bad_input = Path(tmp_dir) / "bad.json"
            bad_input.write_text(
                json.dumps(
                    {
                        "id": "bad_task",
                        "kind": "active_task",
                        "scope": "task",
                        "project": "yomems",
                        "content": "Missing task id"
                    }
                )
            )

            result = subprocess.run(
                ["python3", "-m", "yomems", "save", "--root", str(root), "--input", str(bad_input)],
                cwd=str(REPO_ROOT),
                env={"PYTHONPATH": str(REPO_ROOT / "src")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task_id is required", result.stderr)

    def test_propose_and_approve_promotes_candidate_into_committed_memory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            candidate_input = Path(tmp_dir) / "candidate.json"
            candidate_input.write_text(
                json.dumps(
                    {
                        "id": "lesson_scope_001",
                        "kind": "lesson",
                        "scope": "project",
                        "project": "yomems",
                        "topic": "scope",
                        "tags": ["scope", "paths"],
                        "content": "Relative project roots create unstable identity if not normalized."
                    }
                )
            )

            propose_payload = json.loads(
                self.run_cli("propose", "--root", str(root), "--input", str(candidate_input))
            )
            self.assertEqual(propose_payload["mode"], "candidate")
            self.assertTrue((root / "projects" / "yomems" / "candidates" / "lesson-scope-001.md").exists())

            candidates_payload = json.loads(
                self.run_cli("candidates", "--root", str(root), "--project", "yomems")
            )
            self.assertEqual(len(candidates_payload), 1)
            self.assertEqual(candidates_payload[0]["id"], "lesson-scope-001")

            pre_approval_context = json.loads(
                self.run_cli(
                    "context",
                    "--root",
                    str(root),
                    "--project",
                    "yomems",
                    "--intent",
                    "project-onboard",
                )
            )
            self.assertEqual(pre_approval_context["lessons"], [])

            approve_payload = json.loads(
                self.run_cli("approve", "--root", str(root), "--project", "yomems", "--id", "lesson_scope_001")
            )
            self.assertEqual(approve_payload["approved"], "lesson-scope-001")
            self.assertTrue((root / "projects" / "yomems" / "lessons" / "lesson-scope-001.md").exists())
            self.assertFalse((root / "projects" / "yomems" / "candidates" / "lesson-scope-001.md").exists())

            committed_payload = json.loads(
                self.run_cli("query", "--root", str(root), "--project", "yomems", "--kind", "lesson")
            )
            self.assertEqual(len(committed_payload), 1)
            self.assertEqual(committed_payload[0]["id"], "lesson-scope-001")

            candidates_after = json.loads(
                self.run_cli("candidates", "--root", str(root), "--project", "yomems")
            )
            self.assertEqual(candidates_after, [])

    def test_active_task_cannot_be_proposed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            bad_input = Path(tmp_dir) / "active_task_candidate.json"
            bad_input.write_text(
                json.dumps(
                    {
                        "id": "task_candidate_001",
                        "kind": "active_task",
                        "scope": "task",
                        "project": "yomems",
                        "task_id": "task_candidate_001",
                        "content": "Should not be proposed"
                    }
                )
            )

            result = subprocess.run(
                ["python3", "-m", "yomems", "propose", "--root", str(root), "--input", str(bad_input)],
                cwd=str(REPO_ROOT),
                env={"PYTHONPATH": str(REPO_ROOT / "src")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("active_task should use committed writes", result.stderr)

    def test_reject_removes_candidate_without_committing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yomems-store-") as tmp_dir:
            root = Path(tmp_dir) / ".yomems"
            self.run_cli("init", "--root", str(root))

            candidate_input = Path(tmp_dir) / "candidate.json"
            candidate_input.write_text(
                json.dumps(
                    {
                        "id": "dec_candidate_001",
                        "kind": "project_decision",
                        "scope": "project",
                        "project": "yomems",
                        "content": "A candidate decision to reject."
                    }
                )
            )

            self.run_cli("propose", "--root", str(root), "--input", str(candidate_input))
            reject_payload = json.loads(
                self.run_cli("reject", "--root", str(root), "--project", "yomems", "--id", "dec_candidate_001")
            )
            self.assertEqual(reject_payload["rejected"], "dec-candidate-001")
            self.assertFalse((root / "projects" / "yomems" / "candidates" / "dec-candidate-001.md").exists())

            candidates_after = json.loads(
                self.run_cli("candidates", "--root", str(root), "--project", "yomems")
            )
            self.assertEqual(candidates_after, [])

            committed_payload = json.loads(
                self.run_cli("query", "--root", str(root), "--project", "yomems", "--kind", "project_decision")
            )
            self.assertEqual(committed_payload, [])


if __name__ == "__main__":
    unittest.main()
