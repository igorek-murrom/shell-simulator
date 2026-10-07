import io
import tempfile
import unittest
from pathlib import Path

from shell_emulator.app import ERROR_CODE
from shell_emulator.app import SUCCESS_CODE
from shell_emulator.app import ShellEmulator
from shell_emulator.cli import build_parser
from shell_emulator.errors import CommandArgumentError
from shell_emulator.errors import CommandNotFoundError


class ReplTests(unittest.TestCase):
    """Tests for the shell emulator."""

    def test_stub_commands(self):
        output = io.StringIO()
        emulator = ShellEmulator(
            output_stream=output,
        )

        self.assertFalse(
            emulator.execute_line("ls one")
        )
        self.assertFalse(
            emulator.execute_line("cd folder")
        )

        result = output.getvalue()
        self.assertIn("ls one", result)
        self.assertIn("cd folder", result)

    def test_unknown_command(self):
        emulator = ShellEmulator(
            output_stream=io.StringIO(),
        )

        with self.assertRaises(CommandNotFoundError):
            emulator.execute_line("missing")

    def test_invalid_arguments(self):
        emulator = ShellEmulator(
            output_stream=io.StringIO(),
        )

        with self.assertRaises(CommandArgumentError):
            emulator.execute_line("cd first second")

    def test_exit(self):
        emulator = ShellEmulator(
            output_stream=io.StringIO(),
        )

        self.assertTrue(
            emulator.execute_line("exit")
        )

    def test_cli_arguments(self):
        parser = build_parser()

        args = parser.parse_args([
            "--vfs",
            "vfs/test.json",
            "--script",
            "scripts/test.txt",
        ])

        self.assertEqual(
            str(args.vfs),
            "vfs/test.json",
        )
        self.assertEqual(
            str(args.script),
            "scripts/test.txt",
        )


class ScriptTests(unittest.TestCase):
    """Tests for startup scripts."""

    def test_script_success(self):
        content = "ls test\nexit\n"

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "script.txt"
            path.write_text(
                content,
                encoding="utf-8",
            )

            output = io.StringIO()
            emulator = ShellEmulator(
                output_stream=output,
            )

            result = emulator.run_script(path)

        self.assertEqual(result, SUCCESS_CODE)
        self.assertIn(
            "ls test",
            output.getvalue(),
        )

    def test_script_stops_on_error(self):
        content = (
            "ls test\n"
            "unknown\n"
            "cd folder\n"
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "script.txt"
            path.write_text(
                content,
                encoding="utf-8",
            )

            output = io.StringIO()
            emulator = ShellEmulator(
                output_stream=output,
            )

            result = emulator.run_script(path)

        self.assertEqual(result, ERROR_CODE)

        result_text = output.getvalue()

        self.assertIn("unknown", result_text)
        self.assertNotIn(
            "cd folder",
            result_text,
        )

    def test_missing_script(self):
        output = io.StringIO()
        emulator = ShellEmulator(
            output_stream=output,
        )

        result = emulator.run_script(
            Path("missing-script.txt")
        )

        self.assertEqual(result, ERROR_CODE)


if __name__ == "__main__":
    unittest.main()