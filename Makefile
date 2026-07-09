# Uses uv (https://docs.astral.sh/uv) for dependency management — uv sync creates/updates .venv; run commands via uv run, no manual activation.
PYTHON := uv run python

OSM_DIR = osm
SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf
OSM_URL = $(SINGAPORE_OSM_URL)
include $(HOME)/gitRepo/dotfiles/make/osm-country.mk
SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

OSM_STREETS_FILE = data/osm-streets.csv
STREET_NAMES_FILE = data/street-names.txt
STREET_CATEGORIES_FILE = data/street_categories.csv
REVIEW_QUEUE_FILE = data/review-queue.csv
CANONICAL_STREETS_FILE = data/canonical-streets.csv
CATEGORY_STATS_FILE = data/category-stats.json
DATASET_FILE = dataset/singapore-streets.csv
ALLOWLIST_FILE = data/allowlist.txt
INVALID_ADDRESS_LOG = filtered/invalid-address.txt
NOT_STREET_NAMES_LOG = filtered/not-street-names.txt
SINGAPORE_OSM_XML = $(OSM_DIR)/singapore.osm
SINGAPORE_OSM_CLIPPED = $(OSM_DIR)/singapore.osm.pbf

GENERATED_DATA = \
	$(OSM_STREETS_FILE) \
	$(STREET_NAMES_FILE) \
	$(STREET_CATEGORIES_FILE) \
	$(REVIEW_QUEUE_FILE) \
	$(CANONICAL_STREETS_FILE) \
	$(CATEGORY_STATS_FILE) \
	$(DATASET_FILE)

MODEL = mistral-nemo:latest

install:
	@uv sync

osm: osm-country-fetch

city:
	@osmconvert $(SINGAPORE_OSM_PATH) \
	-B=$(OSM_DIR)/singapore.poly \
	-o=$(OSM_DIR)/singapore.osm.pbf

	@osmium cat --overwrite \
	$(SINGAPORE_OSM_CLIPPED) \
	-o $(SINGAPORE_OSM_XML)

streets: install
	@$(PYTHON) scripts/extract_streets.py \
	$(SINGAPORE_OSM_XML) \
	$(OSM_STREETS_FILE) \
	$(STREET_NAMES_FILE) \
	$(REVIEW_QUEUE_FILE)
clean:
	@tmp="$$(mktemp)"; \
	cat $(STREET_NAMES_FILE) | \
	$(PYTHON) scripts/format-address.py | \
	$(PYTHON) scripts/invalid-address.py --reject-log $(INVALID_ADDRESS_LOG) | \
	$(PYTHON) scripts/street-names.py --reject-log $(NOT_STREET_NAMES_LOG) --allowlist $(ALLOWLIST_FILE) | \
	sort | uniq > "$$tmp"; \
	mv "$$tmp" $(STREET_NAMES_FILE)

canonical: install
	@$(PYTHON) scripts/canonical_streets.py \
	$(STREET_NAMES_FILE) \
	$(CANONICAL_STREETS_FILE)
categorize: install
	@$(PYTHON) scripts/categorize_streets.py \
	$(STREET_NAMES_FILE) \
	$(STREET_CATEGORIES_FILE) \
	--model $(MODEL)
category-report: install
	@$(PYTHON) scripts/category_report.py
dataset: install
	@$(PYTHON) scripts/create-dataset.py
upload:
	@kaggle datasets version -p dataset -m "update dataset"

test: install
	@$(PYTHON) -m unittest discover -s tests
all: streets clean canonical categorize category-report dataset

reset:
	@rm -f $(GENERATED_DATA)
	@rm -rf filtered

reset-osm:
	@rm -f $(SINGAPORE_OSM_PATH) $(SINGAPORE_OSM_CLIPPED) $(SINGAPORE_OSM_XML)

fresh: reset all

fresh-all: reset reset-osm osm city all

lock:
	@uv lock

help:
	@echo "install         - uv sync dependencies"
	@echo "osm             - fetch country OSM extract"
	@echo "city            - clip OSM extract to city bounds"
	@echo "streets         - extract streets from OSM data"
	@echo "clean           - dedupe/normalize street names"
	@echo "canonical       - build canonical streets file"
	@echo "categorize      - categorize streets with the model"
	@echo "category-report - print category stats"
	@echo "dataset         - build the final dataset"
	@echo "upload          - push dataset to Kaggle"
	@echo "test            - run unit tests"
	@echo "all             - streets, clean, canonical, categorize, category-report, dataset"
	@echo "reset           - remove generated data"
	@echo "reset-osm       - remove downloaded/converted OSM files"
	@echo "fresh           - reset + all"
	@echo "fresh-all       - reset, reset-osm, osm, city, all"
	@echo "lock            - update uv.lock"

.PHONY: install osm city streets clean canonical categorize category-report dataset upload test all reset reset-osm fresh fresh-all lock help
