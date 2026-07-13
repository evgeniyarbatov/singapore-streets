#!/usr/bin/env python3
"""Categorize Singapore street names using rules and LLM."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from category_overrides import DEFAULT_OVERRIDE_PATH, CategoryOverride, load_overrides
from taxonomy import (
    format_tags,
    get_taxonomy,
    parse_tags,
)

OLLAMA_TIMEOUT_SECONDS = 120
PROMPT_VERSION = "categorize-v1"
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "categorize-v1.md"

OUTPUT_FIELDS = [
    "street_name",
    "primary_category",
    "category",
    "tags",
    "source",
    "prompt_version",
    "model",
    "legacy_category",
]


@dataclass(frozen=True)
class StreetCategory:
    street_name: str
    primary_category: str
    tags: tuple[str, ...]
    source: str
    prompt_version: str = ""
    model: str = ""
    legacy_category: str = ""

    @property
    def category(self) -> str:
        return get_taxonomy().category_name(self.primary_category)


def load_names(input_path: str) -> list[str]:
    names = []
    with open(input_path, encoding="utf-8") as handle:
        for line in handle:
            name = line.strip()
            if name:
                names.append(name)
    return names


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def load_processed(output_path: str) -> dict[str, StreetCategory]:
    processed: dict[str, StreetCategory] = {}
    for row in _read_csv_rows(output_path):
        name = (row.get("street_name") or row.get("name") or "").strip()
        if not name:
            continue

        primary = (row.get("primary_category") or row.get("category") or "").strip()
        if primary and primary not in get_taxonomy().categories:
            resolved = _resolve_category_label(primary)
            primary = resolved.primary_category

        processed[name] = StreetCategory(
            street_name=name,
            primary_category=primary or "uncategorized",
            tags=parse_tags(row.get("tags") or ""),
            source=(row.get("source") or "unknown").strip() or "unknown",
            prompt_version=(row.get("prompt_version") or "").strip(),
            model=(row.get("model") or "").strip(),
            legacy_category=(row.get("legacy_category") or "").strip(),
        )
    return processed


def _resolve_category_label(label: str) -> StreetCategory:
    taxonomy = get_taxonomy()
    normalized = label.strip()
    for category_id, category in taxonomy.categories.items():
        if normalized == category_id or normalized == category.name:
            return StreetCategory(
                street_name="",
                primary_category=category_id,
                tags=(),
                source="legacy",
                legacy_category=label,
            )

    mapped = taxonomy.classify_legacy_label(normalized)
    if mapped:
        return StreetCategory(
            street_name="",
            primary_category=mapped.category_id,
            tags=mapped.tags,
            source="legacy",
            legacy_category=label,
        )

    return StreetCategory(
        street_name="",
        primary_category="uncategorized",
        tags=(),
        source="legacy",
        legacy_category=label,
    )


def build_prompt(street_name: str, prompt_path: Path) -> str:
    taxonomy = get_taxonomy()
    template = prompt_path.read_text(encoding="utf-8")

    category_lines = []
    for category_id in taxonomy.primary_category_ids():
        category = taxonomy.categories[category_id]
        category_lines.append(f"- `{category_id}` — {category.name}: {category.description}")

    tag_lines = []
    for tag_id, tag in taxonomy.tags.items():
        tag_lines.append(f"- `{tag_id}` — {tag.description}")

    return (
        template.replace("{{CATEGORIES}}", "\n".join(category_lines))
        .replace("{{TAGS}}", "\n".join(tag_lines))
        .replace("{{STREET_NAME}}", street_name)
    )


def _extract_json_block(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object in LLM response") from None
        return json.loads(match.group(0))


def categorize_name_llm(
    name: str,
    model: str,
    prompt_path: Path,
) -> StreetCategory:
    prompt = build_prompt(name, prompt_path)
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )
    payload = _extract_json_block(result.stdout)
    taxonomy = get_taxonomy()
    primary = taxonomy.validate_category_id(str(payload.get("primary_category", "")).strip())

    raw_tags = payload.get("tags") or []
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    tags = tuple(
        tag_id for tag_id in (str(tag).strip() for tag in raw_tags) if tag_id in taxonomy.tags
    )

    return StreetCategory(
        street_name=name,
        primary_category=primary,
        tags=tags,
        source="llm",
        prompt_version=PROMPT_VERSION,
        model=model,
    )


def entry_from_override(override: CategoryOverride) -> StreetCategory:
    return StreetCategory(
        street_name=override.street_name,
        primary_category=override.primary_category,
        tags=(),
        source="override",
    )


def classify_street(
    name: str,
    model: str | None,
    prompt_path: Path,
    use_llm: bool,
    overrides: dict[str, CategoryOverride] | None = None,
) -> StreetCategory:
    if overrides and name in overrides:
        return entry_from_override(overrides[name])
    taxonomy = get_taxonomy()
    rule_match = taxonomy.classify_by_rules(name)
    if rule_match:
        return StreetCategory(
            street_name=name,
            primary_category=rule_match.category_id,
            tags=rule_match.tags,
            source="rule",
        )

    if use_llm and model:
        return categorize_name_llm(name, model, prompt_path)

    return StreetCategory(
        street_name=name,
        primary_category="uncategorized",
        tags=(),
        source="uncategorized",
    )


def write_category_row(writer: csv.DictWriter, entry: StreetCategory) -> None:
    writer.writerow(
        {
            "street_name": entry.street_name,
            "primary_category": entry.primary_category,
            "category": entry.category,
            "tags": format_tags(entry.tags),
            "source": entry.source,
            "prompt_version": entry.prompt_version,
            "model": entry.model,
            "legacy_category": entry.legacy_category,
        }
    )


def print_progress(done: int, total: int, name: str, entry: StreetCategory) -> None:
    percent = 100.0 * done / total if total else 100.0
    print(
        f"[{done}/{total}] {percent:5.1f}% {name} -> {entry.category} ({entry.source})",
        file=sys.stderr,
        flush=True,
    )


def parse_args(argv: list[str]) -> dict:
    if len(argv) < 3:
        raise ValueError(
            "Usage: categorize_streets.py <input.txt> <output.csv> "
            "[--model <model>] [--prompt <path>] [--no-llm]"
        )

    options = {
        "input_path": argv[1],
        "output_path": argv[2],
        "model": None,
        "prompt_path": DEFAULT_PROMPT_PATH,
        "override_path": DEFAULT_OVERRIDE_PATH,
        "use_llm": True,
    }

    index = 3
    while index < len(argv):
        flag = argv[index]
        if flag == "--model" and index + 1 < len(argv):
            options["model"] = argv[index + 1]
            index += 2
            continue
        if flag == "--prompt" and index + 1 < len(argv):
            options["prompt_path"] = Path(argv[index + 1])
            index += 2
            continue
        if flag == "--overrides" and index + 1 < len(argv):
            options["override_path"] = Path(argv[index + 1])
            index += 2
            continue
        if flag == "--no-llm":
            options["use_llm"] = False
            index += 1
            continue
        raise ValueError(f"Unknown argument: {flag}")

    if options["use_llm"] and not options["model"]:
        raise ValueError("--model is required unless --no-llm is set")

    return options


def main() -> int:
    try:
        options = parse_args(sys.argv)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    processed = load_processed(options["output_path"])
    overrides = load_overrides(options["override_path"])
    names = load_names(options["input_path"])
    total = len(names)
    already_done = sum(1 for name in names if name in processed and name not in overrides)
    remaining = total - already_done

    print(
        f"Categorizing {remaining} streets "
        f"({already_done}/{total} already done, "
        f"{len(overrides)} overrides, "
        f"model={options['model'] or 'none'}, llm={options['use_llm']})",
        file=sys.stderr,
        flush=True,
    )

    entries: list[StreetCategory] = []
    done = 0
    for name in names:
        if name in overrides:
            entry = entry_from_override(overrides[name])
            entries.append(entry)
            done += 1
            print_progress(done, total, name, entry)
            continue

        if name in processed:
            entry = processed[name]
            entries.append(entry)
            done += 1
            continue

        try:
            entry = classify_street(
                name,
                options["model"],
                options["prompt_path"],
                options["use_llm"],
                overrides=overrides,
            )
        except subprocess.TimeoutExpired:
            entry = StreetCategory(
                street_name=name,
                primary_category="uncategorized",
                tags=(),
                source="llm_timeout",
                prompt_version=PROMPT_VERSION,
                model=options["model"] or "",
            )
            print(
                f"Timed out after {OLLAMA_TIMEOUT_SECONDS}s: {name}",
                file=sys.stderr,
                flush=True,
            )
        except (subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as exc:
            entry = StreetCategory(
                street_name=name,
                primary_category="uncategorized",
                tags=(),
                source="llm_error",
                prompt_version=PROMPT_VERSION,
                model=options["model"] or "",
            )
            print(f"LLM failed for {name}: {exc}", file=sys.stderr, flush=True)

        entries.append(entry)
        done += 1
        print_progress(done, total, name, entry)

    with open(options["output_path"], "w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for entry in entries:
            write_category_row(writer, entry)

    print(f"Done. Categorized {done}/{total} streets.", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
