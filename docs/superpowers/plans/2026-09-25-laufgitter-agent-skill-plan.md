# Laufgitter Agent Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a global agent skill for Laufgitter (`laufgitter-agent`) that enforces the workflow-centric orchestration model (authoring, baselining, dispatching, and managing telemetry) with strict anti-patterns.

**Architecture:** We will initialize a new global skill directory using the `skill-creator` bundled script. We will write a comprehensive `SKILL.md` incorporating the MECE map capabilities (Manifest Engineering, Swarm Orchestration, Fleet Management) and edge-case mitigations. We will validate the final skill format.

**Tech Stack:** Markdown, Python (for validation scripts), Laufgitter architecture

## Global Constraints

- Skill Name: `laufgitter-agent`
- Location: Global (`~/.gemini/config/skills/laufgitter-agent/`)
- Description: Must start with "Use when..." and focus on triggering conditions.
- Document Structure: Must strictly follow the `skill-creator` outline (Frontmatter, Overview, When to Use, Decision Matrix, Runbooks, Examples, Pitfalls, Verification Checklist).
- Token Efficiency: Keep `SKILL.md` concise; delegate heavy operations if needed (though for this skill, it is purely a runbook).

---

### Task 1: Initialize the Skill Scaffold

**Files:**
- Create: `~/.gemini/config/skills/laufgitter-agent/SKILL.md` (via script)

**Interfaces:**
- Consumes: The `skill-creator` initialization script.
- Produces: The scaffolded `laufgitter-agent` skill directory.

- [ ] **Step 1: Run the initialization script**

```bash
uv run python ~/.gemini/config/skills/skill-creator/scripts/init_skill.py laufgitter-agent --global
```
Expected: Script outputs success message and creates `~/.gemini/config/skills/laufgitter-agent/SKILL.md`.

- [ ] **Step 2: Verify the scaffold exists**

```bash
ls -la ~/.gemini/config/skills/laufgitter-agent/
```
Expected: Directory exists and contains `SKILL.md`.

---

### Task 2: Author the SKILL.md Frontmatter and Core Context

**Files:**
- Modify: `~/.gemini/config/skills/laufgitter-agent/SKILL.md`

**Interfaces:**
- Consumes: The scaffolded `SKILL.md`.
- Produces: The upper half of the `SKILL.md` document containing valid YAML frontmatter, Overview, and When to Use sections.

- [ ] **Step 1: Replace the contents of SKILL.md with the frontmatter and context**

```markdown
---
name: laufgitter-agent
description: Use when you need to write a laufgitter manifest, orchestrate parallel agent workers, verify code via deterministic checks, or analyze local model telemetry. Do not use for simple file edits where standard tools suffice.
---

# Laufgitter Agent Workflow

## Overview
This skill enforces the Laufgitter philosophy: Epistemic rigor via deterministic checks, isolated worker execution, and evidence-based model routing. It maps Laufgitter's CLI into a standard operational loop for autonomous agents.

## When to Use & When NOT to Use
- **Trigger when:** The user asks to "run a swarm", "create a manifest", "test models against each other", "check telemetry", or when a complex multi-file feature requires verification before merging.
- **Do NOT trigger when:** The user wants a fast, single-file typo fix that doesn't need external LLM workers.

## Decision / Workflow Matrix
1. **Manifest Engineering:** Write `laufgitter.json` -> Run `lint` -> Run `run --baseline` (must fail) -> Proceed to Execution.
2. **Phase-Driven Integration:** If setting up new tools, use strict phases (0: Probe, 1: Research, 2: Config, 3: Execution).
3. **Telemetry Review:** Run `models` to route tasks based on `first_try_pass_rate`.

```

- [ ] **Step 2: Validate the frontmatter**

```bash
uv run python ~/.gemini/config/skills/skill-creator/scripts/validate_skill.py ~/.gemini/config/skills/laufgitter-agent
```
Expected: Validation passes (YAML is valid, name is lowercase kebab-case, description starts with "Use when").

---

### Task 3: Author the Core Runbooks and Edge Cases

**Files:**
- Modify: `~/.gemini/config/skills/laufgitter-agent/SKILL.md`

**Interfaces:**
- Consumes: The `SKILL.md` created in Task 2.
- Produces: The complete `SKILL.md` with runbooks, anti-patterns, and verification checks.

- [ ] **Step 1: Append the Runbooks, Pitfalls, and Checklist to SKILL.md**

