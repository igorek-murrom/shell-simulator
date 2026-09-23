from .context import ShellContext
from .errors import CommandArgumentError


ONE_ARGUMENT = 1


def _ensure_max_one(name, args):
    if len(args) > ONE_ARGUMENT:
        message = f"{name}: expected at most one argument"
        raise CommandArgumentError(message)


def _ensure_no_args(name, args):
    if args:
        raise CommandArgumentError(
            f"{name}: expected no arguments"
        )


def _print_stub(name, args, output):
    text = name

    if args:
        text += " " + " ".join(args)

    print(text, file=output)


def command_ls(args, context):
    """Execute the stage-one ls stub."""
    _ensure_max_one("ls", args)
    _print_stub("ls", args, context.output)
    return False


def command_cd(args, context):
    """Execute the stage-one cd stub."""
    _ensure_max_one("cd", args)
    _print_stub("cd", args, context.output)
    return False


def command_exit(args, context):
    """Terminate the current emulator session."""
    _ensure_no_args("exit", args)
    return True


COMMANDS = {
    "ls": command_ls,
    "cd": command_cd,
    "exit": command_exit,
}
