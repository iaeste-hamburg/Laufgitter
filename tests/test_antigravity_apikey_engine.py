#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER_PATH = ROOT / "engines" / "antigravity-apikey.sh"


class AntigravityApiKeyEngineWrapperTests(unittest.TestCase):
    def test_wrapper_fails_when_no_api_key_provided(self) -> None:
        """Wrapper must exit 1 with a strict error if no API key is passed, preventing OAuth fallback."""
        env = os.environ.copy()
        env.pop("GEMINI_API_KEY", None)
        env.pop("ANTIGRAVITY_API_KEY", None)

        proc = subprocess.run(
            [str(WRAPPER_PATH), "-p", "hello"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        self.assertEqual(1, proc.returncode)
        self.assertIn("No API key provided", proc.stderr)
        self.assertIn("Refusing to fall back to interactive OAuth", proc.stderr)

    def test_wrapper_executes_isolated_sandbox_with_mock_agy(self) -> None:
        """Wrapper must isolate HOME, write settings.json, pass stripped args, and export GEMINI_API_KEY."""
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            mock_bin_dir = root / "bin"
            mock_bin_dir.mkdir()
            mock_agy = mock_bin_dir / "agy"

            # Create mock agy that dumps its environment and argv to a json file
            mock_agy.write_text(
                "#!/usr/bin/env bash\n"
                "echo \"HOME=$HOME\"\n"
                "echo \"GEMINI_API_KEY=$GEMINI_API_KEY\"\n"
                "echo \"ARGS=$*\"\n"
                "if [[ -f \"$HOME/.gemini/antigravity-cli/settings.json\" ]]; then\n"
                "  echo \"SETTINGS_EXISTS=1\"\n"
                "  cat \"$HOME/.gemini/antigravity-cli/settings.json\"\n"
                "else\n"
                "  echo \"SETTINGS_EXISTS=0\"\n"
                "fi\n"
            )
            mock_agy.chmod(mock_agy.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            env = os.environ.copy()
            env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
            env.pop("GEMINI_API_KEY", None)
            env.pop("ANTIGRAVITY_API_KEY", None)

            # Test invocation with --api-key flag
            proc = subprocess.run(
                [
                    str(WRAPPER_PATH),
                    "--api-key",
                    "AIzaSyTestMockKey999",
                    "--model",
                    "gemini-3.8-flash-high",
                    "-p",
                    "test prompt",
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            self.assertEqual(0, proc.returncode, f"stdout: {proc.stdout}\nstderr: {proc.stderr}")
            self.assertIn("GEMINI_API_KEY=AIzaSyTestMockKey999", proc.stdout)
            # Ensure --api-key was stripped from arguments forwarded to agy
            self.assertNotIn("--api-key", proc.stdout)
            self.assertIn("ARGS=--model gemini-3.8-flash-high -p test prompt", proc.stdout)
            # Ensure isolated settings.json was written
            self.assertIn("SETTINGS_EXISTS=1", proc.stdout)
            self.assertIn('"modelProvider": "gemini"', proc.stdout)
            # Ensure HOME was pointed to a temporary sandbox, not the host user's home
            self.assertNotIn(f"HOME={os.environ['HOME']}\n", proc.stdout)
            self.assertIn("laufgitter-agy-isolated", proc.stdout)

    def test_wrapper_picks_up_gemini_api_key_from_env(self) -> None:
        """Wrapper must recognize GEMINI_API_KEY from environment without requiring --api-key."""
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            mock_bin_dir = root / "bin"
            mock_bin_dir.mkdir()
            mock_agy = mock_bin_dir / "agy"

            mock_agy.write_text(
                "#!/usr/bin/env bash\n"
                "echo \"CAPTURED_KEY=$GEMINI_API_KEY\"\n"
                "echo \"CAPTURED_ARGS=$*\"\n"
            )
            mock_agy.chmod(mock_agy.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            env = os.environ.copy()
            env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
            env["GEMINI_API_KEY"] = "AIzaSyEnvVarKey123"

            proc = subprocess.run(
                [str(WRAPPER_PATH), "-p", "run task"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            self.assertEqual(0, proc.returncode, f"stdout: {proc.stdout}\nstderr: {proc.stderr}")
            self.assertIn("CAPTURED_KEY=AIzaSyEnvVarKey123", proc.stdout)
            self.assertIn("CAPTURED_ARGS=-p run task", proc.stdout)


if __name__ == "__main__":
    unittest.main()
