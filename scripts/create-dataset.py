import pandas as pd
from pathlib import Path

streets_txt = "singapore-streets.txt"
categories_csv = "street_categories.csv"
osm_streets_csv = "data/singapore-streets.csv"

output_dir = Path("dataset")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "singapore-streets.csv"

streets_df = pd.read_csv(
    streets_txt,
    header=None,
)

categories_df = pd.read_csv(
    categories_csv,
    header=None
)

merged_df = streets_df.merge(
    categories_df,
    on=0,
    how="inner"
)

merged_df = merged_df[[0, 1]]
merged_df.columns = ["street_name", "category"]

osm_streets_df = pd.read_csv(osm_streets_csv)
osm_streets_df = osm_streets_df.rename(columns={"name": "street_name"})

osm_streets_df = osm_streets_df[["street_name", "polyline"]]

merged_df = merged_df.merge(
    osm_streets_df,
    on="street_name",
    how="left"
)

merged_df.to_csv(output_file, index=False)
