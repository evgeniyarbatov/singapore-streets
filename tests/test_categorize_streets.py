import importlib.util
import csv
import io
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
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "categorize_streets.py"
MODULE = load_module("categorize_streets", SCRIPT_PATH)
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "taxonomy.yaml"


class TestCategorizeStreets(unittest.TestCase):
    def setUp(self):
        MODULE.get_taxonomy(TAXONOMY_PATH)

    def test_load_names(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.txt")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("Alpha Street\n\nBeta Street\n")

            names = MODULE.load_names(input_path)

            self.assertEqual(names, ["Alpha Street", "Beta Street"])

    def test_load_processed_reads_new_csv_format(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "output.csv")
            with open(output_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MODULE.OUTPUT_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Jalan Besar",
                        "primary_category": "malay_archipelago",
                        "category": "Malay & Archipelago",
                        "tags": "",
                        "source": "rule",
                        "prompt_version": "",
                        "model": "",
                        "legacy_category": "",
                    }
                )

            processed = MODULE.load_processed(output_path)

            self.assertIn("Jalan Besar", processed)
            self.assertEqual(processed["Jalan Besar"].primary_category, "malay_archipelago")

    def test_classify_street_uses_rules_without_llm(self):
        entry = MODULE.classify_street(
            "Jalan Besar",
            model=None,
            prompt_path=MODULE.DEFAULT_PROMPT_PATH,
            use_llm=False,
        )
        self.assertEqual(entry.primary_category, "malay_archipelago")
        self.assertEqual(entry.source, "rule")

    def test_categorize_name_llm_parses_json(self):
        with mock.patch.object(MODULE.subprocess, "run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["ollama", "run", "model"],
                returncode=0,
                stdout='{"primary_category": "nature_geography", "tags": ["tree"], "confidence": "high"}',
            )

            entry = MODULE.categorize_name_llm(
                "Mount Pleasant Road",
                "model",
                MODULE.DEFAULT_PROMPT_PATH,
            )

            self.assertEqual(entry.primary_category, "nature_geography")
            self.assertEqual(entry.tags, ("tree",))
            self.assertEqual(entry.source, "llm")

    def test_main_appends_new_entries_with_rules(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.txt")
            output_path = os.path.join(tmp_dir, "output.csv")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("Jalan Besar\nBeta Street\n")
            with open(output_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MODULE.OUTPUT_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Jalan Besar",
                        "primary_category": "malay_archipelago",
                        "category": "Malay & Archipelago",
                        "tags": "",
                        "source": "rule",
                        "prompt_version": "",
                        "model": "",
                        "legacy_category": "",
                    }
                )

            argv = [
                "categorize_streets.py",
                input_path,
                output_path,
                "--no-llm",
            ]

            with mock.patch.object(sys, "argv", argv):
                with mock.patch.object(sys, "stderr", new_callable=io.StringIO):
                    exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["street_name"], "Jalan Besar")
            self.assertEqual(rows[1]["street_name"], "Beta Street")


if __name__ == "__main__":
    unittest.main()