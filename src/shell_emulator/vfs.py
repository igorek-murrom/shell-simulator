"""Load JSON trees and access virtual files entirely in memory."""

import base64
import binascii
import json
import posixpath
import time
from dataclasses import dataclass, field
from pathlib import Path

from .errors import VFSError, VFSNotFoundError


@dataclass
class VFSNode:
    """An in-memory directory or file with decoded byte contents."""

    name: str
    type: str
    content: bytes = b""
    children: dict = field(default_factory=dict)
    mtime: float = field(default_factory=time.time)


def _check_fields(data, required, optional=()):
    """Reject missing and unexpected fields in a JSON node."""
    if not required <= data.keys():
        raise VFSError("invalid VFS format: missing node fields")
    if data.keys() - required - set(optional):
        raise VFSError("invalid VFS format: unexpected node fields")


def _check_name(name, is_root):
    """Require a root slash or a single safe virtual path component."""
    if is_root:
        valid = name == "/"
    else:
        valid = (
            isinstance(name, str) and bool(name)
            and name not in (".", "..")
            and not any(char in name for char in ("/", "\\", "\0"))
        )
    if not valid:
        raise VFSError("invalid VFS format: invalid node name")


def _decode_content(data):
    """Decode UTF-8 text or strictly validated base64 into bytes."""
    _check_fields(data, {"name", "type", "content"}, {"encoding"})
    content = data["content"]
    if not isinstance(content, str):
        raise VFSError("invalid VFS format: content must be a string")
    encoding = data.get("encoding", "utf-8")
    if encoding == "utf-8":
        return content.encode("utf-8")
    if encoding == "base64":
        try:
            return base64.b64decode(content, validate=True)
        except (ValueError, binascii.Error) as error:
            raise VFSError("invalid VFS format: invalid base64") from error
    raise VFSError("invalid VFS format: unsupported file encoding")


def _build_directory(data, node):
    """Validate a directory and recursively build its children."""
    _check_fields(data, {"name", "type", "children"})
    if not isinstance(data["children"], list):
        raise VFSError("invalid VFS format: children must be a list")
    for child_data in data["children"]:
        child = _build_node(child_data)
        if child.name in node.children:
            raise VFSError("invalid VFS format: duplicate child name")
        node.children[child.name] = child


def _build_node(data, is_root=False):
    """Validate and build one node without accessing the host filesystem."""
    if not isinstance(data, dict):
        raise VFSError("invalid VFS format: node must be an object")
    _check_fields(data, {"name", "type"}, {"children", "content", "encoding"})
    _check_name(data["name"], is_root)
    kind = data["type"]
    if kind not in ("directory", "file"):
        raise VFSError("invalid VFS format: unknown node type")
    if is_root and kind != "directory":
        raise VFSError("invalid VFS format: root must be a directory")
    node = VFSNode(data["name"], kind)
    if kind == "directory":
        _build_directory(data, node)
    else:
        node.content = _decode_content(data)
    return node


def _unique_object(pairs):
    """Reject duplicate JSON keys instead of silently discarding values."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise VFSError("invalid VFS format: duplicate JSON key")
        result[key] = value
    return result


@dataclass
class VirtualFileSystem:
    """A virtual tree independent of its source after loading."""

    root: VFSNode = field(
        default_factory=lambda: VFSNode("/", "directory")
    )

    @classmethod
    def load(cls, source):
        """Read a JSON source once and validate the complete tree."""
        try:
            text = Path(source).read_text(encoding="utf-8")
            data = json.loads(text, object_pairs_hook=_unique_object)
            return cls(_build_node(data, is_root=True))
        except OSError as error:
            raise VFSError(f"cannot load VFS '{source}': {error}") from error
        except (ValueError, UnicodeError, RecursionError) as error:
            message = f"invalid VFS format in '{source}': {error}"
            raise VFSError(message) from error

    def get_node(self, path, cwd="/"):
        """Resolve a UNIX path, checking every traversed component."""
        if not isinstance(path, str) or not path or "\0" in path:
            raise VFSError("invalid VFS path")
        full_path = path if path.startswith("/") else cwd + "/" + path
        stack = [self.root]
        for part in full_path.split("/"):
            if part:
                self._walk_component(stack, part, path)
        node = stack[-1]
        if path.endswith("/") and node.type != "directory":
            raise VFSError(f"not a directory: {path}")
        return node

    def _walk_component(self, stack, part, path):
        """Advance through one component or move toward the virtual root."""
        node = stack[-1]
        if node.type != "directory":
            raise VFSError(f"not a directory: {node.name}")
        if part == ".":
            return
        if part == "..":
            if node is not self.root:
                stack.pop()
            return
        if part not in node.children:
            raise VFSNotFoundError(
                f"no such file or directory: {path}")
        stack.append(node.children[part])

    def list_directory(self, path="/", cwd="/"):
        """Return sorted names from a virtual directory."""
        node = self.get_node(path, cwd)
        if node.type != "directory":
            raise VFSError(f"not a directory: {path}")
        return sorted(node.children)

    def read_file(self, path, cwd="/"):
        """Return file bytes without rereading or modifying the JSON source."""
        node = self.get_node(path, cwd)
        if node.type != "file":
            raise VFSError(f"is a directory: {path}")
        return node.content

    @staticmethod
    def absolute_path(path, cwd="/"):
        """Normalize an already validated path inside the virtual root."""
        full_path = path if path.startswith("/") else cwd + "/" + path
        return "/" + posixpath.normpath(full_path).lstrip("/")

    def _check_removal(self, path, cwd):
        """Reject special entries and keep the active directory reachable."""
        if not isinstance(path, str) or not path or "\0" in path:
            raise VFSError("invalid VFS path")
        if path.rstrip("/").split("/")[-1] in (".", ".."):
            raise VFSError(f"cannot remove '.' or '..': {path}")
        absolute = self.absolute_path(path, cwd)
        current = self.absolute_path(cwd)
        if absolute == "/":
            raise VFSError("cannot remove virtual root")
        if current == absolute or current.startswith(absolute + "/"):
            message = f"cannot remove current directory or ancestor: {path}"
            raise VFSError(message)

    def _check_removal_type(self, node, path, recursive, directory_only):
        """Validate directory emptiness or require recursive removal."""
        if directory_only:
            if node.type != "directory":
                raise VFSError(f"not a directory: {path}")
            if node.children:
                raise VFSError(f"directory not empty: {path}")
        elif node.type == "directory" and not recursive:
            raise VFSError(f"is a directory (use rm -r): {path}")

    def remove(self, path, cwd="/", recursive=False, directory_only=False,
               missing_ok=False):
        """Unlink a validated node without writing to the JSON source."""
        self._check_removal(path, cwd)
        try:
            node = self.get_node(path, cwd)
        except VFSNotFoundError:
            if missing_ok:
                return
            raise
        self._check_removal_type(node, path, recursive, directory_only)
        absolute = self.absolute_path(path, cwd)
        parent = self.get_node(posixpath.dirname(absolute))
        del parent.children[node.name]
        parent.mtime = time.time()


    def statistics(self):
        """Count directories, files, and decoded file bytes, including root."""
        directories = files = size = 0
        pending = [self.root]
        while pending:
            node = pending.pop()
            if node.type == "directory":
                directories += 1
                pending.extend(node.children.values())
            else:
                files += 1
                size += len(node.content)
        return directories, files, size
