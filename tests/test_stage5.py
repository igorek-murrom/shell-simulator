"""Verify in-memory removal, ls flags, and stage-five demonstrations."""

import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shell_emulator.app import ShellEmulator
from shell_emulator.errors import ShellError, VFSNotFoundError
from shell_emulator.vfs import VirtualFileSystem


ROOT = Path(__file__).resolve().parents[1]


class StageFiveTests(unittest.TestCase):
    """Test public commands against an independently loaded JSON fixture."""

    def setUp(self):
        """Load a fresh VFS and capture output for every test."""
        self.source = ROOT / "vfs/stage5.json"
        self.original = self.source.read_bytes()
        self.output = io.StringIO()
        self.vfs = VirtualFileSystem.load(self.source)
        self.shell = ShellEmulator(vfs=self.vfs, output_stream=self.output)

    def execute(self, command):
        """Capture only one command's output."""
        self.output.seek(0)
        self.output.truncate()
        self.assertFalse(self.shell.execute_line(command))
        return self.output.getvalue()

    def test_rm_files_and_rmdir_empty_directories(self):
        self.assertEqual(self.execute('rm "two words.txt" .hidden'), "")
        self.execute("rmdir empty tree/empty")
        self.execute("cd tree")
        self.execute("rm ./one.txt")
        self.assertEqual(self.execute("ls"), "deep\n")
        for path in ("/two words.txt", "/.hidden", "/empty", "/tree/one.txt"):
            with self.subTest(path=path), self.assertRaises(VFSNotFoundError):
                self.vfs.get_node(path)
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_recursive_modes_and_statistics(self):
        before = self.vfs.statistics()
        self.execute("rm -r tree")
        self.assertEqual(self.vfs.statistics(),
                         (before[0] - 4, before[1] - 3, before[2] - 14))
        with self.assertRaises(VFSNotFoundError):
            self.vfs.get_node("tree")
        self.execute("rm -Rf empty")
        self.execute("rm -rf /missing")
        self.execute("rm -f")
        self.execute("rm -r -f /missing/child")

    def test_rm_force_does_not_hide_type_or_path_errors(self):
        for line in ("rm -f tree", "rm -f large.txt/child",
                     "rm -f large.txt/", 'rm -f ""', "rm -rf /",
                     "rm -rf tree/deep/.."):
            before = self.vfs.statistics()
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute_line(line)
            self.assertEqual(self.vfs.statistics(), before)

    def test_root_current_and_ancestor_protection(self):
        self.execute("cd tree/deep/level3")
        for path in ("/", "//", "/tree", "/tree/deep", ".", "..",
                     "./", "../", "/tree/deep/level3", "/tree/../tree"):
            with self.subTest(path=path), self.assertRaises(ShellError):
                self.shell.execute_line("rm -rf " + path)
        self.assertEqual(self.shell.context.state.cwd, "/tree/deep/level3")
        self.assertEqual(self.execute("ls"), "three.txt\n")
        self.execute("cd /")
        self.execute("rm -r /tree//deep/./level3/")
        self.assertEqual(self.execute("ls tree/deep"), "two.txt\n")

    def test_rmdir_type_emptiness_and_multiple_operands(self):
        for line in ("rmdir large.txt", "rmdir tree", "rmdir /",
                     "rmdir .", "rmdir missing", "rmdir -p empty"):
            before = self.vfs.statistics()
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute_line(line)
            self.assertEqual(self.vfs.statistics(), before)
        self.execute("rmdir /empty/ tree/empty")
        self.assertEqual(self.execute("ls tree"), "deep\none.txt\n")

    def test_option_terminator_and_partial_failure(self):
        self.execute("rm -- -dash.txt")
        self.execute("rmdir -- -empty")
        with self.assertRaises(ShellError):
            self.shell.execute_line('rm "two words.txt" missing large.txt')
        with self.assertRaises(VFSNotFoundError):
            self.vfs.get_node("two words.txt")
        self.assertEqual(len(self.vfs.read_file("large.txt")), 1536)

    def test_invalid_arguments_do_not_mutate_tree(self):
        for line in ("rm", "rmdir", "rm -z large.txt", "ls -lhz",
                     "ls -l / /", "rmdir --", "rm --", 'rmdir ""'):
            before = self.vfs.statistics()
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute_line(line)
            self.assertEqual(self.vfs.statistics(), before)

    def test_ls_long_sizes_permissions_and_links(self):
        with patch("shell_emulator.listing.get_username", return_value="u"):
            large = self.execute("ls -l large.txt")
            human = self.execute("ls -lh large.txt")
            entries = self.execute("ls -la tree")
        self.assertRegex(large,
                         r"^-rw-r--r-- 1 u vfs 1536 .+ large.txt\n$")
        self.assertRegex(human,
                         r"^-rw-r--r-- 1 u vfs 1\.5K .+ large.txt\n$")
        self.assertRegex(entries.splitlines()[0], r"^drwxr-xr-x 4 u vfs 0 ")
        self.assertTrue(entries.splitlines()[0].endswith(" ."))
        self.assertTrue(entries.splitlines()[1].endswith(" .."))
        self.execute("rmdir tree/empty")
        self.assertRegex(self.execute("ls -la tree").splitlines()[0],
                         r"^drwxr-xr-x 3 ")

    def test_ls_all_combinations(self):
        with patch("shell_emulator.listing.get_username", return_value="u"):
            for flags in ("-l", "-h", "-a", "-lh", "-la", "-ha", "-lha"):
                separated = " ".join("-" + char for char in flags[1:])
                with self.subTest(flags=flags):
                    self.assertEqual(self.execute("ls " + flags),
                                     self.execute("ls " + separated))
            self.assertEqual(self.execute("ls -lah"), self.execute("ls -alh"))
        self.assertEqual(self.execute("ls -h"), self.execute("ls"))
        self.assertNotIn(".hidden", self.execute("ls -lh"))
        self.assertIn(".hidden", self.execute("ls -lah"))
        self.assertEqual(self.execute("ls -lh empty"), "")
        self.assertEqual(len(self.execute("ls -lah empty").splitlines()), 2)
        self.assertEqual(self.execute("ls -h -- -dash.txt"), "-dash.txt\n")

    def test_human_size_boundaries_and_utf8_bytes(self):
        node = self.vfs.get_node("large.txt")
        cases = ((0, "0"), (1023, "1023"), (1024, "1.0K"),
                 (1536, "1.5K"), (10240, "10K"), (1048576, "1.0M"))
        for size, expected in cases:
            node.content = b"x" * size
            with self.subTest(size=size):
                self.assertEqual(self.execute("ls -lh large.txt").split()[4],
                                 expected)
        node.content = "ёж".encode()
        self.assertEqual(self.execute("ls -l large.txt").split()[4], "4")

    def test_source_is_not_needed_and_sessions_are_independent(self):
        second = VirtualFileSystem.load(self.source)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "vfs.json"
            source.write_bytes(self.original)
            self.shell.context.state.vfs = VirtualFileSystem.load(source)
            source.unlink()
            self.execute("rm -r tree")
            self.execute("rmdir empty")
            self.execute("ls -lah")
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertIsNotNone(second.get_node("tree/deep/level3/three.txt"))
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_scripts_and_repl_continue_after_error(self):
        self.assertEqual(self.shell.run_script(
            ROOT / "scripts/stage5_success.txt"), 0)
        self.assertNotIn("must_not_execute", self.output.getvalue())
        self.assertNotIn("error:", self.output.getvalue())
        self.shell.input = io.StringIO("rm missing\nls -lah\nwhoami\nexit\n")
        self.assertEqual(self.shell.run_interactive(), 0)
        self.assertTrue(self.output.getvalue().endswith(
            "Execution finished with errors.\n"))

    def test_os_demonstrations_and_all_sources_unchanged(self):
        sources = list((ROOT / "vfs").glob("*.json"))
        before = {path: path.read_bytes() for path in sources}
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/stage5_all.sh")],
                cwd=directory, capture_output=True, text=True, timeout=20,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Stage 5 scenarios passed.", result.stdout)
        self.assertNotIn("must_not_execute", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(before, {path: path.read_bytes() for path in sources})


if __name__ == "__main__":
    unittest.main()
