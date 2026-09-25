# Laufgitter Agent Skill: MECE Capability & Workflow Map

This document outlines the Mutually Exclusive, Collectively Exhaustive (MECE) capabilities, data-flow derived workflows, and critical edge cases required to build an autonomous agent skill for integrating with Laufgitter.

## 1. Capabilities (MECE)

### 1.1 Manifest Engineering (Workload Definition)
The ability to author, validate, and prove execution contracts.
* **Manifest Generation (`Manifest`, `TaskSpec`)**: Generating syntactically valid JSON task definitions (`laufgitter.json`), mapping out `spec`, `check`, `engine`, `model`, `task_type`, `expect_files`, and `max_attempts`.
* **Static Analysis (`lint_manifest`)**: Executing `./laufgitter.py lint` to detect silent probes, write collisions, missing `{spec}` or `{model}` tokens, and worktree conflicts.
* **Negative Verification (`LaufgitterRunner.run(baseline=True)`)**: Executing `./laufgitter.py run --baseline` to mathematically prove that the proposed bash `check` correctly fails against unmodified/empty workspaces.

### 1.2 Swarm Execution (Orchestration)
The ability to dispatch workloads to isolated agent processes and harvest results.
* **Swarm Dispatch (`LaufgitterRunner.run()`)**: Executing `./laufgitter.py run` to spawn parallel workers (`max_parallel`), enforcing strict OS isolation (sandbox/full access) and kill timers.
* **Ad-hoc Querying (`ask`)**: Executing `./laufgitter.py ask` for single, unverified context-packet queries against specific sources without generating a manifest.
* **Artifact Harvesting (`_harvest_deliverables_on_pass`)**: Explicitly copying deliverables out of temporary `taskdir` or Git worktrees before Laufgitter's `_cleanup_worktree_on_pass` prunes them.

### 1.3 Fleet & Telemetry Management (Optimization)
The ability to select the right model based on empirical data and configure new engines.
* **Telemetry Review (`models`)**: Parsing local `runs.jsonl` (via `./laufgitter.py models`) to analyze `first_try_pass_rate` and `pass_rate` by `task_type` for routing decisions.
* **Catalog Synchronization (`refresh_openrouter_catalog`)**: Managing the OpenRouter catalog snapshot (`./laufgitter.py catalog --refresh`) to discover untested/free models.
* **Engine Configuration (`load_engines`)**: Authoring, validating, and merging TOML engine blocks (with `args_template`, `sandbox_args`) into `~/.config/laufgitter/config.toml`.

### 1.4 State & HUD Management (Human-in-the-loop)
* **Zentrale Monitoring (`StateWriter`, `PersistentHudServer`)**: Booting or interacting with the local HUD (`./laufgitter.py hud`) to provide the user with live visual validation of parallel worker streams.

---

## 2. Workflows (Data Flow Derivatives)

### 2.1 The Standard Verification Loop
1. **Author:** Agent writes `laufgitter.json` for a specific sub-task.
2. **Lint:** Agent runs `./laufgitter.py lint`. If warnings appear (e.g., "check cannot fail"), agent rewrites the check.
3. **Baseline:** Agent runs `./laufgitter.py run --baseline`. If baseline passes (exit 0), the check is broken (hallucinated success). Agent rewrites check.
4. **Execute:** Agent runs `./laufgitter.py run`.
5. **Harvest:** Agent reads the target deliverables from the output directory or `artifacts-out/`.

### 2.2 The Phase-Driven Integration Pipeline (Cross-Engine Setup)
* **Phase 0 (Probe):** Run a single-task manifest to assert the proxy/backend is correctly routing the target model (e.g., verify `worker.log` identity).
* **Phase 1 (Research):** Dispatch an exploratory manifest to gather documentation/facts, saving to a structured JSON schema.
* **Phase 2 (Config):** Dispatch a manifest that reads Phase 1's JSON and authors a strict TOML config block.
* **Phase 3 (Execution):** Dispatch a dual-task manifest (`max_parallel: 1`, `worktrees: false`). Task A creates a contract; Task B executes the contract using the newly configured engine.

### 2.3 The Feedback & Remediation Loop
* **Detection:** `Verifier._run_check` returns non-zero exit code.
* **Injection:** Laufgitter captures check failure stdout/stderr and automatically prepends it to the worker's prompt on attempt 2.
* **Resolution:** If attempt 2 fails, Laufgitter marks task as FAIL. The Agent must then read the failure logs in the task directory, adjust the `spec` or `check` in the manifest, and rerun.

---

## 3. Critical Edge Cases

1. **The Worktree Erasure Footgun (`_cleanup_worktree_on_pass`)**
   * *Trigger:* `worktrees: true` (default in some configs) cleans up the repo on PASS.
   * *Impact:* Deliverables written inside the worktree are deleted instantly.
   * *Remediation:* The Agent must write manifests where the `check` explicitly copies deliverables to an `artifacts-out/` directory, or instruct the worker to write outputs outside the repo boundary.
2. **The Silent Pass (`check_may_fail_silently`)**
   * *Trigger:* Writing bash checks that fail to emit output or use commands like `git diff --quiet` (exit 1 with no stdout).
   * *Impact:* If the check fails silently on attempt 1, attempt 2 gets zero diagnostic context injected, resulting in a guaranteed double-fail.
   * *Remediation:* The Agent must explicitly write checks that echo their failure reasons: `command || { echo "FAIL: reason"; exit 1; }`.
3. **Sequential Dependency Collisions (`max_parallel`)**
   * *Trigger:* Tasks that depend on the output of previous tasks run simultaneously.
   * *Impact:* Race conditions, missing files.
   * *Remediation:* The Agent must set `max_parallel: 1` and `worktrees: false` for multi-task sequential dependencies.
4. **Missing Interpolation Tokens (`args_template`)**
   * *Trigger:* Synthesizing engine configs without `{spec}` or `{model}`.
   * *Impact:* CLI fails to launch the worker.
   * *Remediation:* Strict TOML validation gate before merging to `config.toml`.
5. **Non-Canonical Model Misrouting**
   * *Trigger:* A model string bypasses the proxy or routes to a fallback default.
   * *Remediation:* Implement Phase 0 routing probes before trusting a new engine setup.
