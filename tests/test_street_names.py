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


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "street-names.py"
MODULE = load_module("street_names", SCRIPT_PATH)


class TestStreetNames(unittest.TestCase):
    def test_main_filters_street_names(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filtered_dir = Path(tmp_dir) / "filtered"
            filtered_dir.mkdir(parents=True, exist_ok=True)

            input_data = "Orchard Road\nVivoCity Mall\nJalan Besar\nFoo/Bar Road\n"
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

            output_lines = stdout.getvalue().splitlines()
            self.assertEqual(output_lines, ["Orchard Road", "Jalan Besar"])

            filtered_path = filtered_dir / "not-street-names.txt"
            self.assertTrue(filtered_path.exists())
            filtered_lines = filtered_path.read_text(encoding="utf-8").splitlines()
            self.assertTrue(any("VivoCity Mall" in line for line in filtered_lines))
            self.assertTrue(any("Foo/Bar Road" in line for line in filtered_lines))


if __name__ == "__main__":
    unittest.main()
