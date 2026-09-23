class ShellError(Exception):
    """Base class for expected shell emulator errors."""


class CommandNotFoundError(ShellError):
    """Raised when the entered command is not supported."""

    def __init__(self, name):
        super().__init__(f"unknown command: {name}")


class CommandArgumentError(ShellError):
    """Raised when a command receives invalid arguments."""
