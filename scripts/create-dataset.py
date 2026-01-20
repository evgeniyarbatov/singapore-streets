import pandas as pd
from pathlib import Path

streets_txt = "singapore-streets.txt"
categories_csv = "street_categories.csv"

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

merged_df.to_csv(output_file, index=False)
