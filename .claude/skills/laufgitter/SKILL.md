---
name: laufgitter
description: >-
  Operator guide and routing rules for Laufgitter, the verified-swarm orchestration tool (`laufgitter.py`). TRIGGER — load BEFORE acting, not after — whenever:
  you are about to run any model-calling script or eval harness outside a live Laufgitter run; you are about to start an edit→test→edit loop or a batch
  of similar edits; you are about to do a quick check that spawns a model or CLI agent; you are writing or reviewing a manifest, choosing a swarm pattern,
  choosing an engine/model lane, or debugging a failed run; or the user asks for a demo, asks what Laufgitter is, asks how to use `ask`, wants the live
  dashboard, wants model-routing guidance, or wants to run a swarm. SKIP only for: reading/searching files, pure git operations, a one-file few-line ONE-SHOT
  edit (once only — if you are back for a second pass, that is a loop: TRIGGER), authoring prose straight from your own context, or pure conversation.
---

# Laufgitter operator guide

## What Laufgitter is
Laufgitter is a verified-swarm orchestrator: it sends work to parallel workers, then decides PASS or FAIL by executing the task's check command against the artifact, not by trusting the worker's summary.

Zentrale is the local mission-control view: a local web dashboard that opens automatically on runs and shows live workers, results, and the artifact library.

Assume the user is already in a working Laufgitter environment. If a chosen command fails because a prerequisite is missing, handle that in the recovery branches instead of front-loading setup gates.

## When to trigger
- The user wants to use Laufgitter, asks what it does, or asks for a demo.
- The user is about to do batch work, parallel work, or anything that needs executed verification.
- The user is about to do a model-calling quick check outside a live Laufgitter run.
- The user needs a manifest, a lane choice, or model-routing guidance.
- You catch yourself thinking the task is small enough to just do inline. That thought is the trigger.

## Pick the right lane
### Use `ask`
Use `ask` when the user wants one bounded read-only answer over known files and does not need executed verification.

```bash
./laufgitter.py ask "Why did the Wednesday release slip?" --source notes/status.md
```

Explain that `ask` is the lightest lane: one question, one clean worker, and no manifest unless the user needs executable proof.

### Use `demo`
Use `demo` when the user wants a proof-of-setup or a quick product tour.

```bash
./laufgitter.py demo --no-self-update
```

Explain that demo is the shortest way to watch the whole system run end to end.

### Use a manifest + swarm
Use the manifest path when the user wants executable work, multiple artifacts, retries, or parallel delegation.

```bash
./laufgitter.py run swarm.json --max-parallel 4
```

Explain that this is the full verified lane: manifest, workers, executed checks, and Zentrale visibility.

### Use `hud`
Use `hud` when the user wants to watch or revisit results.

```bash
./laufgitter.py hud
```

Explain that this opens Zentrale, the local dashboard, on demand.

## Guided onboarding
### Stage 0 – Run the demo
```bash
./laufgitter.py demo --no-self-update
```

After demo, narrate:
1. Where Zentrale opened.
2. What the toy tasks are doing.
3. Where the final report landed.
4. Which lane the user should choose next: `ask`, manifest/swarm, or `hud`.

### Stage 1 – Choose the first real task
Choose the lightest valid path.

For one bounded question:
```bash
./laufgitter.py ask "..." --source path/to/file-or-dir
```

For executable work: start from a template in `templates/`, or write a small manifest with `key`, `spec`, `check`, and `expect_files`.

Explain briefly:
- `check` is the truth source.
- `expect_files` proves deliverables exist.
- `engine`, `model`, `task_type`, `verified`, and `worktrees` matter once the task gets real.

## Choose your Laufgitter operating policy
Before the first real job, ask the user which operating policy they want and repeat it back before continuing.

1. **Laufgitter-native swarms only (default)**
   - Use Laufgitter manifests, `lint`, `run --baseline`, `run`, and Zentrale as the only execution path.
   - This is the cleanest first-class path in the docs.

2. **Claude Code + Laufgitter mixed mode**
   - Use Claude Code for interviewing, planning, and small inline work, but route executable or batch work through Laufgitter.
   - If needed, `./laufgitter.py install-agent` installs the Laufgitter skill and gentle hooks for Claude Code.
   - Do not describe this as a separate built-in swarm backend; it is a mixed workflow.

3. **Antigravity-guided mode**
   - Supported as a documented experimental integration path for launching and monitoring Laufgitter through Antigravity tools such as `run_command` and `manage_task`.
   - Treat this as an advanced, human-gated orchestration environment with design/docs support, not as a built-in default backend, quickstart-ready lane, or same-maturity path as Codex, Grok, or OpenCode unless the repo later promotes it there.

