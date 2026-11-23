---
name: wiki
description: Grow and maintain the Singapore streets wiki in wiki/, following wiki/SCHEMA.md. Run manually with /wiki [ingest N | query "<question>" | lint]; no argument means ingest 5.
disable-model-invocation: true
---

Read `wiki/SCHEMA.md` and follow it for everything below. Run `make wiki-facts` first; if it fails because the dataset is missing, stop and say to run `/pipeline`.

The facts file is `wiki-facts.json` in the data dir printed by `printf 'pdd: ; @echo $(DATA_DIR)\n' | make -s -f Makefile -f - pdd`.

## ingest N

1. List gaps: elements, series, families and categories in the facts file with no page yet, plus people and streets named in existing pages' sources but with no page. Rank by how many streets a page would explain; prefer elements and categories while fewer than ten of each exist.
2. Take the top N. For each, research on the web, then write the page. Drop a candidate whose meaning or origin you cannot source, and say so in the report.
3. Add a street or person page only when research turned up its sourced history.
4. Add links to the new pages from existing pages that mention them, and add the pages to `index.md`. Keep up to five pages under Start here, chosen to give a newcomer the widest view.
5. Append to `log.md`: `## <date> ingest` then one line per page written or changed.

## query "<question>"

Answer from the wiki, citing pages with wikilinks. If the wiki can't answer, say what is missing. If the answer finds a pattern with no page yet, offer to file it as a pattern page; write it only on a yes. Log the question and any page written.

## lint

Check and fix, then log what changed:
- wikilinks to missing pages, and pages no other page links to
- streets named in pages that are not in the facts file
- counts or street lists that differ from the facts file
- claims without a footnote, and footnotes whose URL no longer loads
- contradictions between pages
- street pages without sourced history (delete them and unlink)

Report the pages written, changed or deleted, and the candidates dropped and why.

Arguments: $ARGUMENTS
