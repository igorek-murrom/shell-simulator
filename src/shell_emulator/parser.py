import os
import shlex


def parse_line(line):
    """Expand environment variables and split a command line."""
    expanded = os.path.expandvars(line)
    return shlex.split(expanded, posix=True)
