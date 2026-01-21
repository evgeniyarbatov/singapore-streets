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
    def test_main_filters_invalid_lines(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filtered_dir = Path(tmp_dir) / "filtered"
            filtered_dir.mkdir(parents=True, exist_ok=True)

            input_data = "Main Road\nBlk 123\nLorong 12\n"
            stdin = io.StringIO(input_data)
            stdout = io.StringIO()
            old_stdin = sys.stdin
            old_cwd = os.getcwd()

            try:
                sys.stdin = stdin
                os.chdir(tmp_dir)
                with redirect_stdout(stdout):
                    MODULE.main()
            finally:
                sys.stdin = old_stdin
                os.chdir(old_cwd)

            self.assertEqual(stdout.getvalue(), "Main Road\n")
            invalid_path = filtered_dir / "invalid-address.txt"
            self.assertTrue(invalid_path.exists())
            invalid_lines = invalid_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(invalid_lines, ["Blk 123", "Lorong 12"])


if __name__ == "__main__":
    unittest.main()
