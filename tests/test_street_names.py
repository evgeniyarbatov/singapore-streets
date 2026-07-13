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
            sys.argv = ["street-names.py"] + (argv or [])
            os.chdir(tmp_dir)
            with redirect_stdout(stdout):
                MODULE.main()
        finally:
            sys.stdin = old_stdin
            sys.argv = old_argv
            os.chdir(old_cwd)

        return stdout.getvalue()

    def test_main_filters_street_names(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stdout = self._run_main(
                tmp_dir, "Orchard Road\nVivoCity Mall\nJalan Besar\nFoo/Bar Road\n"
            )

            output_lines = stdout.splitlines()
            self.assertEqual(output_lines, ["Orchard Road", "Jalan Besar"])

            filtered_path = Path(tmp_dir) / "filtered" / "not-street-names.txt"
            self.assertTrue(filtered_path.exists())
            filtered_lines = filtered_path.read_text(encoding="utf-8").splitlines()
            self.assertTrue(any("VivoCity Mall" in line for line in filtered_lines))
            self.assertTrue(any("Foo/Bar Road" in line for line in filtered_lines))

    def test_reject_log_flag_overrides_default_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._run_main(
                tmp_dir,
                "Orchard Road\nVivoCity Mall\n",
                argv=["--reject-log", "custom/rejects.txt"],
            )

            custom_path = Path(tmp_dir) / "custom" / "rejects.txt"
            self.assertTrue(custom_path.exists())
            self.assertTrue(
                any(
                    "VivoCity Mall" in line
                    for line in custom_path.read_text(encoding="utf-8").splitlines()
                )
            )

    def test_allowlist_bypasses_slash_and_building_filters(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            allowlist_path = Path(tmp_dir) / "allowlist.txt"
            allowlist_path.write_text("Foo/Bar Road\n", encoding="utf-8")

            stdout = self._run_main(
                tmp_dir,
                "Orchard Road\nFoo/Bar Road\n",
                argv=["--allowlist", str(allowlist_path)],
            )

            self.assertEqual(stdout.splitlines(), ["Orchard Road", "Foo/Bar Road"])

    def test_expanded_suffixes_are_kept(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stdout = self._run_main(tmp_dir, "Marina Quay\nRaffles Place\nBukit Timah\n")

            self.assertEqual(stdout.splitlines(), ["Marina Quay", "Raffles Place", "Bukit Timah"])


if __name__ == "__main__":
    unittest.main()
