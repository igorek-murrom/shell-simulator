import io
import unittest

from shell_emulator.app import ShellEmulator
from shell_emulator.errors import CommandArgumentError
from shell_emulator.errors import CommandNotFoundError


class ReplTests(unittest.TestCase):
    """Tests for the stage-one command loop."""

    def test_stub_commands(self):
        output = io.StringIO()
        emulator = ShellEmulator(output_stream=output)

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
            output_stream=io.StringIO()
        )

        with self.assertRaises(CommandNotFoundError):
            emulator.execute_line("missing")

    def test_invalid_arguments(self):
        emulator = ShellEmulator(
            output_stream=io.StringIO()
        )

        with self.assertRaises(CommandArgumentError):
            emulator.execute_line("cd first second")

    def test_exit(self):
        emulator = ShellEmulator(
            output_stream=io.StringIO()
        )

        self.assertTrue(
            emulator.execute_line("exit")
        )
