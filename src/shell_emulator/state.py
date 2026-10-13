from dataclasses import dataclass, field

from .vfs import VirtualFileSystem


@dataclass
class ShellState:
    """Mutable session state with a virtual working directory and tree."""

    cwd: str = "/"
    vfs: VirtualFileSystem = field(default_factory=VirtualFileSystem)
