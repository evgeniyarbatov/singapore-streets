VENV_PATH := .venv

PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
REQUIREMENTS := requirements.txt

SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf

OSM_DIR = osm
SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

TMP_SG_STREETS_FILE = /tmp/singapore-streets.txt
SG_STREETS_FILE = data/singapore-streets.txt

STREET_PATTERN = (avenue$$|boulevard$$|central$$|circle$$|close$$|crescent$$|drive$$|expressway$$|farmway$$|gardens$$|green$$|grove$$|heights$$|hill$$|lane$$|link$$|loop$$|parkway$$|ring$$|rise$$|road$$|square$$|street$$|terrace$$|walk$$|way$$|jalan|lorong)

STREET_FILE        := singapore-streets.txt
CHUNK_DIR          := chunks
LINES_PER_CHUNK    := 25
MODEL              := mistral-nemo:latest

# Core categories (editable)
CATEGORIES := \
  1) Linguistic Origin (Malay, English/British, Chinese, Tamil, etc.) ; \
  2) Historical Themes (colonial figures, local leaders, royalty) ; \
  3) Nature & Geography (trees, plants, animals, landforms) ; \
  4) Cultural & Religious (festivals, concepts, heritage, temples) ; \
  5) Occupational (professions, trades, industries) ; \
  6) Descriptive (colors, shapes, directions, adjectives) ; \
  7) Modern Development (HDB-era names, planning themes, new towns) ; \
  8) Infrastructure & Transport (bridge/port/airport/rail-related) ; \
  9) Numerical or Lettered Names (numbered streets/avenues, alphabet-themed) ; \
  10) International/Foreign References (countries, cities, foreign leaders) ; \
  11) Residential/Community Themes (virtues, values, neighbourhood concepts)

venv:
	@python3 -m venv $(VENV_PATH)

install: venv
	@$(PIP) install --disable-pip-version-check -q --upgrade pip
	@$(PIP) install --disable-pip-version-check -q -r $(REQUIREMENTS)

osm:
	rm -f $(SINGAPORE_OSM_PATH)
	wget $(SINGAPORE_OSM_URL) -P $(OSM_DIR)

city:
	osmconvert $(SINGAPORE_OSM_PATH) -B=$(OSM_DIR)/singapore.poly -o=$(OSM_DIR)/singapore.osm.pbf
	osmium cat --overwrite $(OSM_DIR)/singapore.osm.pbf -o $(OSM_DIR)/singapore.osm

streets:
	$(PYTHON) scripts/extract_streets.py $(OSM_DIR)/singapore.osm data/singapore-streets.csv
	$(PYTHON) -c "import csv; [print(row[0]) for row in csv.reader(open('data/singapore-streets.csv'))][1:]" | sort | uniq > $(SG_STREETS_FILE) 

clean:
	cat data/singapore-streets.txt | \
	$(PYTHON) scripts/format-address.py | \
	$(PYTHON) scripts/invalid-address.py | \
	$(PYTHON) scripts/street-names.py | \
	sort | uniq > singapore-streets.txt

categorize:
	@echo "▶ Starting street name categorization"
	@mkdir -p $(CHUNK_DIR)

	@if [ -z "$$(ls -A $(CHUNK_DIR) 2>/dev/null)" ]; then \
		echo "▶ No chunks found — splitting input file"; \
		split -l $(LINES_PER_CHUNK) $(STREET_FILE) $(CHUNK_DIR)/streets_chunk_; \
		echo "✓ Split into chunks"; \
	else \
		echo "▶ Existing chunks found — resuming from last unprocessed file"; \
	fi

	@for chunk in $(CHUNK_DIR)/streets_chunk_*; do \
		outfile="$(CHUNK_DIR)/category_$$(basename $$chunk).md"; \
		if [ -f "$$outfile" ]; then \
			echo "⏩ Skipping $$chunk (already processed)"; \
			continue; \
		fi; \
		echo "▶ Processing $$chunk..."; \
		ollama run $(MODEL) "\
		Analyze these Singapore street names and categorize them into the following master categories: $(CATEGORIES)\
		\
		Instructions: \
		- Output clean structured markdown. \
		- Use H2 headings for categories (##). \
		- Under each category, list the relevant street names as bullet points with a short explanation (1 sentence). \
		- If a category has no matches, omit it entirely. \
		- Do NOT invent street names. \
		" < $$chunk > $$outfile \
		&& echo "✓ Completed $$chunk" \
		|| { echo "✗ Failed processing $$chunk"; exit 1; }; \
	done

	@echo "▶ Consolidating partial results..."
	@cat $(CHUNK_DIR)/category_*.md > $(CHUNK_DIR)/all_categories.md

	@ollama run $(MODEL) "\
	You will receive fragmented categorization results from batch processing. \
	Please consolidate them into a single, unified markdown document organized strictly by the following categories: $(CATEGORIES)\
	\
	Requirements: \
	- Merge duplicated categories/content. \
	- Deduplicate street names. \
	- Remove contradictory classifications and keep best fit. \
	- Maintain clear, consistent structure with H2 category headings and bullet lists. \
	- Omit categories with no entries. \
	" < $(CHUNK_DIR)/all_categories.md > street_categories.md \
	&& echo '✓ Final consolidation complete' \
	|| { echo '✗ Consolidation failed'; exit 1; }

	@echo "▶ Leaving chunk directory in place so you can resume next time if needed"

.PHONY: venv osm city streets clean categorize

cleanvenv:
	@rm -rf .venv
