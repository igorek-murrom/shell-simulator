"""Parse supported short options without touching the host filesystem."""

from .errors import CommandArgumentError


def parse_options(name, args, allowed):
    """Accept separate or combined short flags and the -- terminator."""
    flags = set()
    operands = []
    options = True
    for arg in args:
        if options and arg == "--":
            options = False
        elif options and arg.startswith("-") and arg != "-":
            selected = set(arg[1:])
            if not selected <= set(allowed):
                message = f"{name}: unsupported option: {arg}"
                raise CommandArgumentError(message)
            flags.update(selected)
        else:
            operands.append(arg)
    return flags, operands
