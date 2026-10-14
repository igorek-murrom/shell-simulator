"""Test complete stage-three CLI sessions and demonstration scenarios."""

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from shell_emulator.app import ShellEmulator
from shell_emulator.cli import main
from shell_emulator.vfs import VirtualFileSystem


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class StageThreeTests(unittest.TestCase):
    """Verify that VFS configuration reaches the emulator and scripts."""

    def run_cli(self, *arguments, input_text=""):
        """Run the public entry point with controlled streams."""
        output = io.StringIO()
        with redirect_stdout(output), patch("sys.stdin",
                                            io.StringIO(input_text)):
            result = main(list(arguments))
        return result, output.getvalue()

    def test_empty_default_vfs(self):
        result, output = self.run_cli(input_text="ls\nexit\n")
        self.assertEqual(result, 0)
        self.assertIn("directories=1, files=0, bytes=0", output)
        self.assertIn(":/$ ", output)

    def test_loaded_vfs_is_attached_to_session(self):
        vfs = VirtualFileSystem.load(PROJECT_ROOT / "vfs/deep.json")
        emulator = ShellEmulator(vfs=vfs, output_stream=io.StringIO())
        self.assertIs(emulator.context.state.vfs, vfs)
        self.assertEqual(emulator.context.state.cwd, "/")
        emulator.execute_line("cd /level1")
        self.assertEqual(emulator.context.state.cwd, "/level1")

    def test_success_script_and_exit(self):
        arguments = ("--vfs", str(PROJECT_ROOT / "vfs/deep.json"),
                     "--script", str(PROJECT_ROOT /
                                     "scripts/stage3_success.txt"))
        with patch.dict(os.environ, {"HOME": "/test home"}):
            result, output = self.run_cli(*arguments)
        self.assertEqual(result, 0)
        self.assertIn("directories=4, files=5, bytes=35", output)
        self.assertIn("level1\nroot.txt\n", output)
        self.assertNotIn("unknown_after_exit", output)
        self.assertNotIn("error:", output)

    def test_each_error_script_stops_immediately(self):
        cases = {"unknown": "unknown command", "ls_error": "ls: expected",
                 "cd_error": "cd: expected", "exit_error": "exit: expected",
                 "syntax_error": "invalid command syntax"}
        for scenario, message in cases.items():
            script = PROJECT_ROOT / f"scripts/stage3_{scenario}.txt"
            with self.subTest(scenario=scenario):
                result, output = self.run_cli("--script", str(script))
                self.assertEqual(result, 1)
                self.assertIn(message, output)
                self.assertNotIn("must_not_execute", output)
                self.assertEqual(output.count(
                    "Execution finished with errors."), 1)

    def test_invalid_vfs_prevents_script_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.json"
            source.write_text("[]", encoding="utf-8")
            script = PROJECT_ROOT / "scripts/stage3_success.txt"
            result, output = self.run_cli("--vfs", str(source),
                                          "--script", str(script))
        self.assertEqual(result, 1)
        self.assertIn("invalid VFS format", output)
        self.assertNotIn("$ ls", output)
        self.assertNotIn("Traceback", output)

    def test_non_utf8_script_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "invalid.txt"
            script.write_bytes(b"\xff")
            result, output = self.run_cli("--script", str(script))
        self.assertEqual(result, 1)
        self.assertIn("error:", output)
        self.assertNotIn("Traceback", output)

    def test_os_demonstrations_from_another_directory(self):
        sources = list((PROJECT_ROOT / "vfs").glob("*.json"))
        before = {source: source.read_bytes() for source in sources}
        with tempfile.TemporaryDirectory() as directory:
            for name in ("vfs", "interactive", "errors"):
                script = PROJECT_ROOT / f"scripts/stage3_{name}.sh"
                result = subprocess.run(
                    ["bash", str(script)], cwd=directory,
                    capture_output=True, text=True, timeout=20,
                )
                with self.subTest(script=name):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("files=0", result.stdout)
                    self.assertIn("files=3", result.stdout)
                    self.assertIn("files=5", result.stdout)
                    self.assertNotIn("Traceback", result.stdout)
                    self.assertNotIn("must_not_execute", result.stdout)
        self.assertEqual(before, {
            source: source.read_bytes() for source in sources
        })


if __name__ == "__main__":
    unittest.main()
