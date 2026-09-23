from dataclasses import dataclass
from typing import TextIO

from .state import ShellState


@dataclass
class ShellContext:
    """Shared state passed to command handlers."""

    state: ShellState
    output: TextIO
