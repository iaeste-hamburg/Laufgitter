#!/usr/bin/env python3
"""Repository audit report contract tests."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


class RepoAuditReportContractTests(unittest.TestCase):
    def test_report_contains_required_sections_and_status_rows(self) -> None:
        report = Path("repo_audit_report.md").read_text(encoding="utf-8")
        for heading in (
            "## License",
            "## Contribution",
            "## CI/CD",
            "## Skill Metadata",
            "## Script Placement",
            "## Orchestrator Patterns",
            "## Remediation Plan",
        ):
            self.assertIn(heading, report)
        self.assertRegex(report, re.compile(r"\|\s*PASS\s*\|"))
        self.assertNotRegex(report, re.compile(r"\|\s*No rows generated\s*\|"))
        self.assertIn("Actionable remediation", report)


if __name__ == "__main__":
    unittest.main()
