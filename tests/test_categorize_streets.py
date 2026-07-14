from __future__ import annotations

import csv
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "categorize_streets.py"
MODULE = load_module("categorize_streets", SCRIPT_PATH)
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "taxonomy.yaml"


class TestCategorizeStreets(unittest.TestCase):
    def setUp(self) -> None:
        MODULE.get_taxonomy(TAXONOMY_PATH)

    def test_load_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.txt")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("Alpha Street\n\nBeta Street\n")

            names = MODULE.load_names(input_path)

            self.assertEqual(names, ["Alpha Street", "Beta Street"])

    def test_load_processed_reads_new_csv_format(self) -> None:
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

    def test_classify_street_uses_rules_without_llm(self) -> None:
        entry = MODULE.classify_street(
            "Jalan Besar",
            model=None,
            prompt_path=MODULE.DEFAULT_PROMPT_PATH,
            use_llm=False,
        )
        self.assertEqual(entry.primary_category, "malay_archipelago")
        self.assertEqual(entry.source, "rule")

    def test_categorize_name_llm_parses_json(self) -> None:
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

    def test_classify_street_uses_override_before_rules(self) -> None:
        overrides = {
            "Jalan Besar": MODULE.CategoryOverride(
                street_name="Jalan Besar",
                primary_category="nature_geography",
            )
        }

        entry = MODULE.classify_street(
            "Jalan Besar",
            model=None,
            prompt_path=MODULE.DEFAULT_PROMPT_PATH,
            use_llm=False,
            overrides=overrides,
        )

        self.assertEqual(entry.primary_category, "nature_geography")
        self.assertEqual(entry.source, "override")

    def test_main_appends_new_entries_with_rules(self) -> None:
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

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(sys, "stderr", new_callable=io.StringIO),
            ):
                exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            with open(output_path, encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["street_name"], "Jalan Besar")
            self.assertEqual(rows[1]["street_name"], "Beta Street")

    def test_main_applies_override_to_existing_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.txt")
            output_path = os.path.join(tmp_dir, "output.csv")
            override_path = os.path.join(tmp_dir, "overrides.csv")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("Adam Drive\n")
            with open(output_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MODULE.OUTPUT_FIELDS)
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Adam Drive",
                        "primary_category": "housing_development",
                        "category": "Housing & Development",
                        "tags": "estate",
                        "source": "llm",
                        "prompt_version": "categorize-v1",
                        "model": "mistral-nemo:latest",
                        "legacy_category": "",
                    }
                )
            with open(override_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["street_name", "category"])
                writer.writeheader()
                writer.writerow(
                    {
                        "street_name": "Adam Drive",
                        "category": "commemorative_persons",
                    }
                )

            argv = [
                "categorize_streets.py",
                input_path,
                output_path,
                "--no-llm",
                "--overrides",
                override_path,
            ]

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(sys, "stderr", new_callable=io.StringIO),
            ):
                exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            with open(output_path, encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["primary_category"], "commemorative_persons")
            self.assertEqual(rows[0]["source"], "override")


if __name__ == "__main__":
    unittest.main()
