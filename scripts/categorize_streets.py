#!/usr/bin/env python3
import os
import subprocess
import sys


def load_processed(output_path: str) -> set[str]:
    if not os.path.exists(output_path):
        return set()
    processed = set()
    with open(output_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if "," not in line:
                continue
            name, _category = line.split(",", 1)
            name = name.strip()
            if name:
                processed.add(name)
    return processed


def categorize_name(name: str, model: str) -> str:
    prompt = (
        "Given this Singapore street name, output a concise category label (2-5 words) "
        "describing its theme. Be specific and create a new category if appropriate. "
        "Output only the category label, with no extra text or punctuation.\n"
        f"Street: {name}\n"
    )
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip().splitlines()[0].strip()


def main() -> int:
    if len(sys.argv) != 5 or sys.argv[3] != "--model":
        print("Usage: categorize_streets.py <input.txt> <output.csv> --model <model>")
        return 1

    input_path, output_path, model = sys.argv[1], sys.argv[2], sys.argv[4]
    processed = load_processed(output_path)

    with open(input_path, "r", encoding="utf-8") as handle, open(
        output_path, "a", encoding="utf-8"
    ) as output:
        for line in handle:
            name = line.strip()
            if not name or name in processed:
                continue
            category = categorize_name(name, model)
            if not category:
                category = "Uncategorized"
            output.write(f"{name},{category}\n")
            output.flush()
            processed.add(name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
