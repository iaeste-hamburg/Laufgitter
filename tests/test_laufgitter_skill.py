#!/usr/bin/env python3
"""Contract coverage for the Laufgitter Claude Code skill."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".claude" / "skills" / "laufgitter" / "SKILL.md"


class LaufgitterSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_text = SKILL_PATH.read_text(encoding="utf-8")

    def test_skill_has_required_sections(self) -> None:
        for heading in (
            "# Laufgitter operator guide",
            "## What Laufgitter is",
            "## When to trigger",
            "## Pick the right lane",
            "## Guided onboarding",
            "## Choose your Laufgitter operating policy",
            "## Stage 2 – Safe first run: Lint → Baseline → Execute",
            "## What Zentrale is",
            "## Stage 3 – Review results and improve routing",
            "## Maintenance and recovery branches",
            "## Platform adaptation",
            "## Verification Plan",
        ):
            self.assertIn(heading, self.skill_text)

    def test_frontmatter_keeps_trigger_and_skip_categories(self) -> None:
        self.assertRegex(self.skill_text, re.compile(r"^---\nname:\s*laufgitter", re.MULTILINE))
        self.assertIn("TRIGGER — load BEFORE acting", self.skill_text)
        for phrase in (
            "model-calling script or eval harness",
            "edit→test→edit loop",
            "manifest, choosing a swarm pattern",
            "SKIP only for",
            "reading/searching files",
            "pure conversation",
        ):
            self.assertIn(phrase, self.skill_text)

    def test_mode_decision_tree_covers_all_lanes(self) -> None:
        for command in (
            './laufgitter.py ask "Why did the Wednesday release slip?" --source notes/status.md',
            "./laufgitter.py demo --no-self-update",
            "./laufgitter.py run swarm.json --max-parallel 4",
            "./laufgitter.py hud",
        ):
            self.assertIn(command, self.skill_text)

    def test_policy_stage_covers_supported_modes(self) -> None:
        for phrase in (
            "Laufgitter-native swarms only (default)",
            "Claude Code + Laufgitter mixed mode",
            "Antigravity-guided mode",
            "OpenCode local engine mode",
            "If the user does not choose, default to **Laufgitter-native swarms only**.",
        ):
            self.assertIn(phrase, self.skill_text)

    def test_safe_execution_loop_contains_core_commands(self) -> None:
        for command in (
            "./laufgitter.py lint my-task.json",
            "./laufgitter.py run my-task.json --baseline",
            "./laufgitter.py run my-task.json",
        ):
            self.assertIn(command, self.skill_text)
        self.assertIn("baseline proves the check fails against the unmodified workspace", self.skill_text)

    def test_zentrale_section_keeps_local_dashboard_guidance(self) -> None:
        for phrase in (
            "Zentrale is the default local web dashboard, not a hosted service.",
            "./laufgitter.py hud",
            "http://127.0.0.1:8700",
            "the web dashboard is the primary/current path",
        ):
            self.assertIn(phrase, self.skill_text)

    def test_maintenance_and_recovery_cover_key_commands_and_branches(self) -> None:
        for phrase in (
            "./laufgitter.py self-update",
            "./laufgitter.py uninstall-agent",
            "./laufgitter.py models",
            "./laufgitter.py catalog",
            "./laufgitter.py models --explore",
            "If baseline passes unexpectedly",
            "If the dashboard is not visible",
            "If self-update is blocked",
            "If worktree deliverables disappeared",
        ):
            self.assertIn(phrase, self.skill_text)

    def test_platform_adaptation_keeps_supported_positioning(self) -> None:
        for phrase in (
            "if the user has run `./laufgitter.py install-agent`",
            "The hooks nudge; they do not block.",
            "documented integration path",
            "built-in default worker lane",
            "supported local engine lane",
        ):
            self.assertIn(phrase, self.skill_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
