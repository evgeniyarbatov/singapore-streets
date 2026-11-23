---
name: pipeline
description: Run the full Singapore streets pipeline end to end (OSM fetch through site build), report what changed, then publish to Kaggle and GitHub Pages after confirmation. Run manually with /pipeline; pass "fresh" to wipe generated data and OSM files first.
disable-model-invocation: true
---

1. If the arguments include `fresh`, run `make reset reset-osm`.
2. Run `make e2e`. If any step fails, stop and report the failing target and its error; don't work around it (e.g. Ollama not running or the model not pulled is yours to report, not fix).
3. Report, reading from the data dir printed by `printf 'pdd: ; @echo $(DATA_DIR)\n' | make -s -f Makefile -f - pdd`:
   - dataset row count vs the street count stated in `README.md`
   - category coverage from `category-stats.json`
   - row count of `review-queue.csv`
   - line counts of `filtered/*.txt`
   - `git status --short` and `git diff --stat` for `site/dist`
4. Ask for confirmation to publish, naming both steps below. Run only the ones confirmed:
   - Kaggle: `make upload`.
   - Pages: commit `site/dist` with `chore: rebuild site`, then `git push origin main`. Skip when `site/dist` has no changes.
5. Report what was published, or that nothing was.

Arguments: $ARGUMENTS
