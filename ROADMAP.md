# Singapore Streets — Roadmap

## Vision

A **living catalog** of Singapore street names where every name can be found, understood, and revisited, not just counted. Street names compress a place's history (colonial officials, Malay place-words, clan links, vanished kampungs, developer flourishes), and this project turns ~4,700 of them into something you can wander through.

Once the pipeline (extract → categorize → enrich → publish) is proven here, it is a template for other cities whose street names carry history, such as Saigon's post-1975 renamings or Hanoi's naming logic.

## Where We Are

Extraction from OSM, a stable 12-category taxonomy (99.8% coverage), the Kaggle dataset, a public map site, and CI are in place. What remains is making the list **complete**, the names **meaningful**, the site **personal**, and the pipeline **self-refreshing**.

## Themes

### Completeness

Know what the OSM list is missing by diffing it against official sources (OneMap, data.gov.sg, URA), and settle the gray zone of private estates, orphan lorongs and expressways with an explicit confidence signal. Track progress in [#6](https://github.com/evgeniyarbatov/singapore-streets/issues/6).

### Enrichment

Give every street a district and as many as possible a sourced etymology, language of origin, era and former names. Publish the aliases and tags the pipeline already produces. Curate notable lists, such as streets that no longer exist, the longest names and the best for running. The first step is [#9](https://github.com/evgeniyarbatov/singapore-streets/issues/9).

### Memory lane

Make the catalog personal: private notes on visited and run streets ([#7](https://github.com/evgeniyarbatov/singapore-streets/issues/7)), and site features that invite recall, such as a random street, a quiz, a running map, and a comparison of old and new names ([#10](https://github.com/evgeniyarbatov/singapore-streets/issues/10)). Later: "streets near me", offline/PWA use, flashcards before a trip.

### Living catalog

Keep the data fresh without effort: scheduled OSM refreshes that surface what changed ([#11](https://github.com/evgeniyarbatov/singapore-streets/issues/11)), versioned dataset releases with generated release notes, and a golden-file regression test on a small OSM snippet. Tidy the code as friction shows up ([#8](https://github.com/evgeniyarbatov/singapore-streets/issues/8), [#5](https://github.com/evgeniyarbatov/singapore-streets/issues/5)).

### Contributions

Let others fix a category, add a missing street or source an etymology without touching Python, through a contributing guide, issue templates and clear OSM/URA/SLA licensing.

## Milestones

| Milestone | Target |
|-----------|--------|
| **Complete list** | ≤50 streets unexplained gap vs the best official source |
| **Story-ready** | 500 streets with a sourced etymology |
| **Personal** | Local site shows your own notes and routes |
| **Living catalog** | Quarterly refresh runs unattended and reports what changed |

## Open Questions

- **Scope:** Include expressways (`PIE`, `ECP`) and major bridges, or only traditional streets?
- **Historical streets:** Track renamed and extinct streets as a separate table?
- **Languages:** Store official Chinese/Malay/Tamil forms alongside the English display name?
- **Publishing:** Is Kaggle still the primary target, or GitHub Releases plus the site?

## References

- [URA — Singapore Street, Building and Place Names](https://www.ura.gov.sg/Corporate/Resources/Publications/Books/Book-Details/Singapore-Street-Building-Place-Names)
- [NLB — History of street names in Singapore](https://www.nlb.gov.sg/main/article-detail?cmsuuid=4d8269aa-4464-40f5-8193-10b16a13eeea)
- [Roots.gov.sg — Street names in Singapore](https://www.roots.gov.sg/stories-landing/stories/street-names-in-singapore/story)
- [Remember Singapore — Street suffixes](https://remembersingapore.org/2018/08/15/singapore-street-suffixes/)
- [Wikipedia — Road names in Singapore](https://en.wikipedia.org/wiki/Road_names_in_Singapore)
- [OpenStreetMap Wiki — Singapore](https://wiki.openstreetmap.org/wiki/Singapore)
- Victor R. Savage & Brenda S. A. Yeoh, *Singapore Street Names: A Study of Toponymics*
