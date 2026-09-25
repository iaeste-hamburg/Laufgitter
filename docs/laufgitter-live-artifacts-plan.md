# Laufgitter Live Artifacts — Design Plan

**Author:** aicred (Claude, MBP) — 2026-07-04, written during the aicred baseline-repair double swarm
**For:** Jon → Laufgitter repo (github.com/iaeste-hamburg/Laufgitter, Lex maintains)
**Goal:** live, shareable visual status/review pages from Laufgitter runs with ZERO Anthropic tokens.
Reserve Fable/Claude for what it's uniquely good at (triage judgment, adversarial verification,
boss-level integration) and stop spending it on dashboard upkeep.

## Why

Tonight's data point: keeping a live status artifact updated through a swarm run cost a dedicated
Claude subagent ~90k+ tokens for what is, structurally, a template render of state Laufgitter already
has on disk. Meanwhile the compiled 211-recommendation review HTML from yesterday cost one Codex
writer worker ~284k OpenAI tokens. Both jobs are automatable inside Laufgitter at the right tier:

| Tier | Job | Engine | Marginal cost |
|------|-----|--------|---------------|
| 0 | Live swarm progress page | Pure Python (no LLM) | $0, forever |
| 1 | Synthesized review/report page (judgment content) | `codex exec`, cheap model | OpenAI tokens only |
| 2 | Hosting/sharing beyond the local machine | pluggable publish hook | whatever the hook costs |

## Tier 0 — zero-LLM live status artifact (the big win)

Laufgitter is zero-LLM orchestration; the status page should be too. Every fact a progress dashboard
shows already lives in the run state (`~/.laufgitter/runs/<run>.json`): task keys, status
(queued/running/pass/fail/retry), timings, check commands, retry counts, eval rows.

**Change:** add a `render_status_html(state) -> str` function (stdlib only, one big template
string) and call it at every point laufgitter.py flushes run state. Write the result next to the state
file AND to an optional configured path.

```toml
# config.toml
[artifact]
enabled = true
out = "~/.laufgitter/artifacts/{run_name}.html"   # {run_name}, {ts} substitutions
open_on_start = false                          # Zentrale already opens; this is for extra displays
```

Page requirements:
