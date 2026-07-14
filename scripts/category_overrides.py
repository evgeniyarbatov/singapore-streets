"""Load manual category overrides from data/categories-override.csv."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from taxonomy import get_taxonomy

if TYPE_CHECKING:
    import pandas as pd

DEFAULT_OVERRIDE_PATH = Path(__file__).resolve().parents[1] / "data" / "categories-override.csv"

OVERRIDE_FIELDS = ["street_name", "category"]


@dataclass(frozen=True)
class CategoryOverride:
    street_name: str
    primary_category: str


def _resolve_category(label: str) -> str:
    taxonomy = get_taxonomy()
    normalized = label.strip()
    if not normalized:
        return "uncategorized"

    if normalized in taxonomy.categories:
        return normalized

    for category_id, category in taxonomy.categories.items():
        if normalized == category.name:
            return category_id

    return taxonomy.validate_category_id(normalized)


def load_overrides(path: str | Path | None = None) -> dict[str, CategoryOverride]:
    override_path = Path(path) if path else DEFAULT_OVERRIDE_PATH
    if not override_path.exists():
        return {}

    overrides: dict[str, CategoryOverride] = {}
    with open(override_path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = (row.get("street_name") or "").strip()
            category = (row.get("category") or "").strip()
            if not name or not category:
                continue

            overrides[name] = CategoryOverride(
                street_name=name,
                primary_category=_resolve_category(category),
            )

    return overrides


def apply_overrides_to_rows(
    rows: list[dict[str, str]],
    overrides: dict[str, CategoryOverride] | None = None,
    *,
    override_path: str | Path | None = None,
) -> list[dict[str, str]]:
    taxonomy = get_taxonomy()
    resolved_overrides = overrides if overrides is not None else load_overrides(override_path)
    if not resolved_overrides:
        return rows

    by_name = {
        (row.get("street_name") or row.get("name") or "").strip(): dict(row)
        for row in rows
        if (row.get("street_name") or row.get("name") or "").strip()
    }

    for name, override in resolved_overrides.items():
        row = by_name.get(name, {"street_name": name})
        row["street_name"] = name
        row["primary_category"] = override.primary_category
        row["category"] = taxonomy.category_name(override.primary_category)
        row["tags"] = ""
        row["source"] = "override"
        row["prompt_version"] = ""
        row["model"] = ""
        row["legacy_category"] = ""
        by_name[name] = row

    return list(by_name.values())


def merge_category_dataframe(
    categories_df: pd.DataFrame, overrides: dict[str, CategoryOverride] | None = None
) -> pd.DataFrame:
    """Return categories_df with override rows replacing matching street_name rows."""
    import pandas as pd

    resolved_overrides = overrides if overrides is not None else load_overrides()
    if not resolved_overrides:
        return categories_df

    taxonomy = get_taxonomy()
    override_rows = [
        {
            "street_name": name,
            "category": taxonomy.category_name(override.primary_category),
        }
        for name, override in resolved_overrides.items()
    ]
    override_df = pd.DataFrame(override_rows)
    filtered = categories_df[~categories_df["street_name"].isin(override_df["street_name"])]
    return pd.concat([filtered, override_df], ignore_index=True)