```markdown
## Core Instructions & Runbooks

### 1. Manifest Engineering (The Standard Loop)
1. **Author Manifest**: Create `laufgitter.json` (or `phaseX-*.json`). Define `key`, `spec`, `check` (bash command), `expect_files`. Use `"worktrees": false` if sequentially dependent tasks need shared state, else default to `true`.
2. **Lint**: Execute `./laufgitter.py lint <manifest>`. Fix any warnings (silent probes, write collisions).
3. **Baseline (Crucial)**: Execute `./laufgitter.py run <manifest> --baseline`. The check MUST fail against the unmodified workspace. If it exits 0, the check is hallucinating success. Fix the check.
4. **Execute**: Execute `./laufgitter.py run <manifest>`. Workers spawn. Check Zentrale HUD for live status.
5. **Harvest**: Copy deliverables out of `taskdir` before the worktree is pruned (if applicable).

### 2. Fleet & Telemetry Management
- **Catalog Refresh**: Execute `./laufgitter.py catalog --refresh` to pull new OpenRouter models.
- **Model Scoreboard**: Execute `./laufgitter.py models` to view local performance. Route tasks to models with the highest `first_try_pass_rate` for the specific `task_type`.

## Common Pitfalls & Edge Cases

| Failure Mode | Root Cause | Explicit Mitigation |
| :--- | :--- | :--- |
| **Silent Pass** | Bash `check` fails silently (e.g., `git diff --quiet`) | Check MUST echo reason before exit: `command || { echo "FAIL: reason"; exit 1; }` |
| **Worktree Erasure** | Laufgitter deletes the worktree on PASS. | Explicitly copy output to `artifacts-out/` or use `"worktrees": false` for sequential setups. |
| **Sequential Collision** | Dependent tasks run simultaneously. | Set `"max_parallel": 1` in manifest. |
| **Engine Missing Tokens** | `config.toml` engine `args_template` lacks `{spec}` or `{model}` | Explicitly validate TOML schema before appending to config. |

## Verification Checklist
- [ ] Manifest passes `./laufgitter.py lint` with 0 warnings.
- [ ] Manifest fails cleanly on `./laufgitter.py run --baseline`.
- [ ] Bash `check` emits clear string text on failure to inject context into retry prompts.
- [ ] Deliverables are harvested from temporary worktrees securely.
```

- [ ] **Step 2: Append the code to the file**

```bash
cat << 'EOF' >> ~/.gemini/config/skills/laufgitter-agent/SKILL.md
## Core Instructions & Runbooks

### 1. Manifest Engineering (The Standard Loop)
1. **Author Manifest**: Create `laufgitter.json` (or `phaseX-*.json`). Define `key`, `spec`, `check` (bash command), `expect_files`. Use `"worktrees": false` if sequentially dependent tasks need shared state, else default to `true`.
2. **Lint**: Execute `./laufgitter.py lint <manifest>`. Fix any warnings (silent probes, write collisions).
3. **Baseline (Crucial)**: Execute `./laufgitter.py run <manifest> --baseline`. The check MUST fail against the unmodified workspace. If it exits 0, the check is hallucinating success. Fix the check.
4. **Execute**: Execute `./laufgitter.py run <manifest>`. Workers spawn. Check Zentrale HUD for live status.
5. **Harvest**: Copy deliverables out of `taskdir` before the worktree is pruned (if applicable).

### 2. Fleet & Telemetry Management
- **Catalog Refresh**: Execute `./laufgitter.py catalog --refresh` to pull new OpenRouter models.
- **Model Scoreboard**: Execute `./laufgitter.py models` to view local performance. Route tasks to models with the highest `first_try_pass_rate` for the specific `task_type`.

## Common Pitfalls & Edge Cases

| Failure Mode | Root Cause | Explicit Mitigation |
| :--- | :--- | :--- |
| **Silent Pass** | Bash `check` fails silently (e.g., `git diff --quiet`) | Check MUST echo reason before exit: `command || { echo "FAIL: reason"; exit 1; }` |
| **Worktree Erasure** | Laufgitter deletes the worktree on PASS. | Explicitly copy output to `artifacts-out/` or use `"worktrees": false` for sequential setups. |
| **Sequential Collision** | Dependent tasks run simultaneously. | Set `"max_parallel": 1` in manifest. |
| **Engine Missing Tokens** | `config.toml` engine `args_template` lacks `{spec}` or `{model}` | Explicitly validate TOML schema before appending to config. |

## Verification Checklist
- [ ] Manifest passes `./laufgitter.py lint` with 0 warnings.
- [ ] Manifest fails cleanly on `./laufgitter.py run --baseline`.
- [ ] Bash `check` emits clear string text on failure to inject context into retry prompts.
- [ ] Deliverables are harvested from temporary worktrees securely.
EOF
```

- [ ] **Step 3: Run final validation**

```bash
uv run python ~/.gemini/config/skills/skill-creator/scripts/validate_skill.py ~/.gemini/config/skills/laufgitter-agent
```
Expected: The validation script reports the skill is fully valid and ready for use.
