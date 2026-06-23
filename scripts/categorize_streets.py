#!/usr/bin/env python3
import os
import subprocess
import sys

OLLAMA_TIMEOUT_SECONDS = 120


def load_names(input_path: str) -> list[str]:
    names = []
    with open(input_path, "r", encoding="utf-8") as handle:
        for line in handle:
            name = line.strip()
            if name:
                names.append(name)
    return names


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
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )
    return result.stdout.strip().splitlines()[0].strip()


def print_progress(done: int, total: int, name: str, category: str) -> None:
    percent = 100.0 * done / total if total else 100.0
    print(
        f"[{done}/{total}] {percent:5.1f}% {name} -> {category}",
        file=sys.stderr,
        flush=True,
    )


def main() -> int:
    if len(sys.argv) != 5:
        print(
            "Usage: categorize_streets.py <input.txt> <output.csv> --model <model>",
            file=sys.stderr,
        )
        return 1

    input_path, output_path, model = sys.argv[1], sys.argv[2], sys.argv[4]
    processed = load_processed(output_path)
    names = load_names(input_path)
    total = len(names)
    already_done = sum(1 for name in names if name in processed)
    remaining = total - already_done

    print(
        f"Categorizing {remaining} streets "
        f"({already_done}/{total} already done, model={model})",
        file=sys.stderr,
        flush=True,
    )

    done = already_done
    with open(output_path, "a", encoding="utf-8") as output:
        for name in names:
            if name in processed:
                continue
            try:
                category = categorize_name(name, model)
            except subprocess.TimeoutExpired:
                category = "Uncategorized"
                print(
                    f"Timed out after {OLLAMA_TIMEOUT_SECONDS}s: {name}",
                    file=sys.stderr,
                    flush=True,
                )
            except subprocess.CalledProcessError as exc:
                category = "Uncategorized"
                detail = (exc.stderr or exc.stdout or "").strip()
                print(
                    f"Ollama failed for {name}: {detail or exc}",
                    file=sys.stderr,
                    flush=True,
                )

            if not category:
                category = "Uncategorized"

            output.write(f"{name},{category}\n")
            output.flush()
            processed.add(name)
            done += 1
            print_progress(done, total, name, category)

    print(f"Done. Categorized {done}/{total} streets.", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
