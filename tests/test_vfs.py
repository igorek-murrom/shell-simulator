"""Check VFS loading, validation, path handling, and memory isolation."""

import json
import tempfile
import unittest
from pathlib import Path

from shell_emulator.errors import VFSError
from shell_emulator.vfs import VirtualFileSystem


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BINARY_SIZE = 16


class VFSTests(unittest.TestCase):
    """Exercise real fixtures and malformed JSON sources."""

    def setUp(self):
        """Allocate an isolated source location for each test."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.source = Path(temporary.name) / "source.json"

    def load_data(self, data):
        """Serialize a tree and load it through the public API."""
        self.source.write_text(json.dumps(data), encoding="utf-8")
        return VirtualFileSystem.load(self.source)

    def load_fixture(self, name):
        """Load a repository VFS example."""
        return VirtualFileSystem.load(PROJECT_ROOT / "vfs" / name)

    def test_minimal(self):
        vfs = self.load_fixture("minimal.json")
        self.assertEqual(vfs.list_directory(), [])
        self.assertEqual(vfs.statistics(), (1, 0, 0))

    def test_text_and_binary_files(self):
        vfs = self.load_fixture("several.json")
        self.assertEqual(vfs.list_directory(), [
            "data.bin", "hello.txt", "two words.txt",
        ])
        self.assertEqual(vfs.read_file("/data.bin"), bytes(range(BINARY_SIZE)))
        self.assertEqual(vfs.read_file("hello.txt"), "Привет, VFS!\n".encode())
        self.assertEqual(vfs.read_file("two words.txt"), b"two words\n")
        self.assertEqual(vfs.statistics(), (1, 3, 45))

    def test_deep_paths(self):
        vfs = self.load_fixture("deep.json")
        path = "/level1/level2/level3"
        self.assertEqual(vfs.read_file("three.txt", path), b"three\n")
        self.assertEqual(vfs.read_file(path + "/data.bin"),
                         bytes(range(BINARY_SIZE)))
        self.assertEqual(vfs.list_directory(path), ["data.bin", "three.txt"])
        self.assertIs(vfs.get_node("../../../../..", path), vfs.root)
        self.assertEqual(vfs.read_file("./../two.txt", path), b"two\n")
        self.assertEqual(vfs.read_file("//level1//one.txt"), b"one\n")
        self.assertEqual(vfs.statistics(), (4, 5, 35))

    def test_invalid_paths(self):
        vfs = self.load_fixture("several.json")
        for path in ("", "\0", "/missing", "/hello.txt/child",
                     "/hello.txt/..", "/hello.txt/", "/hello.txt/."):
            with self.subTest(path=path), self.assertRaises(VFSError):
                vfs.get_node(path)
        with self.assertRaises(VFSError):
            vfs.read_file("/")
        with self.assertRaises(VFSError):
            vfs.list_directory("hello.txt")

    def test_source_is_unchanged_and_not_needed_after_load(self):
        source = PROJECT_ROOT / "vfs" / "several.json"
        original = source.read_bytes()
        self.source.write_bytes(original)
        vfs = VirtualFileSystem.load(self.source)
        self.assertEqual(self.source.read_bytes(), original)
        self.source.unlink()
        self.assertEqual(vfs.read_file("hello.txt"), "Привет, VFS!\n".encode())
        vfs.get_node("hello.txt").content = b"changed in memory"
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(vfs.read_file("hello.txt"), b"changed in memory")
        self.assertEqual(list(self.source.parent.iterdir()), [])

    def test_independent_sessions(self):
        first = self.load_fixture("several.json")
        second = self.load_fixture("several.json")
        first.root.children.clear()
        self.assertEqual(len(second.list_directory()), 3)
        self.assertIsNot(VirtualFileSystem().root, VirtualFileSystem().root)

    def test_missing_or_directory_source(self):
        for path in (self.source, self.source.parent):
            with self.subTest(path=path), self.assertRaises(VFSError):
                VirtualFileSystem.load(path)

    def test_invalid_json_and_encoding(self):
        for content in (b"not json", b"\xff", b'{"name":"/","name":"/"}',
                        b'{"type":"directory",'):
            self.source.write_bytes(content)
            with self.subTest(content=content), self.assertRaises(VFSError):
                VirtualFileSystem.load(self.source)

    def test_invalid_roots(self):
        cases = [None, [], {}, {"type": "other", "name": "/"},
                 {"type": "file", "name": "/", "content": ""},
                 {"type": "directory", "name": "root", "children": []},
                 {"type": "directory", "name": "/", "children": {}},
                 {"type": "directory", "name": "/", "children": [],
                  "extra": True}]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(VFSError):
                self.load_data(data)

    def test_invalid_children(self):
        cases = [None, {}, {"type": "unknown", "name": "x"},
                 {"type": "file", "name": "x"},
                 {"type": "file", "name": "x", "content": 1},
                 {"type": "file", "name": "x", "content": "!",
                  "encoding": "base64"},
                 {"type": "file", "name": "x", "content": "abc",
                  "encoding": "base64"},
                 {"type": "file", "name": "x", "content": "AA==\n",
                  "encoding": "base64"},
                 {"type": "file", "name": "x", "content": "é",
                  "encoding": "base64"},
                 {"type": "file", "name": "x", "content": "",
                  "encoding": "unknown"},
                 {"type": "file", "name": "x", "content": "",
                  "children": []},
                 {"type": "directory", "name": "x", "children": [],
                  "content": ""}]
        for child in cases:
            data = {"type": "directory", "name": "/", "children": [child]}
            with self.subTest(child=child), self.assertRaises(VFSError):
                self.load_data(data)

    def test_invalid_names(self):
        for name in ("", ".", "..", "a/b", "a\\b", "\0", None, 1):
            child = {"type": "file", "name": name, "content": ""}
            data = {"type": "directory", "name": "/", "children": [child]}
            with self.subTest(name=name), self.assertRaises(VFSError):
                self.load_data(data)

    def test_duplicate_names(self):
        child = {"type": "file", "name": "same", "content": ""}
        with self.assertRaises(VFSError):
            self.load_data({"type": "directory", "name": "/",
                            "children": [child, child]})

    def test_empty_files(self):
        children = [{"type": "file", "name": "text", "content": ""},
                    {"type": "file", "name": "binary", "content": "",
                     "encoding": "base64"}]
        vfs = self.load_data({"type": "directory", "name": "/",
                              "children": children})
        self.assertEqual(vfs.read_file("text"), b"")
        self.assertEqual(vfs.read_file("binary"), b"")


if __name__ == "__main__":
    unittest.main()
