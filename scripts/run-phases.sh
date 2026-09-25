#!/usr/bin/env bash
# scripts/run-phases.sh
# Phased execution wrapper for Laufgitter Antigravity Integration.
# Runs laufgitter from original ../Laufgitter path with strict containment to pwd.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PWD_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
ORIGINAL_DIR="$(cd "$PWD_DIR/../Laufgitter" && pwd -P)"
CONFIG_FILE="$PWD_DIR/config.toml"

# Prevent any self-update or catalog rewrite touching outside paths
export LAUFGITTER_NO_SELF_UPDATE=1
export LAUFGITTER_NO_CATALOG_REFRESH=1

usage() {
  cat <<EOF
Usage: $0 <command>

Commands:
  lint                Lint all 4 phase manifests
  baseline <phase>    Run baseline check for phase (0, 1, 2, or 3)
  run 0               Execute Phase 0 (Litellm routing probe)
  run 1               Execute Phase 1 (Antigravity live web research)
  run 2               Execute Phase 2 (Author Antigravity engine block)
  merge-engine        Merge Phase 2 output into local config.toml
  run 3               Execute Phase 3 (Contract-driven screenshot)
  run-all             Execute all phases sequentially with interactive gates

Examples:
  $0 lint
  $0 run 0
  $0 run 1
EOF
  exit 1
}

run_laufgitter() {
  (
    cd "$ORIGINAL_DIR"
    uv run laufgitter.py --config "$CONFIG_FILE" --no-self-update "$@"
  )
}

do_lint() {
  echo "=== Linting all phase manifests ==="
  for phase in phase0-litellm-probe phase1-research-antigravity phase2-author-antigravity-engine phase3-antigravity-screenshot; do
    echo -n "Checking $phase.json: "
    run_laufgitter lint "$PWD_DIR/phases/$phase.json"
  done
  echo "All phase manifests passed lint cleanly."
}

do_baseline() {
  local p="${1:?phase number required (0..3)}"
  case "$p" in
    0) run_laufgitter run "$PWD_DIR/phases/phase0-litellm-probe.json" --baseline ;;
    1) run_laufgitter run "$PWD_DIR/phases/phase1-research-antigravity.json" --baseline ;;
    2) run_laufgitter run "$PWD_DIR/phases/phase2-author-antigravity-engine.json" --baseline ;;
    3) run_laufgitter run "$PWD_DIR/phases/phase3-antigravity-screenshot.json" --baseline ;;
    *) echo "Unknown phase: $p"; exit 1 ;;
  esac
}

do_run_phase0() {
  echo "=== Running Phase 0: Litellm Probe ==="
  run_laufgitter run "$PWD_DIR/phases/phase0-litellm-probe.json" --max-parallel 1
  echo -e "\n--- Phase 0 Gate Check ---"
  local log_file="$PWD_DIR/work/phase0/gpt54-routing-probe/worker.log"
  if [ -f "$log_file" ]; then
    echo "Worker log output excerpt:"
    grep "ROUTING_OK" "$log_file" || true
  else
    echo "Warning: $log_file not found."
  fi
}

do_run_phase1() {
  echo "=== Running Phase 1: Research Antigravity CLI ==="
  run_laufgitter run "$PWD_DIR/phases/phase1-research-antigravity.json" --max-parallel 1
  echo -e "\n--- Phase 1 Gate Check ---"
  local facts_file="$PWD_DIR/work/phase1/research-antigravity-cli/antigravity-cli-facts.json"
  if [ -f "$facts_file" ]; then
    echo "Generated facts file: $facts_file"
    python3 -m json.tool "$facts_file"
  else
    echo "Warning: $facts_file not found."
  fi
}

do_run_phase2() {
  echo "=== Running Phase 2: Author Antigravity Engine Block ==="
  local facts_file="$PWD_DIR/work/phase1/research-antigravity-cli/antigravity-cli-facts.json"
  if [ ! -f "$facts_file" ]; then
    echo "Error: Phase 1 output not found at $facts_file. Run Phase 1 first."
    exit 1
  fi
  run_laufgitter run "$PWD_DIR/phases/phase2-author-antigravity-engine.json" --max-parallel 1
  echo -e "\n--- Phase 2 Gate Check ---"
  local toml_block="$PWD_DIR/work/phase2/write-antigravity-engine-config/antigravity-engine-block.toml"
  if [ -f "$toml_block" ]; then
    echo "Authored TOML block:"
    cat "$toml_block"
    echo -e "\nRun '$0 merge-engine' to merge this block into local config.toml."
  else
    echo "Warning: $toml_block not found."
  fi
}

do_merge_engine() {
  echo "=== Merging Engine Block into Local config.toml ==="
  local toml_block="$PWD_DIR/work/phase2/write-antigravity-engine-config/antigravity-engine-block.toml"
  if [ ! -f "$toml_block" ]; then
    echo "Error: $toml_block does not exist. Run Phase 2 first."
    exit 1
  fi
  if grep -q "\[engines\.antigravity\]" "$CONFIG_FILE"; then
    echo "Warning: [engines.antigravity] already present in $CONFIG_FILE. Replacing with new block..."
    python3 -c "
with open('$CONFIG_FILE', 'r') as f:
    content = f.read()
idx = content.find('[engines.antigravity]')
if idx != -1:
    content = content[:idx].rstrip() + '\n'
with open('$CONFIG_FILE', 'w') as f:
    f.write(content)
"
  fi
  echo "" >> "$CONFIG_FILE"
  cat "$toml_block" >> "$CONFIG_FILE"
  echo "Validating updated config.toml with tomllib..."
  python3 -c "import tomllib; tomllib.load(open('$CONFIG_FILE', 'rb')); print('Merged config.toml is valid.')"
}

do_run_phase3() {
  echo "=== Running Phase 3: Antigravity Contract-Driven Execution ==="
  if ! grep -q "\[engines\.antigravity\]" "$CONFIG_FILE"; then
    echo "Error: [engines.antigravity] missing from $CONFIG_FILE. Run '$0 merge-engine' first."
    exit 1
  fi
  run_laufgitter run "$PWD_DIR/phases/phase3-antigravity-screenshot.json" --max-parallel 1
  echo -e "\n--- Phase 3 Verification ---"
  local artifact="$PWD_DIR/work/phase3/artifacts-out/screenshot.png"
  if [ -f "$artifact" ]; then
    echo "Artifact created: $artifact"
    file "$artifact"
  else
    echo "Warning: $artifact not found."
  fi
}

CMD="${1:-}"
shift || true

case "$CMD" in
  lint)
    do_lint
    ;;
  baseline)
    do_baseline "${1:-}"
    ;;
  run)
    PHASE="${1:-}"
    case "$PHASE" in
      0) do_run_phase0 ;;
      1) do_run_phase1 ;;
      2) do_run_phase2 ;;
      3) do_run_phase3 ;;
      *) echo "Specify phase number: 0, 1, 2, or 3"; exit 1 ;;
    esac
    ;;
  merge-engine)
    do_merge_engine
    ;;
  run-all)
    do_lint
    echo -e "\nPress Enter to execute Phase 0..."; read -r _
    do_run_phase0
    echo -e "\nPress Enter to execute Phase 1..."; read -r _
    do_run_phase1
    echo -e "\nPress Enter to execute Phase 2..."; read -r _
    do_run_phase2
    echo -e "\nMerging engine config into local config.toml..."
    do_merge_engine
    echo -e "\nPress Enter to execute Phase 3..."; read -r _
    do_run_phase3
    echo -e "\n=== Phased Workflow Complete ==="
    ;;
  *)
    usage
    ;;
esac
