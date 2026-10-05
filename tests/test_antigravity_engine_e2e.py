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


def toml_string(value: object) -> str:
    return json.dumps(str(value))


class AntigravityEngineLiveDispatchTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("agy"), "agy CLI binary not found on PATH")
    def test_antigravity_engine_dispatches_and_fulfills_manifest_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            home = root / "home"
            laufgitter_home = root / "laufgitter-home"
            state_dir = root / "state"
            workdir = root / "work"
            runs_jsonl = root / "runs.jsonl"
            config_path = root / "config.toml"
            manifest_path = root / "manifest.json"

            home.mkdir()
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
                        "[engines.antigravity]",
                        'bin = "agy"',
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
                        "run_name": "antigravity-live-dispatch-test",
                        "workdir": str(workdir),
                        "max_parallel": 1,
                        "worktrees": False,
                        "tasks": [
                            {
                                "key": "agy-live-proof-task",
                                "engine": "antigravity",
                                "model": "gemini-3.7-flash-low",
                                "task_type": "code-feature",
                                "full_access": True,
                                "spec": (
                                    "Write a file named proof.txt in the current working directory "
                                    "containing the exact text: AGY_DISPATCH_CONFIRMED"
                                ),
                                "check": (
                                    "grep -q AGY_DISPATCH_CONFIRMED proof.txt || "
                                    "{ echo FAIL: proof.txt missing or lacks AGY_DISPATCH_CONFIRMED; exit 1; }"
                                ),
                                "expect_files": ["proof.txt"],
                                "verified": "Confirms agy successfully executes in taskdir and creates proof.txt.",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            # Preserve user credentials/PATH for agy while isolating Laufgitter state
            env["LAUFGITTER_HOME"] = str(laufgitter_home)

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
                    "antigravity-e2e-tester",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )

            combined_output = proc.stdout + proc.stderr
            task_dir = workdir / "agy-live-proof-task"
            worker_log_file = task_dir / "worker.log"
            log_content = worker_log_file.read_text(encoding="utf-8") if worker_log_file.exists() else "NO WORKER LOG"
            state_files = list(state_dir.glob("runs/*.json"))
            state_content = state_files[0].read_text(encoding="utf-8") if state_files else "NO STATE FILE"
            self.assertEqual(0, proc.returncode, f"{combined_output}\n--- WORKER LOG ---\n{log_content}\n--- STATE ---\n{state_content}")
            self.assertRegex(
                combined_output,
                re.compile(r"^agy-live-proof-task\s+pass\s+PASS\s+1\s+", re.MULTILINE),
                combined_output,
            )

            proof_file = workdir / "agy-live-proof-task" / "proof.txt"
            self.assertTrue(proof_file.exists(), "proof.txt was not created by agy")
            self.assertIn("AGY_DISPATCH_CONFIRMED", proof_file.read_text(encoding="utf-8"))

            worker_log = (workdir / "agy-live-proof-task" / "worker.log").read_text(encoding="utf-8")
            self.assertIn('"status":"SUCCESS"', worker_log)
            self.assertIn('"total_tokens":', worker_log)

            eval_rows = [
                json.loads(line)
                for line in runs_jsonl.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(1, len(eval_rows))
            self.assertEqual("antigravity", eval_rows[0].get("worker_engine"))
            self.assertEqual("PASS", eval_rows[0].get("verdict"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
