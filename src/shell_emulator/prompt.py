import getpass
import os
import socket


def get_username():
    """Return the current operating system user name."""
    return getpass.getuser()


def _normalize(path):
    return os.path.abspath(path).replace("\\", "/")


def _display_path(path):
    home = _normalize(os.path.expanduser("~"))
    current = _normalize(path)

    if current == home:
        return "~"

    prefix = home + "/"
    if current.startswith(prefix):
        return "~" + current[len(home):]

    return current


def build_prompt(path):
    """Build a UNIX-like prompt from current OS information."""
    user = get_username()
    host = socket.gethostname()
    location = _display_path(path)
    return f"{user}@{host}:{location}$ "
