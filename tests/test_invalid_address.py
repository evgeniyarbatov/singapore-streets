import importlib.util
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "invalid-address.py"
MODULE = load_module("invalid_address", SCRIPT_PATH)


class TestInvalidAddress(unittest.TestCase):
    def _run_main(self, tmp_dir, input_data, argv=None):
        filtered_dir = Path(tmp_dir) / "filtered"
        filtered_dir.mkdir(parents=True, exist_ok=True)

        stdin = io.StringIO(input_data)
        stdout = io.StringIO()
        old_stdin = sys.stdin
        old_cwd = os.getcwd()
        old_argv = sys.argv

        try:
            sys.stdin = stdin
            sys.argv = ["invalid-address.py"] + (argv or [])
            os.chdir(tmp_dir)
            with redirect_stdout(stdout):
                MODULE.main()
        finally:
            sys.stdin = old_stdin
            sys.argv = old_argv
            os.chdir(old_cwd)

        return stdout.getvalue()

    def test_main_filters_invalid_lines(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stdout = self._run_main(tmp_dir, "Main Road\nBlk 123\nLorong 12\n")

            self.assertEqual(stdout, "Main Road\n")
            invalid_path = Path(tmp_dir) / "filtered" / "invalid-address.txt"
            self.assertTrue(invalid_path.exists())
            invalid_lines = invalid_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(invalid_lines, ["Blk 123", "Lorong 12"])

    def test_bare_lorong_kept_when_named_variant_present(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stdout = self._run_main(tmp_dir, "Lorong 12\nLorong 12 Geylang\nLorong 99\n")

            self.assertEqual(stdout, "Lorong 12\nLorong 12 Geylang\n")
            invalid_path = Path(tmp_dir) / "filtered" / "invalid-address.txt"
            invalid_lines = invalid_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(invalid_lines, ["Lorong 99"])

    def test_reject_log_flag_overrides_default_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._run_main(
                tmp_dir, "Main Road\nBlk 123\n", argv=["--reject-log", "custom/rejects.txt"]
            )

            custom_path = Path(tmp_dir) / "custom" / "rejects.txt"
            self.assertTrue(custom_path.exists())
            self.assertEqual(custom_path.read_text(encoding="utf-8").splitlines(), ["Blk 123"])


if __name__ == "__main__":
    unittest.main()
