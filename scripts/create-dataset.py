import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from category_overrides import merge_category_dataframe

streets_txt = "data/street-names.txt"
categories_csv = "data/street_categories.csv"
osm_streets_csv = "data/osm-streets.csv"

output_dir = Path("dataset")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "singapore-streets.csv"

streets_df = pd.read_csv(
    streets_txt,
    header=None,
)

categories_df = pd.read_csv(categories_csv)
if "street_name" in categories_df.columns:
    category_col = "category" if "category" in categories_df.columns else "primary_category"
    categories_df = categories_df[["street_name", category_col]].rename(
        columns={category_col: "category"}
    )
else:
    categories_df = pd.read_csv(categories_csv, header=None)
    categories_df = categories_df[[0, 1]]
    categories_df.columns = pd.Index(["street_name", "category"])

categories_df = merge_category_dataframe(categories_df)

merged_df = streets_df.merge(
    categories_df,
    left_on=0,
    right_on="street_name",
    how="inner",
)

osm_streets_df = pd.read_csv(osm_streets_csv)
osm_streets_df = osm_streets_df.rename(columns={"name": "street_name"})

osm_streets_df = osm_streets_df[["street_name", "polyline"]]

merged_df = merged_df.merge(osm_streets_df, on="street_name", how="left")

merged_df = merged_df[["street_name", "category", "polyline"]]
merged_df.to_csv(output_file, index=False)
