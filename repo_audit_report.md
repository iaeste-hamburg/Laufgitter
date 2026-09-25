# Repository Audit Report

Generated from live repository evidence by `scripts/repo_audit.py`.

## License

| Item | Status | Evidence | Remediation |
|---|---|---|---|
| Top-level license file present | PASS | LICENSE.md present at repository root. | None. |
| License text declares an OSS grant | PASS | License text scanned for standard open-source grant language. | None. |

## Contribution

| Item | Status | Evidence | Remediation |
|---|---|---|---|
| Top-level contribution guide present | PASS | CONTRIBUTING.md present at repository root. | None. |
| README contribution guidance surfaced | PASS | README checked for contribution or pull-request guidance. | None. |
| Contribution guide covers development workflow | PASS | CONTRIBUTING.md checked for setup, run, test, or development workflow guidance. | None. |

## CI/CD

| Item | Status | Evidence | Remediation |
|---|---|---|---|
| Python floor matches executed CI | PASS | requires-python=>=3.12; tested=['3.12'] | None. |
| Release workflow exists | PASS | Checked release workflow for a publish job using tauri-action. | None. |

## Skill Metadata

| Item | Status | Evidence | Remediation |
|---|---|---|---|
| Canonical skill path | PASS | canonical=['.claude/skills/laufgitter/SKILL.md']; stray=[] | None. |

## Script Placement

| Item | Status | Evidence | Remediation |
|---|---|---|---|
| Repo-root operational clutter | PASS | No unexpected operational markdown notes found at repository root. | None. |
| Repo-root operational scripts | PASS | No operational scripts found at repository root. | None. |
| Noncanonical operational tooling directories | PASS | Operational tooling is scoped to scripts/ and engines/. | None. |

## Orchestrator Patterns

| Item | Status | Evidence | Remediation |
|---|---|---|---|
| Primary orchestrator entrypoint present | PASS | laufgitter.py present at repository root. | None. |
| Worker engines are directory-scoped | PASS | Found version-controlled engine assets under engines/. | None. |
| Lifecycle hooks are directory-scoped | PASS | Found version-controlled hook assets under hooks/. | None. |
| Orchestrator templates are version-controlled | PASS | Found reusable swarm or workflow templates under templates/. | None. |

## Remediation Plan

1. Actionable remediation: fix every FAIL row before treating the repository as compliant, starting with policy drift and misplaced operational files.
2. Actionable remediation: re-run `python3 scripts/repo_audit.py --repo-root . --output repo_audit_report.md` after each remediation batch.
3. Actionable remediation: keep this report committed so later audits diff against evidence instead of memory.
