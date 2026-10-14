"""List virtual files with short, long, human-readable, and hidden modes."""

from datetime import datetime

from .errors import CommandArgumentError
from .options import parse_options
from .prompt import get_username


ONE_PATH = 1
SIZE_BASE = 1024
DECIMAL_THRESHOLD = 10
SIZE_UNITS = ("", "K", "M", "G", "T", "P", "E")
DIRECTORY_LINKS = 2
FILE_LINKS = 1


def human_size(size):
    """Format bytes using powers of 1024, with suffixes K through E."""
    value = size
    for unit in SIZE_UNITS:
        if value < SIZE_BASE or unit == SIZE_UNITS[-1]:
            if not unit:
                return str(size)
            digits = 1 if value < DECIMAL_THRESHOLD else 0
            return f"{value:.{digits}f}{unit}"
        value /= SIZE_BASE


def _entries(vfs, path, cwd, show_all):
    """Return visible name/node pairs, including actual dot directories."""
    node = vfs.get_node(path, cwd)
    if node.type == "file":
        return [(path, node)]
    entries = [(name, child) for name, child in sorted(node.children.items())
               if show_all or not name.startswith(".")]
    if show_all:
        absolute = vfs.absolute_path(path, cwd)
        entries = [(".", node), ("..", vfs.get_node("..", absolute))] + entries
    return entries


def _long_entry(name, node, flags, username):
    """Use virtual default permissions, group, sizes, and in-memory times."""
    is_directory = node.type == "directory"
    mode = "drwxr-xr-x" if is_directory else "-rw-r--r--"
    links = FILE_LINKS
    size = len(node.content)
    if is_directory:
        links = DIRECTORY_LINKS + sum(
            child.type == "directory" for child in node.children.values())
        size = 0
    size_text = human_size(size) if "h" in flags else str(size)
    timestamp = datetime.fromtimestamp(node.mtime).strftime("%Y-%m-%d %H:%M")
    return f"{mode} {links} {username} vfs {size_text} {timestamp} {name}"


def command_ls(args, context):
    """List one virtual path with any combination of -l, -h, and -a."""
    flags, operands = parse_options("ls", args, "lha")
    if len(operands) > ONE_PATH:
        raise CommandArgumentError("ls: expected at most one argument")
    path = operands[0] if operands else "."
    state = context.state
    entries = _entries(state.vfs, path, state.cwd, "a" in flags)
    username = get_username() if "l" in flags else ""
    for name, node in entries:
        text = name
        if "l" in flags:
            text = _long_entry(name, node, flags, username)
        print(text, file=context.output)
    return False
