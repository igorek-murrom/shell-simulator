import os
import shlex

from .errors import CommandArgumentError


def parse_line(line):
    """Expand environment variables and split a command line."""
    expanded = os.path.expandvars(line)

    try:
        return shlex.split(expanded, posix=True)
    except ValueError as error:
        raise CommandArgumentError(
            f"invalid command syntax: {error}"
        ) from error