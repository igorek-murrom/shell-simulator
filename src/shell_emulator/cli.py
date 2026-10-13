import argparse
from pathlib import Path

from .app import ERROR_CODE
from .app import ShellEmulator
from .errors import VFSError
from .vfs import VirtualFileSystem


def build_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="UNIX-like shell emulator"
    )
    parser.add_argument(
        "--vfs",
        type=Path,
        help="path to a JSON VFS (default: empty in-memory root)",
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

    try:
        vfs = (
            VirtualFileSystem.load(args.vfs)
            if args.vfs is not None else VirtualFileSystem()
        )
    except VFSError as error:
        print(f"error: {error}")
        print("Execution finished with errors.")
        return ERROR_CODE

    directories, files, size = vfs.statistics()
    print(
        f"[debug] VFS loaded: directories={directories}, "
        f"files={files}, bytes={size}"
    )
    emulator = ShellEmulator(vfs=vfs)

    if args.script is not None:
        return emulator.run_script(args.script)

    return emulator.run_interactive()
