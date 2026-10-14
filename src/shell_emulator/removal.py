"""Remove virtual files and directories exclusively from memory."""

from .errors import CommandArgumentError
from .options import parse_options


def command_rm(args, context):
    """Remove files, or directory trees with -r/-R; -f ignores absence."""
    flags, operands = parse_options("rm", args, "rRf")
    if not operands and "f" not in flags:
        raise CommandArgumentError("rm: expected at least one path")
    state = context.state
    for path in operands:
        state.vfs.remove(path, state.cwd, recursive=bool(flags & {"r", "R"}),
                         missing_ok="f" in flags)
    return False


def command_rmdir(args, context):
    """Remove empty virtual directories, processing operands in order."""
    _, operands = parse_options("rmdir", args, "")
    if not operands:
        raise CommandArgumentError("rmdir: expected at least one path")
    state = context.state
    for path in operands:
        state.vfs.remove(path, state.cwd, directory_only=True)
    return False
