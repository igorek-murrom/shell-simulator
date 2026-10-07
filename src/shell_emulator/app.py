import sys

from . import context
from .commands import COMMANDS
from .context import ShellContext
from .errors import ShellError
from .errors import CommandNotFoundError
from .parser import parse_line
from .prompt import build_prompt
from .state import ShellState
from pathlib import Path

SUCCESS_CODE = 0
ERROR_CODE = 1
SUCCESS_CODE = 0


class ShellEmulator:
    """Console application that executes shell commands."""

    def __init__(self, input_stream=None, output_stream=None):
        self.input = input_stream or sys.stdin
        self.output = output_stream or sys.stdout
        state = ShellState()
        self.context = ShellContext(state, self.output)

    def execute_line(self, line):
        """Parse and execute one command line."""
        tokens = parse_line(line)

        if not tokens:
            return False

        name = tokens[0]
        handler = COMMANDS.get(name)

        if handler is None:
            raise CommandNotFoundError(name)

        return handler(tokens[1:], self.context)

    def _report_error(self, error):
        print(f"error: {error}", file=self.output)

    def _report_error_summary(self):
        print("Execution finished with errors.", file=self.output)

    def run_interactive(self):
        """Run the emulator until exit or end of input."""
        had_error = False
        while True:
            prompt = build_prompt(self.context.state.cwd)
            self.output.write(prompt)
            self.output.flush()

            try:
                line = self.input.readline()
            except KeyboardInterrupt:
                self.output.write("\n")
                continue

            if not line:
                if had_error:
                    self._report_error_summary()
                return SUCCESS_CODE

            try:
                if self.execute_line(line.rstrip("\n")):
                    if had_error:
                        self._report_error_summary()
                    return SUCCESS_CODE
            except ShellError as error:
                had_error = True
                self._report_error(error)

    def run_script(self, script_path):
        """Execute a startup script and stop on the first error."""
        path = Path(script_path)

        try:
            with path.open("r", encoding="utf-8") as script:
                for raw_line in script:
                    line = raw_line.rstrip("\n")

                    if not line.strip():
                        continue

                    self.output.write(
                        build_prompt(self.context.state.cwd)
                    )
                    self.output.write(line + "\n")
                    self.output.flush()

                    try:
                        if self.execute_line(line):
                            return SUCCESS_CODE
                    except ShellError as error:
                        self._report_error(error)
                        self._report_error_summary()
                        return ERROR_CODE
        except OSError as error:
            self._report_error(error)
            self._report_error_summary()
            return ERROR_CODE

        return SUCCESS_CODE
