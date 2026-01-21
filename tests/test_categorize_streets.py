import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import subprocess


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "categorize_streets.py"
MODULE = load_module("categorize_streets", SCRIPT_PATH)


class TestCategorizeStreets(unittest.TestCase):
    def test_load_processed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "output.csv")
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write("Alpha,Category A\n\nInvalidLine\nBeta,Category B\n")

            processed = MODULE.load_processed(output_path)

            self.assertEqual(processed, {"Alpha", "Beta"})

    def test_categorize_name(self):
        with mock.patch.object(MODULE.subprocess, "run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["ollama", "run", "model"],
                returncode=0,
                stdout="Theme One\nTheme Two\n",
            )

            category = MODULE.categorize_name("Sample Street", "model")

            self.assertEqual(category, "Theme One")

    def test_main_appends_new_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.txt")
            output_path = os.path.join(tmp_dir, "output.csv")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("Alpha Street\nBeta Street\n")
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write("Alpha Street,Old Category\n")

            argv = [
                "categorize_streets.py",
                input_path,
                output_path,
                "unused",
                "test-model",
            ]

            with mock.patch.object(MODULE.subprocess, "run") as mocked_run:
                mocked_run.return_value = subprocess.CompletedProcess(
                    args=["ollama", "run", "test-model"],
                    returncode=0,
                    stdout="New Category\n",
                )
                with mock.patch.object(sys, "argv", argv):
                    exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as handle:
                lines = [line.strip() for line in handle if line.strip()]

            self.assertEqual(
                lines,
                ["Alpha Street,Old Category", "Beta Street,New Category"],
            )


if __name__ == "__main__":
    unittest.main()
