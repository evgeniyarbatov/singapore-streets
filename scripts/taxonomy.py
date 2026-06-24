#!/usr/bin/env python3
"""Load and apply the stable street-name taxonomy."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "taxonomy.yaml"
UNCATEGORIZED_ID = "uncategorized"


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    description: str
    examples: tuple[str, ...]


@dataclass(frozen=True)
class SecondaryTag:
    id: str
    description: str


@dataclass(frozen=True)
class Classification:
    category_id: str
    tags: tuple[str, ...] = ()
    source: str = "rule"

    @property
    def category_name(self) -> str:
        return category_id_to_name(self.category_id)


@dataclass
class Taxonomy:
    version: int
    categories: dict[str, Category]
    tags: dict[str, SecondaryTag]
    rules: list[tuple[re.Pattern[str], str, tuple[str, ...]]]
    legacy_mappings: list[tuple[re.Pattern[str], str, tuple[str, ...]]]
    colonial_surnames: tuple[re.Pattern[str], ...]

    def category_name(self, category_id: str) -> str:
        if category_id not in self.categories:
            return self.categories[UNCATEGORIZED_ID].name
        return self.categories[category_id].name

    def validate_category_id(self, category_id: str) -> str:
        if category_id in self.categories:
            return category_id
        return UNCATEGORIZED_ID

    def primary_category_names(self) -> list[str]:
        return [
            category.name
            for category_id, category in self.categories.items()
            if category_id != UNCATEGORIZED_ID
        ]

    def primary_category_ids(self) -> list[str]:
        return [
            category_id
            for category_id in self.categories
            if category_id != UNCATEGORIZED_ID
        ]

    def classify_by_rules(self, street_name: str) -> Classification | None:
        for pattern, category_id, tags in self.rules:
            if pattern.search(street_name):
                return Classification(category_id=category_id, tags=tags, source="rule")

        for pattern in self.colonial_surnames:
            if pattern.search(street_name):
                return Classification(
                    category_id="colonial_british",
                    tags=("person",),
                    source="rule",
                )

        return None

    def classify_legacy_label(self, legacy_label: str) -> Classification | None:
        normalized = legacy_label.strip()
        if not normalized:
            return None

        for pattern, category_id, tags in self.legacy_mappings:
            if pattern.search(normalized):
                return Classification(
                    category_id=category_id,
                    tags=tags,
                    source="legacy",
                )

        return None


def _compile_patterns(patterns: list[str]) -> re.Pattern[str]:
    combined = "|".join(f"(?:{pattern})" for pattern in patterns)
    return re.compile(combined, re.IGNORECASE)


def _compile_word_pattern(word: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)


def load_taxonomy(path: str | Path | None = None) -> Taxonomy:
    taxonomy_path = Path(path) if path else DEFAULT_TAXONOMY_PATH
    with open(taxonomy_path, "r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)

    categories = {}
    for entry in raw.get("primary_categories", []):
        categories[entry["id"]] = Category(
            id=entry["id"],
            name=entry["name"],
            description=(entry.get("description") or "").strip(),
            examples=tuple(entry.get("examples") or []),
        )

    tags = {}
    for entry in raw.get("secondary_tags", []):
        tags[entry["id"]] = SecondaryTag(
            id=entry["id"],
            description=(entry.get("description") or "").strip(),
        )

    rules = []
    for entry in raw.get("rules", []):
        patterns = entry.get("patterns") or []
        if not patterns:
            continue
        rules.append(
            (
                _compile_patterns(patterns),
                entry["category"],
                tuple(entry.get("tags") or []),
            )
        )

    legacy_mappings = []
    for entry in raw.get("legacy_label_mappings", []):
        patterns = entry.get("patterns") or []
        if not patterns:
            continue
        legacy_mappings.append(
            (
                _compile_patterns(patterns),
                entry["category"],
                tuple(entry.get("tags") or []),
            )
        )

    colonial_surnames = tuple(
        _compile_word_pattern(word) for word in raw.get("colonial_surnames", [])
    )

    return Taxonomy(
        version=int(raw.get("version", 1)),
        categories=categories,
        tags=tags,
        rules=rules,
        legacy_mappings=legacy_mappings,
        colonial_surnames=colonial_surnames,
    )


_TAXONOMY: Taxonomy | None = None


def get_taxonomy(path: str | Path | None = None) -> Taxonomy:
    global _TAXONOMY
    if path is not None:
        return load_taxonomy(path)
    if _TAXONOMY is None:
        _TAXONOMY = load_taxonomy()
    return _TAXONOMY


def category_id_to_name(category_id: str, taxonomy: Taxonomy | None = None) -> str:
    tax = taxonomy or get_taxonomy()
    return tax.category_name(category_id)


def format_tags(tags: tuple[str, ...] | list[str]) -> str:
    return "|".join(tags)


def parse_tags(raw: str) -> tuple[str, ...]:
    if not raw or not raw.strip():
        return ()
    return tuple(part.strip() for part in raw.split("|") if part.strip())