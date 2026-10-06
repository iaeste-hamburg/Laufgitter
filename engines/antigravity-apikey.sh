#!/usr/bin/env bash
# Laufgitter engine wrapper: run Google Antigravity CLI (`agy`) with strict API-key auth
# and 100% credential isolation from the user's personal Google OAuth credentials.
#
# Antigravity CLI defaults to host OAuth and stored tokens in ~/.gemini/ unless:
# 1) A configuration file at $HOME/.gemini/antigravity-cli/settings.json exists with
#    "modelProvider": "gemini"
# 2) GEMINI_API_KEY is exported in the process environment.
#
# This wrapper manages an isolated sandbox environment for agy, ensures personal
# OAuth sessions and Keychain credentials are never accessed or prompted, accepts
# either --api-key <KEY> or GEMINI_API_KEY/ANTIGRAVITY_API_KEY, strips --api-key
# before invoking agy, and strictly prevents interactive OAuth fallbacks.
#
# Usage:
#   antigravity-apikey.sh [--api-key <KEY>] [agy args...]
set -euo pipefail

ORIG_HOME="${HOME:-}"
API_KEY="${GEMINI_API_KEY:-${ANTIGRAVITY_API_KEY:-}}"
AGY_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-key)
      if [[ $# -lt 2 ]]; then
        echo "antigravity-apikey.sh: error: --api-key requires an argument" >&2
        exit 1
      fi
      API_KEY="$2"
      shift 2
      ;;
    --api-key=*)
      API_KEY="${1#*=}"
      shift 1
      ;;
    *)
      AGY_ARGS+=("$1")
      shift 1
      ;;
  esac
done

if [[ -z "$API_KEY" ]]; then
  echo "antigravity-apikey.sh: error: No API key provided via --api-key, GEMINI_API_KEY, or ANTIGRAVITY_API_KEY." >&2
  echo "Refusing to fall back to interactive OAuth personal authentication." >&2
  exit 1
fi

# Locate agy binary
if ! AGY_BIN="$(command -v agy 2>/dev/null)" || [[ -z "$AGY_BIN" ]]; then
  if [[ -n "$ORIG_HOME" && -x "$ORIG_HOME/.local/bin/agy" ]]; then
    AGY_BIN="$ORIG_HOME/.local/bin/agy"
  elif [[ -x "/opt/homebrew/bin/agy" ]]; then
    AGY_BIN="/opt/homebrew/bin/agy"
  elif [[ -x "/usr/local/bin/agy" ]]; then
    AGY_BIN="/usr/local/bin/agy"
  else
    echo "antigravity-apikey.sh: error: 'agy' CLI binary not found on PATH" >&2
    exit 127
  fi
fi

# Configure isolated sandbox environment
if [[ -n "${ANTIGRAVITY_SANDBOX_DIR:-}" ]]; then
  SANDBOX_DIR="$ANTIGRAVITY_SANDBOX_DIR"
  mkdir -p "$SANDBOX_DIR/.gemini/antigravity-cli"
else
  SANDBOX_DIR="$(mktemp -d -t laufgitter-agy-isolated-XXXXXX)"
  cleanup() {
    rm -rf "$SANDBOX_DIR"
  }
  trap cleanup EXIT
  mkdir -p "$SANDBOX_DIR/.gemini/antigravity-cli"
fi

cat > "$SANDBOX_DIR/.gemini/antigravity-cli/settings.json" << 'EOF'
{
  "modelProvider": "gemini"
}
EOF

export HOME="$SANDBOX_DIR"
export GEMINI_API_KEY="$API_KEY"
unset GOOGLE_APPLICATION_CREDENTIALS 2>/dev/null || true

# Execute agy within the isolated sandbox
set +e
"$AGY_BIN" "${AGY_ARGS[@]}"
status=$?
set -e
exit "$status"
