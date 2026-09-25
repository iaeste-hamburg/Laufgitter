# Zentrale Upgrade Notes

Working log for the four-feature Zentrale/Laufgitter upgrade (2026-07-04). Written while two
production swarms (`aicred-docs-repair`, `aicred-site-fixes`) were live — all edits happened in
an isolated git worktree, never in `~/fleet/swarm` directly (its `dashboard/dashboard.html` is
re-read from disk on every live-dashboard HTTP request by the running orchestrators, so editing
it in place would have visibly corrupted Jon's screen recording).

## Stack discovered

- **Repo:** `~/fleet/swarm` (git, `main` branch, Jon works here on the Mac alongside Lex; push feature branches + PRs).
- **Laufgitter** (`laufgitter.py`, stdlib-only Python 3.11+): orchestrator + per-run state writer
  (`~/.laufgitter/runs/<run_id>.json`, flushed every 1s) + optional embedded HTTP dashboard
  (`Dashboard` class, serves `dashboard/dashboard.html` + `/state.json`, live-read from disk
  every request — no caching).
- **Zentrale** (`hud/`): a **Tauri v2** app (Rust backend `hud/src/main.rs` + vanilla-JS/HTML
  frontend, NOT SwiftUI/React). `productName: Zentrale`, `identifier: com.jonedwards.zentrale`.
  - Rust side polls `~/.laufgitter/runs/*.json` every 1s (`start_state_poller`), computes
    live/finished/died state + sort order, emits a `laufgitter-runs` Tauri event with the full JSON
    array (fields are passed through mostly verbatim — new task/run JSON fields show up in the
    frontend for free, no Rust changes needed unless you need new file I/O or window behavior).
  - Frontend: `hud/dist/index.html` (webview HTML+CSS+JS) is a **generated copy** of the repo's
    canonical `dashboard/dashboard.html` — synced by `hud/scripts/sync-dist.sh` at build time.
    **Always edit `dashboard/dashboard.html`, never `hud/dist/index.html` directly**, then run
    the sync script (or let `tauri build`'s `beforeBuildCommand` do it).
  - `hud/frontend/hud.js` (synced to `hud/dist/hud.js`) is the Tauri-only bridge: builds the
    custom title bar, window drag, close button, HUD ticker text. It listens for `laufgitter-runs`
    and also calls the shared `update()` function defined inline in `dashboard.html`.
  - `dashboard.html`'s inline script also does `pollLocalState()` — a `fetch('/state.json')`
    poll. That's for when the SAME html is served by laufgitter.py's own embedded HTTP dashboard
    (browser tab, no Tauri). Under Tauri it 404s harmlessly (try/catch swallows it) since there's
    no HTTP server backing the webview.
  - Window: 360x420 default, transparent, decorations:false, alwaysOnTop, resizable (min
    280x220). `toggle_collapse` Tauri command shrinks it to a 34px title-bar-only strip.
  - Capabilities: `hud/capabilities/default.json` lists allowed commands
    (`core:default` + window permissions). New `#[tauri::command]` fns must be added to both
    `invoke_handler!` in `main.rs` AND (if not covered by `core:default`) get a permission there.

## Branch / worktree

- Canonical repo: `~/fleet/swarm` (do not edit while swarms are live).
- Working worktree: `~/fleet/swarm-zentrale-upgrades`, branch `feat/zentrale-upgrades`.
- Local only — never pushed, never touched `main`.

## What changed (laufgitter.py — Tier 0 + Tier 4 "final report", the plan doc's build order #1)

File: `~/fleet/swarm-zentrale-upgrades/laufgitter.py`

- Added `ArtifactConfig` dataclass + `load_artifact_config()`; new `[artifact]` config block
  (`enabled`, `out` template, `report_out` template, `index_out`) documented in
  `config.sample.toml`. Defaults write under `~/.laufgitter/artifacts/`.
- `TaskRuntime` gained `last_check_output`, `last_check_returncode`, `last_check_timed_out` —
  previously the verify/check output was logged to the eval sink and then thrown away; nothing
  else in the process remembered it, so neither a live page nor a final report could show *why*
  a task failed without grepping `worker.log`. Set in `LaufgitterRunner._run_task` right after
  `verify = await self.verifier.verify(...)`.
- `StateWriter` now takes `max_parallel` + `artifact: ArtifactConfig`. `snapshot()` gained, per
  task: `check` (the check command), `timeout_s`, `taskdir` (absolute path, for report links),
  `verdict` (PASS/FAIL/TIMEOUT/ERROR — more specific than `status`), `check_returncode`,
  `check_output_tail` (capped), `log_tail_full` (40 lines vs the existing 3-line `log_tail`) —
