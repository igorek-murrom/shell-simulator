from .app import ShellEmulator


def main():
    """Start the interactive shell emulator."""
    emulator = ShellEmulator()
    return emulator.run_interactive()
