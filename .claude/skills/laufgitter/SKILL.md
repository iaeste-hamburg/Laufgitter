---
name: laufgitter
description: >-
  Orchestrator playbook and routing rules for Laufgitter, the verified-swarm delegation tool (laufgitter.py). TRIGGER — load BEFORE acting, not after —
  whenever: you are about to run ANY script or command that calls a model or drives a conversational/eval harness (probe, smoke test, simulation, grader, persona conversation) outside a live Laufgitter run; you are about to start an edit→test→edit loop or a batch of similar edits across files; you are about to do a "quick check" that spawns a model or a CLI agent; you are reviewing or diagnosing failed worker or model output; you catch yourself thinking a task is "small enough to just do myself" — that thought IS the trigger (a single task is a one-task manifest, and a bounded read-only question is `laufgitter.py ask`); or you are writing or reviewing a manifest, choosing a swarm pattern (review swarm, fix swarm, focus group, bakeoff, research-with-proof), picking a worker engine, or debugging a failed run. SKIP only for: reading or searching files, git operations, a one-file few-line ONE-SHOT edit (once — if you are back for a second pass, that is a loop: TRIGGER), authoring prose/specs/docs straight from your own context, or pure conversation.
---

# Laufgitter orchestrator playbook

## When to Trigger (expanded)
- New triggers: "I just installed laufgitter", "show me a demo", "what can laufgitter do"
- Existing triggers preserved

## Guided Onboarding (NEW SECTION)
### Stage 0 – Verify installation
```bash
./laufgitter.py --help
```
✅ If help text appears → go to Stage 1.
❌ If not found → clone the repo and ensure `laufgitter.py` is executable:
```bash
git clone https://github.com/iaeste-hamburg/Laufgitter && chmod +x laufgitter.py
```

### Stage 1 – Verify config
```bash
ls ~/.config/laufgitter/config.toml
```
✅ Present → go to Stage 2.
❌ Missing → copy sample:
```bash
cp config.sample.toml ~/.config/laufgitter/config.toml
```

### Stage 2 – Run the demo (zero cost)
```bash
./laufgitter.py demo --no-self-update
```
Open the dashboard URL printed to stdout.
✅ Tasks complete → go to Stage 3.

### Stage 3 – Author your first manifest
Use the template below. Save as `my-task.json` in your project root.

### Stage 4 – Standard Loop: Lint → Baseline → Execute
(see Core Instructions section)

### Stage 5 – Review telemetry
```bash
./laufgitter.py models
```
Route future tasks to models with the highest `first_try_pass_rate`.

## Demo Trigger (NEW SECTION)
Fixed phrase: "show me a demo" (or "laufgitter demo")
→ Agent immediately runs:
```bash
./laufgitter.py demo --no-self-update
```
→ Agent narrates:
1. Where the dashboard opened: `http://127.0.0.1:<port>` – open it now.
2. What the 3 toy tasks are doing (writing files, running checks).
3. Where the final HTML report lands: `~/.laufgitter/artifacts/`.
4. "Your next step: author a real manifest with `laufgitter.py lint`."

## Platform Adaptation (NEW SECTION)
- **Antigravity**: use `run_command` / `manage_task` to launch + monitor.
- **Claude Code**: skill already installed via `./laufgitter.py install-agent`.
- **Codex**: engine block already in `config.sample.toml`.

## Verification Plan
### Automated
None needed — SKILL.md is documentation; correctness is verified by reading it.

### Manual
1. In a fresh Antigravity session, type: **"I just installed laufgitter, what do I do?"**
   - Skill should fire (description now covers this).
   - Agent should walk through Stage 0 → 1 → 2 automatically.
2. Type: **"show me a demo"**
   - Agent should immediately run `./laufgitter.py demo --no-self-update` and narrate the output.
3. Type: **"run a swarm"** (existing trigger)
   - Existing Manifest Engineering flow should be unchanged.
---
