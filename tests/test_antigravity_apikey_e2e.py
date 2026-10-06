#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER_PATH = ROOT / "engines" / "antigravity-apikey.sh"


def toml_string(value: object) -> str:
    return json.dumps(str(value))


def get_tempkeygoogle() -> str:
    key = os.environ.get("TEMPKEYGOOGLE") or os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTIGRAVITY_API_KEY")
    if key:
        return key.strip()
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        match = re.search(r'export\s+TEMPKEYGOOGLE=["\']?([^"\'\s]+)["\']?', zshrc.read_text(encoding="utf-8"))
        if match:
            return match.group(1).strip()
    return ""


class AntigravityApiKeyEngineLiveInferenceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("agy") or Path.home().joinpath(".local/bin/agy").exists(), "agy CLI binary not found")
    def test_antigravity_apikey_live_dispatch_with_tempkeygoogle(self) -> None:
        """Dispatches a real Laufgitter task to Antigravity using TEMPKEYGOOGLE and verifies API key isolation."""
        api_key = get_tempkeygoogle()
        self.assertTrue(api_key, "TEMPKEYGOOGLE was not found in environment or ~/.zshrc")

        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            laufgitter_home = root / "laufgitter-home"
            state_dir = root / "state"
            workdir = root / "work"
            runs_jsonl = root / "runs.jsonl"
            config_path = root / "config.toml"
            manifest_path = root / "manifest.json"

            laufgitter_home.mkdir()

            config_path.write_text(
                "\n".join(
                    [
                        f"state_dir = {toml_string(state_dir)}",
                        "allow_full_access = true",
                        "",
                        "[eval]",
                        'backend = "jsonl"',
                        f"jsonl_path = {toml_string(runs_jsonl)}",
                        "",
                        "[artifact]",
                        "enabled = false",
                        "",
                        "[engines.antigravity_apikey]",
                        f"bin = {toml_string(WRAPPER_PATH)}",
                        'model_default = "gemini-3.7-flash-low"',
                        "args_template = [",
                        '  "{access_args}",',
                        '  "--model",',
                        '  "{model}",',
                        '  "{engine_args}",',
                        '  "--disable-slash-commands",',
                        '  "--output-format",',
                        '  "json",',
                        '  "-p",',
                        '  "{spec}",',
                        "]",
                        'sandbox_args = ["--sandbox"]',
                        'full_access_args = ["--dangerously-skip-permissions"]',
                        'token_regex = \'"total_tokens":\\s*([0-9]+)\'',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            manifest_path.write_text(
                json.dumps(
                    {
                        "run_name": "antigravity-apikey-live-inference-test",
                        "workdir": str(workdir),
                        "max_parallel": 1,
                        "worktrees": False,
                        "tasks": [
                            {
                                "key": "agy-apikey-task",
                                "engine": "antigravity_apikey",
                                "model": "gemini-3.7-flash-low",
                                "task_type": "code-feature",
                                "full_access": True,
                                "spec": (
                                    "Write a file named proof.txt in the current working directory "
                                    "containing the exact text: AGY_APIKEY_INFERENCE_CONFIRMED"
                                ),
                                "check": (
                                    "grep -q AGY_APIKEY_INFERENCE_CONFIRMED proof.txt || "
                                    "{ echo FAIL: proof.txt missing or lacks AGY_APIKEY_INFERENCE_CONFIRMED; exit 1; }"
                                ),
                                "expect_files": ["proof.txt"],
                                "verified": "Confirms agy executes in taskdir with API key.",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["LAUFGITTER_HOME"] = str(laufgitter_home)
            env["GEMINI_API_KEY"] = api_key
            env["TEMPKEYGOOGLE"] = api_key

            proc = subprocess.run(
                [
                    sys.executable,
                    "laufgitter.py",
                    "run",
                    str(manifest_path),
                    "--config",
                    str(config_path),
                    "--no-dashboard",
                    "--identity",
                    "antigravity-apikey-tester",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )

            task_dir = workdir / "agy-apikey-task"
            worker_log_file = task_dir / "worker.log"
            self.assertTrue(worker_log_file.exists(), "worker.log was not generated by Laufgitter worker")
            worker_log = worker_log_file.read_text(encoding="utf-8")

            # CRITICAL ASSERTION 1: Verify host OAuth was NEVER requested
            self.assertNotIn(
                "accounts.google.com/o/oauth2/auth",
                worker_log,
                "Interactive OAuth login was unexpectedly triggered instead of API key auth!",
            )

            # CRITICAL ASSERTION 2: Verify direct inference against Google Gemini API with the key
            # If the upstream Google project is in depleted prepayment state (Error 402):
            if "credits are depleted" in worker_log or "Error 402" in worker_log:
                self.assertIn("Error 402", worker_log)
                self.assertIn("prepayment credits are depleted", worker_log)
                self.assertIn("ai.google.dev", worker_log)
            else:
                # If credits are topped up:
                self.assertEqual(0, proc.returncode, f"Laufgitter failed:\n{proc.stdout}\n{proc.stderr}\nWorker log:\n{worker_log}")
                proof_file = task_dir / "proof.txt"
                self.assertTrue(proof_file.exists(), "proof.txt was not created")
                self.assertIn("AGY_APIKEY_INFERENCE_CONFIRMED", proof_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
