#!/usr/bin/env python3
"""Repository inventory helpers for the audit workflow."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


GENERATED_REPORT_NAME = "repo_audit_report.md"
REPORT_SECTIONS = (
    "License",
    "Contribution",
    "CI/CD",
    "Skill Metadata",
    "Script Placement",
    "Orchestrator Patterns",
)
SCRIPT_PLACEMENT_EXCLUDED_PREFIXES = ("tests/", "templates/", "hooks/")
CANONICAL_ROOT_ENTRYPOINTS = {"laufgitter.py"}


def _row(
    section: str,
    item: str,
    status: str,
    evidence: str,
    remediation: str,
) -> dict[str, str]:
    return {
        "section": section,
        "item": item,
        "status": status,
        "evidence": evidence,
        "remediation": remediation,
    }



def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")



def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")



def _display_remediation(row: dict[str, str]) -> str:
    if row.get("status") == "PASS":
        return "None."
    return f"Actionable remediation: {row['remediation']}"



def _row_by_item(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["item"]: row for row in rows}



def _git_tracked_paths(repo_root: Path) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return [line for line in result.stdout.splitlines() if line]



def _inventory_from_paths(paths: list[str], governance: dict[str, bool]) -> dict[str, object]:
    return {
        "governance": governance,
        "paths": [
            {"path": path, "kind": classify_repo_path(path)}
            for path in sorted(dict.fromkeys(paths))
        ],
    }



def _select_distribution_paths(repo_root: Path, inventory: dict[str, object]) -> list[str]:
    tracked_paths = _git_tracked_paths(repo_root)
    all_paths = [
        entry["path"]
        for entry in inventory.get("paths", [])
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    ]
    if tracked_paths is None:
        return [path for path in all_paths if path != GENERATED_REPORT_NAME]
    available = set(all_paths)
    return [
        path for path in tracked_paths if path in available and path != GENERATED_REPORT_NAME
    ]



def _exclude_prefixes(paths: list[str], prefixes: tuple[str, ...]) -> list[str]:
    return [path for path in paths if not path.startswith(prefixes)]



def _orchestrator_patterns(inventory: dict[str, object]) -> list[dict[str, str]]:
    path_entries = inventory.get("paths", [])
    paths = [entry["path"] for entry in path_entries if isinstance(entry, dict)]

    has_entrypoint = "laufgitter.py" in paths
    has_engines = any(path.startswith("engines/") for path in paths)
    has_hooks = any(path.startswith("hooks/") for path in paths)
    has_templates = any(path.startswith("templates/") for path in paths)

    return [
        _row(
            "Orchestrator Patterns",
            "Primary orchestrator entrypoint present",
            "PASS" if has_entrypoint else "FAIL",
            "laufgitter.py present at repository root."
            if has_entrypoint
            else "laufgitter.py missing from repository root.",
            "Restore the primary orchestrator entrypoint at repository root so operators have a stable launch surface.",
        ),
        _row(
            "Orchestrator Patterns",
            "Worker engines are directory-scoped",
            "PASS" if has_engines else "FAIL",
            "Found version-controlled engine assets under engines/."
            if has_engines
            else "No version-controlled engine assets found under engines/.",
            "Move engine wrappers and provider adapters under engines/ so orchestration lanes stay discoverable.",
        ),
        _row(
            "Orchestrator Patterns",
            "Lifecycle hooks are directory-scoped",
            "PASS" if has_hooks else "FAIL",
            "Found version-controlled hook assets under hooks/."
            if has_hooks
            else "No version-controlled hook assets found under hooks/.",
            "Keep hook logic under hooks/ so operator extensions are auditable and discoverable.",
        ),
        _row(
            "Orchestrator Patterns",
            "Orchestrator templates are version-controlled",
            "PASS" if has_templates else "FAIL",
            "Found reusable swarm or workflow templates under templates/."
            if has_templates
            else "No reusable swarm or workflow templates found under templates/.",
            "Version reusable manifests and workflow templates under templates/ to distribute orchestrator patterns consistently.",
        ),
    ]



def classify_repo_path(relative_path: str) -> str:
    if relative_path.startswith(".claude/skills/") and relative_path.endswith("/SKILL.md"):
        return "agent-skill"
    if relative_path.startswith("scripts/") or relative_path.startswith("engines/"):
        return "script"
    if "/" not in relative_path:
        return "repo-root-misc"
    return "other"



def find_governance_files(repo_root: Path) -> dict[str, bool]:
    return {
        "license": (repo_root / "LICENSE.md").is_file(),
        "contributing": (repo_root / "CONTRIBUTING.md").is_file(),
        "security": (repo_root / "SECURITY.md").is_file(),
    }



def collect_repo_inventory(repo_root: Path) -> dict[str, object]:
    paths: list[dict[str, str]] = []
    for path in sorted(p for p in repo_root.rglob("*") if p.is_file()):
        relative = path.relative_to(repo_root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        paths.append({"path": relative, "kind": classify_repo_path(relative)})
    return {
        "governance": find_governance_files(repo_root),
        "paths": paths,
    }



def evaluate_ci_cd(
    pyproject_text: str,
    tests_workflow_text: str,
    release_workflow_text: str,
) -> list[dict[str, str]]:
    floor_match = re.search(r'requires-python\s*=\s*"([^"]+)"', pyproject_text)
    tested_versions = set(
        re.findall(r'python-version:\s*"([^"]+)"', tests_workflow_text)
    )
    floor = floor_match.group(1) if floor_match else "unknown"
    floor_version = floor.replace(">=", "").strip()

    return [
        _row(
            "CI/CD",
            "Python floor matches executed CI",
            "PASS" if floor_version in tested_versions else "FAIL",
            f"requires-python={floor}; tested={sorted(tested_versions)}",
            "Align pyproject.toml and workflow Python versions so CI exercises the supported floor.",
        ),
        _row(
            "CI/CD",
            "Release workflow exists",
            "PASS"
            if "tauri-action" in release_workflow_text
            or "tauri-apps/tauri-action" in release_workflow_text
            else "FAIL",
            "Checked release workflow for a publish job using tauri-action.",
            "Add or repair the release workflow so tagged builds publish artifacts.",
        ),
    ]



def evaluate_skill_metadata(inventory: dict[str, object]) -> list[dict[str, str]]:
    path_entries = inventory.get("paths", [])
    paths = [entry["path"] for entry in path_entries if isinstance(entry, dict)]
    canonical_skills = [
        path
        for path in paths
        if path.startswith(".claude/skills/") and path.endswith("/SKILL.md")
    ]
    stray_skills = [
        path
        for path in paths
        if path.endswith("/SKILL.md") and not path.startswith(".claude/skills/")
    ]

    return [
        _row(
            "Skill Metadata",
            "Canonical skill path",
            "PASS" if canonical_skills and not stray_skills else "FAIL",
            f"canonical={canonical_skills}; stray={stray_skills}",
            "Keep project skills under .claude/skills/<name>/SKILL.md and remove duplicate skill roots.",
        )
    ]



def evaluate_script_placement(inventory: dict[str, object]) -> list[dict[str, str]]:
    path_entries = inventory.get("paths", [])
    paths = [entry["path"] for entry in path_entries if isinstance(entry, dict)]

    allowed_root_files = {"README.md", "CONTRIBUTING.md", "LICENSE.md", "AGENTS.md"}
    repo_root_operational_scripts = [
        path
        for path in paths
        if "/" not in path
        and path not in allowed_root_files
        and path not in CANONICAL_ROOT_ENTRYPOINTS
        and Path(path).suffix in {".py", ".sh", ".bash", ".zsh", ".js", ".ts"}
    ]
    repo_root_operational_clutter = [
        path
        for path in paths
        if "/" not in path
        and path not in allowed_root_files
        and path.endswith(".md")
    ]

    canonical_tooling_roots = {"scripts", "engines"}
    tooling_suffixes = {".py", ".sh", ".bash", ".zsh", ".js", ".ts"}
    operational_keywords = (
        "hook",
        "orchestr",
        "engine",
        "worker",
        "runner",
        "release",
        "deploy",
        "phase",
        "swarm",
        "lint",
        "audit",
    )
    noncanonical_tooling = []
    for path in paths:
        path_obj = Path(path)
        if len(path_obj.parts) < 2:
            continue
        if path_obj.parts[0] in canonical_tooling_roots:
            continue
        if path_obj.suffix not in tooling_suffixes:
            continue
        lowered = path.lower()
        if any(keyword in lowered for keyword in operational_keywords):
            noncanonical_tooling.append(path)

    return [
        _row(
            "Script Placement",
            "Repo-root operational clutter",
            "PASS" if not repo_root_operational_clutter else "FAIL",
            ", ".join(repo_root_operational_clutter)
            or "No unexpected operational markdown notes found at repository root.",
            "Move ad hoc operational notes into docs/ or another scoped directory.",
        ),
        _row(
            "Script Placement",
            "Repo-root operational scripts",
            "PASS" if not repo_root_operational_scripts else "FAIL",
            ", ".join(repo_root_operational_scripts)
            or "No operational scripts found at repository root.",
            "Move operational entrypoints under scripts/ or engines/ so tooling distribution stays predictable.",
        ),
        _row(
            "Script Placement",
            "Noncanonical operational tooling directories",
            "PASS" if not noncanonical_tooling else "FAIL",
            ", ".join(noncanonical_tooling)
            or "Operational tooling is scoped to scripts/ and engines/.",
            "Consolidate operational tooling under scripts/ or engines/ unless there is a documented exception.",
        ),
    ]



def evaluate_oss_compliance(
    inventory: dict[str, object],
    readme_text: str,
    contributing_text: str,
    license_text: str,
) -> list[dict[str, str]]:
    governance = inventory.get("governance", {})
    has_license = bool(governance.get("license")) if isinstance(governance, dict) else False
    has_contributing = (
        bool(governance.get("contributing")) if isinstance(governance, dict) else False
    )
    readme_lower = readme_text.lower()
    contributing_lower = contributing_text.lower()
    license_lower = license_text.lower()

    readme_mentions_contributing = any(
        marker in readme_lower
        for marker in ("contributing", "contributing.md", "how to contribute", "pull request")
    )
    contribution_workflow_markers = (
        "test",
        "tests",
        "development",
        "develop",
        "workflow",
        "setup",
        "install",
        "run",
    )
    has_contribution_workflow = any(
        marker in contributing_lower for marker in contribution_workflow_markers
    )
    license_declares_oss = any(
        marker in license_lower
        for marker in (
            "permission is hereby granted",
            "apache license",
            "mozilla public license",
            "gnu general public license",
            "bsd license",
            "isc license",
            "mit license",
        )
    )

    return [
        _row(
            "OSS Compliance",
            "Top-level governance files present",
            "PASS" if has_license and has_contributing else "FAIL",
            f"license={has_license}; contributing={has_contributing}",
            "Add the missing top-level license or contribution document at repository root.",
        ),
        _row(
            "OSS Compliance",
            "README contribution guidance surfaced",
            "PASS" if readme_mentions_contributing else "FAIL",
            "README checked for contribution or pull-request guidance.",
            "Link contributors from README.md to CONTRIBUTING.md or equivalent onboarding instructions.",
        ),
        _row(
            "OSS Compliance",
            "Contribution guide covers development workflow",
            "PASS" if has_contribution_workflow else "FAIL",
            "CONTRIBUTING.md checked for setup, run, test, or development workflow guidance.",
            "Document the local development and verification workflow in CONTRIBUTING.md.",
        ),
        _row(
            "OSS Compliance",
            "License text declares an OSS grant",
            "PASS" if license_declares_oss else "FAIL",
            "License text scanned for standard open-source grant language.",
            "Replace placeholder license content with a recognized OSS license text.",
        ),
    ]



def build_checklists(repo_root: Path) -> dict[str, list[dict[str, str]]]:
    inventory = collect_repo_inventory(repo_root)
    governance = inventory.get("governance", {})
    distribution_paths = _select_distribution_paths(repo_root, inventory)
    distribution_inventory = _inventory_from_paths(distribution_paths, governance)
    script_inventory = _inventory_from_paths(
        _exclude_prefixes(distribution_paths, SCRIPT_PLACEMENT_EXCLUDED_PREFIXES),
        governance,
    )

    oss_rows = evaluate_oss_compliance(
        distribution_inventory,
        _read_text(repo_root / "README.md"),
        _read_text(repo_root / "CONTRIBUTING.md"),
        _read_text(repo_root / "LICENSE.md"),
    )
    oss_by_item = _row_by_item(oss_rows)
    has_license = bool(governance.get("license")) if isinstance(governance, dict) else False
    has_contributing = (
        bool(governance.get("contributing")) if isinstance(governance, dict) else False
    )

    return {
        "License": [
            _row(
                "License",
                "Top-level license file present",
                "PASS" if has_license else "FAIL",
                "LICENSE.md present at repository root."
                if has_license
                else "LICENSE.md missing from repository root.",
                "Add a top-level LICENSE.md so repository distribution terms are explicit.",
            ),
            oss_by_item["License text declares an OSS grant"],
        ],
        "Contribution": [
            _row(
                "Contribution",
                "Top-level contribution guide present",
                "PASS" if has_contributing else "FAIL",
                "CONTRIBUTING.md present at repository root."
                if has_contributing
                else "CONTRIBUTING.md missing from repository root.",
                "Add a top-level CONTRIBUTING.md so contributor expectations are discoverable.",
            ),
            oss_by_item["README contribution guidance surfaced"],
            oss_by_item["Contribution guide covers development workflow"],
        ],
        "CI/CD": evaluate_ci_cd(
            _read_text(repo_root / "pyproject.toml"),
            _read_text(repo_root / ".github" / "workflows" / "tests.yml"),
            _read_text(repo_root / ".github" / "workflows" / "release.yml"),
        ),
        "Skill Metadata": evaluate_skill_metadata(distribution_inventory),
        "Script Placement": evaluate_script_placement(script_inventory),
        "Orchestrator Patterns": _orchestrator_patterns(distribution_inventory),
    }



def render_report(checklists: dict[str, list[dict[str, str]]]) -> str:
    lines = [
        "# Repository Audit Report",
        "",
        "Generated from live repository evidence by `scripts/repo_audit.py`.",
        "",
    ]
    for section in REPORT_SECTIONS:
        rows = checklists.get(section, [])
        lines.extend(
            [
                f"## {section}",
                "",
                "| Item | Status | Evidence | Remediation |",
                "|---|---|---|---|",
            ]
        )
        for row in rows:
            lines.append(
                "| "
                + " | ".join(
                    (
                        _escape_cell(_display_remediation(row))
                        if column == "remediation"
                        else _escape_cell(row[column])
                    )
                    for column in ("item", "status", "evidence", "remediation")
                )
                + " |"
            )
        if not rows:
            lines.append(
                "| No rows generated | FAIL | Generator produced no evidence. | Add the missing evaluator before shipping the audit. |"
            )
        lines.append("")
    lines.extend(
        [
            "## Remediation Plan",
            "",
            "1. Actionable remediation: fix every FAIL row before treating the repository as compliant, starting with policy drift and misplaced operational files.",
            "2. Actionable remediation: re-run `python3 scripts/repo_audit.py --repo-root . --output repo_audit_report.md` after each remediation batch.",
            "3. Actionable remediation: keep this report committed so later audits diff against evidence instead of memory.",
            "",
        ]
    )
    return "\n".join(lines)



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default=GENERATED_REPORT_NAME)
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    checklists = build_checklists(repo_root)
    Path(args.output).write_text(render_report(checklists), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
