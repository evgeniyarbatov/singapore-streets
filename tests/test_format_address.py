import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "format-address.py"
MODULE = load_module("format_address", SCRIPT_PATH)


class TestFormatAddress(unittest.TestCase):
    def test_format_replacements(self):
        text = "123 rd &apos;test’ jln lor ave blvd bt aft bef"
        formatted = MODULE.format(text)
        self.assertEqual(
            formatted,
            "123 Road &Apos;Test' Jalan Lorong Avenue Boulevard Bukit After Before",
        )

    def test_main_formats_lines(self):
        input_data = "foo rd\nbar st\n"
        expected_output = "Foo Road\nBar Street\n"

        stdin = io.StringIO(input_data)
        stdout = io.StringIO()
        old_stdin = sys.stdin
        try:
            sys.stdin = stdin
            with redirect_stdout(stdout):
                MODULE.main()
        finally:
            sys.stdin = old_stdin

        self.assertEqual(stdout.getvalue(), expected_output)


if __name__ == "__main__":
    unittest.main()
