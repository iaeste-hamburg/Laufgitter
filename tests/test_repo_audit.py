#!/usr/bin/env python3
"""Repository audit inventory behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.repo_audit import (
    build_checklists,
    classify_repo_path,
    collect_repo_inventory,
    evaluate_ci_cd,
    evaluate_oss_compliance,
    evaluate_script_placement,
    evaluate_skill_metadata,
    find_governance_files,
    render_report,
)


class RepoAuditInventoryTests(unittest.TestCase):
    def test_classify_repo_path_marks_root_notes_and_skills(self) -> None:
        self.assertEqual(classify_repo_path("AGENTS.md"), "repo-root-misc")
        self.assertEqual(
            classify_repo_path(".claude/skills/laufgitter/SKILL.md"), "agent-skill"
        )
        self.assertEqual(classify_repo_path("scripts/run-phases.sh"), "script")

    def test_find_governance_files_reports_expected_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE.md").write_text("license\n", encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text("contrib\n", encoding="utf-8")
            found = find_governance_files(root)

        self.assertTrue(found["license"])
        self.assertTrue(found["contributing"])
        self.assertFalse(found["security"])

    def test_find_governance_files_ignores_same_named_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE.md").mkdir()
            (root / "CONTRIBUTING.md").mkdir()
            (root / "SECURITY.md").mkdir()

            found = find_governance_files(root)

        self.assertFalse(found["license"])
        self.assertFalse(found["contributing"])
        self.assertFalse(found["security"])

    def test_collect_repo_inventory_returns_sorted_paths_and_governance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").write_text("gitdir: /tmp/worktree\n", encoding="utf-8")
            (root / "LICENSE.md").write_text("license\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "run-phases.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (root / ".claude" / "skills" / "laufgitter").mkdir(parents=True)
            (root / ".claude" / "skills" / "laufgitter" / "SKILL.md").write_text(
                "# Skill\n", encoding="utf-8"
            )
            (root / "nested").mkdir()
            (root / "nested" / "note.txt").write_text("note\n", encoding="utf-8")

            inventory = collect_repo_inventory(root)

        self.assertEqual(
            {"license": True, "contributing": False, "security": False},
            inventory["governance"],
        )
        self.assertEqual(
            [
                {"path": ".claude/skills/laufgitter/SKILL.md", "kind": "agent-skill"},
                {"path": "LICENSE.md", "kind": "repo-root-misc"},
                {"path": "nested/note.txt", "kind": "other"},
                {"path": "scripts/run-phases.sh", "kind": "script"},
            ],
            inventory["paths"],
        )


class RepoAuditRuleTests(unittest.TestCase):
    def test_evaluate_ci_cd_flags_python_floor_drift(self) -> None:
        rows = evaluate_ci_cd(
            'requires-python = ">=3.13"\n',
            'python-version: "3.12"\n',
            'runs-on: ubuntu-latest\n',
        )
        statuses = {row["item"]: row["status"] for row in rows}

        self.assertEqual(statuses["Python floor matches executed CI"], "FAIL")
        self.assertEqual(statuses["Release workflow exists"], "FAIL")

    def test_evaluate_skill_metadata_requires_canonical_skill_path(self) -> None:
        inventory = {
            "paths": [
                {"path": ".claude/skills/laufgitter/SKILL.md", "kind": "agent-skill"},
                {"path": "skills/legacy/SKILL.md", "kind": "repo-root-misc"},
            ]
        }

        rows = evaluate_skill_metadata(inventory)
        statuses = {row["item"]: row["status"] for row in rows}

        self.assertEqual(statuses["Canonical skill path"], "FAIL")

    def test_evaluate_script_placement_allows_canonical_root_entrypoint(self) -> None:
        inventory = {
            "paths": [
                {"path": "laufgitter.py", "kind": "repo-root-misc"},
                {"path": "scripts/run-phases.sh", "kind": "script"},
            ]
        }

        rows = evaluate_script_placement(inventory)
        statuses = {row["item"]: row["status"] for row in rows}

        self.assertEqual(statuses["Repo-root operational scripts"], "PASS")
        self.assertEqual(
            statuses["Noncanonical operational tooling directories"], "PASS"
        )
        self.assertEqual(statuses["Repo-root operational clutter"], "PASS")

    def test_evaluate_script_placement_flags_noncanonical_tooling_directories(self) -> None:
        inventory = {
            "paths": [
                {"path": "tools/release.sh", "kind": "other"},
                {"path": "engines/mock.sh", "kind": "script"},
                {"path": "hooks/preflight.py", "kind": "other"},
            ]
        }

        rows = evaluate_script_placement(inventory)
        statuses = {row["item"]: row["status"] for row in rows}

        self.assertEqual(
            statuses["Noncanonical operational tooling directories"], "FAIL"
        )

    def test_evaluate_script_placement_flags_repo_root_operational_script_stubs(self) -> None:
        inventory = {
            "paths": [
                {"path": "main.py", "kind": "repo-root-misc"},
                {"path": "laufgitter.py", "kind": "repo-root-misc"},
                {"path": "scripts/run-phases.sh", "kind": "script"},
            ]
        }

        rows = evaluate_script_placement(inventory)
        statuses = {row["item"]: row["status"] for row in rows}

        self.assertEqual(statuses["Repo-root operational scripts"], "FAIL")
        self.assertEqual(statuses["Repo-root operational clutter"], "PASS")
        self.assertEqual(
            statuses["Noncanonical operational tooling directories"], "PASS"
        )

    def test_evaluate_script_placement_flags_repo_root_operational_markdown_clutter(self) -> None:
        inventory = {
            "paths": [
                {"path": "laufgitter-live-artifacts-plan.md", "kind": "repo-root-misc"},
                {"path": "README.md", "kind": "repo-root-misc"},
                {"path": "scripts/run-phases.sh", "kind": "script"},
            ]
        }

        rows = evaluate_script_placement(inventory)
        statuses = {row["item"]: row["status"] for row in rows}

        self.assertEqual(statuses["Repo-root operational clutter"], "FAIL")
        self.assertEqual(statuses["Repo-root operational scripts"], "PASS")
        self.assertEqual(
            statuses["Noncanonical operational tooling directories"], "PASS"
        )

    def test_evaluate_oss_compliance_reports_missing_contribution_details_without_security_gate(self) -> None:
        inventory = {
            "governance": {
                "license": True,
                "contributing": True,
                "security": False,
            },
            "paths": [],
        }

        rows = evaluate_oss_compliance(
            inventory,
            "# Laufgitter\nQuickstart only.\n",
            "# Contributing\nPRs welcome.\n",
            "MIT License\n",
        )
        statuses = {row["item"]: row["status"] for row in rows}

        self.assertEqual(statuses["Top-level governance files present"], "PASS")
        self.assertEqual(statuses["README contribution guidance surfaced"], "FAIL")
        self.assertEqual(statuses["Contribution guide covers development workflow"], "FAIL")
        self.assertEqual(statuses["License text declares an OSS grant"], "PASS")


class RepoAuditRenderTests(unittest.TestCase):
    def test_render_report_contains_all_required_sections(self) -> None:
        markdown = render_report(
            {
                "License": [
                    {
                        "item": "Top-level license file present",
                        "status": "PASS",
                        "evidence": "LICENSE.md",
                        "remediation": "None.",
                    }
                ],
                "Contribution": [],
                "CI/CD": [],
                "Skill Metadata": [],
                "Script Placement": [],
                "Orchestrator Patterns": [],
            }
        )
        self.assertIn("# Repository Audit Report", markdown)
        self.assertIn("## License", markdown)
        self.assertIn("## Contribution", markdown)
        self.assertIn("## CI/CD", markdown)
        self.assertIn("## Skill Metadata", markdown)
        self.assertIn("## Script Placement", markdown)
        self.assertIn("## Orchestrator Patterns", markdown)
        self.assertIn("| Item | Status | Evidence | Remediation |", markdown)

    def test_render_report_uses_neutral_remediation_for_pass_rows_only(self) -> None:
        markdown = render_report(
            {
                "License": [
                    {
                        "item": "Top-level license file present",
                        "status": "PASS",
                        "evidence": "LICENSE.md",
                        "remediation": "Add a top-level LICENSE.md so repository distribution terms are explicit.",
                    },
                    {
                        "item": "License text declares an OSS grant",
                        "status": "FAIL",
                        "evidence": "Placeholder license text detected.",
                        "remediation": "Replace placeholder license content with a recognized OSS license text.",
                    },
                ],
                "Contribution": [],
                "CI/CD": [],
                "Skill Metadata": [],
                "Script Placement": [],
                "Orchestrator Patterns": [],
            }
        )

        self.assertIn(
            "| Top-level license file present | PASS | LICENSE.md | None. |",
            markdown,
        )
        self.assertIn(
            "| License text declares an OSS grant | FAIL | Placeholder license text detected. | Actionable remediation: Replace placeholder license content with a recognized OSS license text. |",
            markdown,
        )

    def test_build_checklists_maps_oss_rows_to_license_and_contribution_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "# Repo\nPlease read CONTRIBUTING.md before sending a pull request.\n",
                encoding="utf-8",
            )
            (root / "CONTRIBUTING.md").write_text(
                "# Contributing\nRun tests during local development before you open a pull request.\n",
                encoding="utf-8",
            )
            (root / "LICENSE.md").write_text(
                "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\n",
                encoding="utf-8",
            )
            (root / "pyproject.toml").write_text(
                '[project]\nrequires-python = ">=3.12"\n', encoding="utf-8"
            )
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "tests.yml").write_text(
                'python-version: "3.12"\n', encoding="utf-8"
            )
            (workflows / "release.yml").write_text(
                'uses: tauri-apps/tauri-action@v0\n', encoding="utf-8"
            )
            (root / ".claude" / "skills" / "repo").mkdir(parents=True)
            (root / ".claude" / "skills" / "repo" / "SKILL.md").write_text(
                "# Skill\n", encoding="utf-8"
            )
            (root / "scripts").mkdir()
            (root / "scripts" / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (root / "engines").mkdir()
            (root / "engines" / "mock.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (root / "hooks").mkdir()
            (root / "hooks" / "hook.py").write_text("print('hook')\n", encoding="utf-8")
            (root / "templates").mkdir()
            (root / "templates" / "manifest.json").write_text("{}\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_repo_audit.py").write_text("pass\n", encoding="utf-8")
            (root / "laufgitter.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "plan.md").write_text("# moved note\n", encoding="utf-8")

            checklists = build_checklists(root)

        self.assertEqual(
            ["License", "Contribution", "CI/CD", "Skill Metadata", "Script Placement", "Orchestrator Patterns"],
            list(checklists.keys()),
        )
        self.assertEqual(checklists["License"][0]["item"], "Top-level license file present")
        self.assertEqual(checklists["License"][0]["status"], "PASS")
        self.assertEqual(
            checklists["License"][1]["item"], "License text declares an OSS grant"
        )
        self.assertEqual(
            checklists["Contribution"][0]["item"],
            "Top-level contribution guide present",
        )
        self.assertEqual(checklists["Contribution"][0]["status"], "PASS")
        self.assertEqual(
            checklists["Orchestrator Patterns"][0]["item"],
            "Primary orchestrator entrypoint present",
        )
        self.assertTrue(all(checklists["CI/CD"]))


if __name__ == "__main__":
    unittest.main()
