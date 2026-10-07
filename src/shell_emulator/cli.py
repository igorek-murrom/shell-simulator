import argparse
from pathlib import Path

from .app import ERROR_CODE
from .app import ShellEmulator


def build_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="UNIX-like shell emulator"
    )
    parser.add_argument(
        "--vfs",
        type=Path,
        help="path to VFS",
    )
    parser.add_argument(
        "--script",
        type=Path,
        help="path to startup script",
    )
    return parser


def _debug_config(args):
    print(f"[debug] vfs={args.vfs}")
    print(f"[debug] script={args.script}")


def main(argv=None):
    """Parse configuration and start the emulator."""
    args = build_parser().parse_args(argv)
    _debug_config(args)

    emulator = ShellEmulator()

    if args.script is not None:
        return emulator.run_script(args.script)

    return emulator.run_interactive()