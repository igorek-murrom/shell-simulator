"""Filter adjacent repeated lines from a virtual UTF-8 file."""

import io
from itertools import groupby

from .errors import CommandArgumentError, VFSError


ONE_OPERAND = 1
SINGLE_LINE = 1
MODES = {"-c", "-d", "-u"}


def _parse_arguments(args):
    """Accept one optional output mode and exactly one file operand."""
    mode = None
    operands = []
    options = True
    for arg in args:
        if options and arg == "--":
            options = False
        elif options and arg in MODES:
            if mode is not None:
                raise CommandArgumentError("uniq: use only one mode")
            mode = arg
        elif options and arg.startswith("-"):
            raise CommandArgumentError(f"uniq: unsupported option: {arg}")
        else:
            operands.append(arg)
    if len(operands) != ONE_OPERAND:
        raise CommandArgumentError("uniq: expected one file argument")
    return mode, operands[0]


def _write_groups(text, mode, output):
    """Compare LF-delimited lines, preserving the first line of each run."""
    for _, group in groupby(io.StringIO(text), key=lambda s: s.rstrip("\n")):
        first = next(group)
        count = SINGLE_LINE + sum(SINGLE_LINE for _ in group)
        if mode == "-d" and count == SINGLE_LINE:
            continue
        if mode == "-u" and count != SINGLE_LINE:
            continue
        prefix = f"{count:7} " if mode == "-c" else ""
        output.write(prefix + first)


def command_uniq(args, context):
    """Print adjacent distinct lines, counts, duplicates, or unique runs."""
    mode, path = _parse_arguments(args)
    state = context.state
    content = state.vfs.read_file(path, state.cwd)
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        raise VFSError(f"uniq: file is not UTF-8: {path}") from error
    _write_groups(text, mode, context.output)
    return False
