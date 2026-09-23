import os
import unittest

from shell_emulator.parser import parse_line


class ParserTests(unittest.TestCase):
    """Tests for command parsing and variable expansion."""

    def test_environment_variable(self):
        name = "SHELL_EMULATOR_TEST"
        old_value = os.environ.get(name)
        os.environ[name] = "value"

        try:
            actual = parse_line(
                "ls $SHELL_EMULATOR_TEST"
            )
            self.assertEqual(actual, ["ls", "value"])
        finally:
            if old_value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old_value

    def test_quotes(self):
        actual = parse_line('ls "two words"')
        self.assertEqual(actual, ["ls", "two words"])
