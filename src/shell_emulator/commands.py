"""Implement read-only UNIX-like commands against the in-memory VFS."""

import posixpath

from .errors import CommandArgumentError, VFSError
from .prompt import get_username
from .uniq import command_uniq


ONE_ARGUMENT = 1


def _ensure_max_one(name, args):
    """Reject commands with more than one path operand."""
    if len(args) > ONE_ARGUMENT:
        message = f"{name}: expected at most one argument"
        raise CommandArgumentError(message)


def _ensure_no_args(name, args):
    """Reject arguments for commands that have no options or operands."""
    if args:
        raise CommandArgumentError(f"{name}: expected no arguments")


def _ls_arguments(args):
    """Parse the optional -a flag and -- option terminator."""
    show_all = False
    operands = []
    options = True
    for arg in args:
        if options and arg == "--":
            options = False
        elif options and arg == "-a":
            show_all = True
        elif options and arg.startswith("-"):
            raise CommandArgumentError(f"ls: unsupported option: {arg}")
        else:
            operands.append(arg)
    _ensure_max_one("ls", operands)
    return show_all, operands[0] if operands else "."


def command_ls(args, context):
    """List a file or sorted directory entries, optionally including dots."""
    show_all, path = _ls_arguments(args)
    state = context.state
    node = state.vfs.get_node(path, state.cwd)
    if node.type == "file":
        names = [path]
    else:
        names = sorted(node.children)
        if show_all:
            names = [".", ".."] + names
        else:
            names = [name for name in names if not name.startswith(".")]
    for name in names:
        print(name, file=context.output)
    return False


def command_cd(args, context):
    """Change the virtual directory; no operand returns to virtual root."""
    operands = args[1:] if args and args[0] == "--" else args
    _ensure_max_one("cd", operands)
    path = operands[0] if operands else "/"
    if path.startswith("-") and operands == args:
        raise CommandArgumentError(f"cd: unsupported option: {path}")
    state = context.state
    node = state.vfs.get_node(path, state.cwd)
    if node.type != "directory":
        raise VFSError(f"cd: not a directory: {path}")
    full_path = path if path.startswith("/") else state.cwd + "/" + path
    state.cwd = "/" + posixpath.normpath(full_path).lstrip("/")
    return False


def command_whoami(args, context):
    """Print the real OS username also used in the shell prompt."""
    _ensure_no_args("whoami", args)
    print(get_username(), file=context.output)
    return False


def command_exit(args, context):
    """Terminate the current emulator session."""
    _ensure_no_args("exit", args)
    return True


COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "uniq": command_uniq,
    "whoami": command_whoami,
    "exit": command_exit,
}
