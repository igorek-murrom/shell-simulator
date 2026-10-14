"""Test stage-four commands, scripts, navigation, and source isolation."""

import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shell_emulator.app import ShellEmulator
from shell_emulator.errors import ShellError
from shell_emulator.vfs import VirtualFileSystem


ROOT = Path(__file__).resolve().parents[1]


class StageFourTests(unittest.TestCase):
    """Exercise real commands using a dedicated JSON demonstration tree."""

    def setUp(self):
        """Load an independent VFS and capture command output."""
        self.source = ROOT / "vfs/stage4.json"
        self.original = self.source.read_bytes()
        self.output = io.StringIO()
        self.shell = ShellEmulator(
            vfs=VirtualFileSystem.load(self.source),
            output_stream=self.output,
        )

    def execute(self, line):
        """Return only the output emitted by one command."""
        self.output.seek(0)
        self.output.truncate()
        self.assertFalse(self.shell.execute_line(line))
        return self.output.getvalue()

    def test_ls_modes_and_file_operands(self):
        self.assertEqual(self.execute("ls"),
                         "data.bin\nempty.txt\nfolder\nlines.txt\n")
        self.assertEqual(self.execute("ls -a /"),
                         ".\n..\n.hidden\ndata.bin\nempty.txt\n"
                         "folder\nlines.txt\n")
        self.assertEqual(self.execute('ls "folder/two words.txt"'),
                         "folder/two words.txt\n")
        self.assertEqual(self.execute("ls folder/deep"), "")
        self.assertEqual(self.execute("ls /.hidden"), "/.hidden\n")

    def test_cd_and_relative_commands(self):
        self.execute("cd //folder/./deep/")
        self.assertEqual(self.shell.context.state.cwd, "/folder/deep")
        self.assertEqual(self.execute("ls .."),
                         "-dash.txt\ndeep\ntwo words.txt\n")
        self.assertEqual(self.execute('uniq "../two words.txt"'), "x\ny\n")
        self.execute("cd ../../../../..")
        self.assertEqual(self.shell.context.state.cwd, "/")
        self.execute("cd folder")
        self.execute("cd")
        self.assertEqual(self.shell.context.state.cwd, "/")
        self.execute("cd -- /folder")
        self.assertEqual(self.execute("ls -- -dash.txt"), "-dash.txt\n")
        self.assertEqual(self.execute("uniq -- -dash.txt"), "dash\n")

    def test_failed_cd_preserves_directory(self):
        self.execute("cd folder")
        for path in ("/missing", "/lines.txt", "/lines.txt/..", '""'):
            with self.subTest(path=path), self.assertRaises(ShellError):
                self.shell.execute_line("cd " + path)
            self.assertEqual(self.shell.context.state.cwd, "/folder")

    def test_uniq_modes_preserve_nonadjacent_repeats(self):
        cases = {
            "": "a\nb\na\n\nlast",
            "-c ": "      2 a\n      1 b\n      2 a\n"
                    "      2 \n      1 last",
            "-d ": "a\na\n\n",
            "-u ": "b\nlast",
        }
        for mode, expected in cases.items():
            with self.subTest(mode=mode):
                self.assertEqual(self.execute(f"uniq {mode}lines.txt"),
                                 expected)
        for mode in ("", "-c ", "-d ", "-u "):
            self.assertEqual(self.execute(f"uniq {mode}empty.txt"), "")

    def test_uniq_lf_crlf_unicode_and_unterminated_repeat(self):
        node = self.shell.context.state.vfs.get_node("lines.txt")
        node.content = "ёж\r\nёж\r\nа\u2028б\nа\u2028б".encode()
        self.assertEqual(self.execute("uniq lines.txt"),
                         "ёж\r\nа\u2028б\n")
        node.content = "повтор\nповтор".encode()
        self.assertEqual(self.execute("uniq -d lines.txt"), "повтор\n")

    def test_whoami_uses_os_username(self):
        with patch("shell_emulator.commands.get_username",
                   return_value="test-user"):
            self.assertEqual(self.execute("whoami"), "test-user\n")

    def test_invalid_options_paths_and_arguments(self):
        commands = (
            "ls -z", "ls / /", "ls missing", 'ls ""',
            "ls lines.txt/child", "cd -x", "cd / /", "whoami x",
            "uniq", "uniq lines.txt empty.txt", "uniq -z lines.txt",
            "uniq -c -u lines.txt", "uniq folder", "uniq missing",
            "uniq data.bin", 'uniq ""',
        )
        for line in commands:
            with self.subTest(line=line), self.assertRaises(ShellError):
                self.shell.execute_line(line)

    def test_commands_survive_deleted_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "vfs.json"
            source.write_bytes(self.original)
            self.shell.context.state.vfs = VirtualFileSystem.load(source)
            source.unlink()
            self.execute("cd folder")
            self.execute("ls")
            self.execute('uniq "two words.txt"')
            self.execute("whoami")
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_script_and_interactive_prompts(self):
        with patch("shell_emulator.prompt.get_username", return_value="u"), \
                patch("shell_emulator.prompt.socket.gethostname",
                      return_value="h"):
            result = self.shell.run_script(ROOT / "scripts/stage4_success.txt")
        self.assertEqual(result, 0)
        self.assertIn("u@h:/folder/deep$ ls", self.output.getvalue())
        self.assertNotIn("must_not_execute", self.output.getvalue())
        self.shell.input = io.StringIO("cd missing\nwhoami\nexit\n")
        self.assertEqual(self.shell.run_interactive(), 0)
        self.assertIn("Execution finished with errors.",
                      self.output.getvalue())

    def test_all_demonstrations_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["bash", str(ROOT / "scripts/stage4_all.sh")],
                cwd=directory, capture_output=True, text=True, timeout=20,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Stage 4 scenarios passed.", result.stdout)
        self.assertNotIn("must_not_execute", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(self.source.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
