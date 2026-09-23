from dataclasses import dataclass, field
import os


@dataclass
class ShellState:
    """Mutable state of the emulator session."""

    cwd: str = field(default_factory=os.getcwd)