4. **OpenCode local engine mode**
   - Supported when the user enables the OpenCode/OpenRouter engine block and points `bin` at the local `engines/opencode-sandboxed.sh` wrapper.
   - On macOS the wrapper provides write confinement; on non-macOS, explain that the user needs their own sandbox or must explicitly allow a less-confined mode.

If the user does not choose, default to **Laufgitter-native swarms only**.

## Stage 2 – Safe first run: Lint → Baseline → Execute
### Run lint first
```bash
./laufgitter.py lint my-task.json
```

Explain that lint catches weak checks, silent failures, collisions, disappearing worktree deliverables, and underspecified manifests before tokens are spent.

### Run baseline second
```bash
./laufgitter.py run my-task.json --baseline
```

Explain that baseline proves the check fails against the unmodified workspace. If baseline passes unexpectedly, the check is broken and must be fixed before live execution.

### Run the real swarm third
```bash
./laufgitter.py run my-task.json
```

Explain that this starts the real swarm and Zentrale opens automatically.

## What Zentrale is
Zentrale is the default local web dashboard, not a hosted service. It runs on localhost, opens automatically on demo/run, and can be reopened with:

```bash
./laufgitter.py hud
```

Default address:

```text
http://127.0.0.1:8700
```

Explain what the user should look at:
- live results at the top
- worker details below
- artifact/history library afterward

If the user asks about the native HUD, explain that the Tauri app exists, but the web dashboard is the primary/current path.

## Stage 3 – Review results and improve routing
Review Zentrale first: confirm what passed, what failed, what each check proved, and where artifacts landed.

Then review model evidence:

```bash
./laufgitter.py models
```

If the user wants new candidate models, refresh catalog and explore:

```bash
./laufgitter.py catalog
./laufgitter.py models --explore
```

Explain the difference:
- `models` = local evidence from the user's own runs
- `catalog` and `models --explore` = untested candidate discovery and routing ideas

## Maintenance and recovery branches
### Maintenance
If the user wants to update Laufgitter:

```bash
./laufgitter.py self-update
```

Explain that this is the immediate, human-readable update check.

If the user wants to stop Claude Code integration:

```bash
./laufgitter.py uninstall-agent
```

Explain that `install-agent` is reversible and the hooks are gentle/non-blocking.

### Recovery
**If lint fails**
- Rewrite the manifest/check until lint is clean.

**If baseline passes unexpectedly**
- Explain that the check is hallucinating success.
- Fix the check before live execution.

**If the dashboard is not visible**
```bash
./laufgitter.py hud
```

**If the user wants headless operation**
- Prefer `--no-dashboard`.
- If they want a simpler fallback dashboard path, mention `--browser` where appropriate.

**If self-update is blocked**
- Explain dirty tracked tree and fast-forward-only constraints.
- Use `--no-self-update` for one command.
- Use `LAUFGITTER_NO_SELF_UPDATE=1` to disable automatic checks in an environment or service.

**If worktree deliverables disappeared**
- Remind the user that PASS removes task worktrees.
- Have workers write outputs outside the worktree or copy them out in the check.

**If the user wants better routing over time**
- Use `./laufgitter.py models`, `./laufgitter.py catalog`, and `./laufgitter.py models --explore`.

## Platform adaptation
- **Claude Code**: if the user has run `./laufgitter.py install-agent`, the Laufgitter skill and gentle hooks should be active user-level; if not, guide them to install it. `./laufgitter.py uninstall-agent` removes them. The hooks nudge; they do not block.
- **Antigravity**: use `run_command` / `manage_task` to launch and monitor Laufgitter when the user explicitly wants the documented integration path.
- **Codex**: built-in default worker lane.
- **OpenCode/OpenRouter**: supported local engine lane when the user wants a local/cheap universal harness.

## Verification Plan
### Automated
None required yet — this is user-facing documentation. Keep the structure concrete enough that future contract coverage can assert the major sections and commands.

### Manual
1. In Claude Code, ask: **"What is Laufgitter?"**
   - The skill should explain verified swarms and Zentrale before jumping to commands.
2. Ask: **"Show me a demo."**
   - The skill should run demo and narrate what happened plus the next lane choice.
3. Ask: **"I have one question about these files."**
   - The skill should choose `ask`, not a full swarm.
4. Ask: **"I want a real batch run."**
   - The skill should walk manifest → policy choice → lint → baseline → run.
5. Ask: **"Open the dashboard again."**
   - The skill should use `./laufgitter.py hud` and explain Zentrale clearly.
