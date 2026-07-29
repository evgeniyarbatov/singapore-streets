# Uses uv (https://docs.astral.sh/uv) for dependency management — uv sync creates/updates .venv; run commands via uv run, no manual activation.
PYTHON := uv run python

DATA_ROOT ?= $(HOME)/data
REPO_NAME := $(notdir $(CURDIR))
DATA_DIR  ?= $(DATA_ROOT)/$(REPO_NAME)

OSM_DIR := $(DATA_DIR)/osm
SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf
OSM_URL = $(SINGAPORE_OSM_URL)

DOTFILES_MK := $(HOME)/gitRepo/dotfiles/make/osm-country.mk

.PHONY: country osm-country-fetch

ifneq ($(wildcard $(DOTFILES_MK)),)
include $(DOTFILES_MK)
else
COUNTRY_OSM_FILE ?= $(notdir $(OSM_URL))

country osm-country-fetch:
	@echo "error: '$@' needs evgeniyarbatov/dotfiles (private helper); not found at $(DOTFILES_MK)." >&2
	@echo "Fetch manually: download $(OSM_URL) into $(OSM_DIR)/$(COUNTRY_OSM_FILE), then retry." >&2
	@exit 1
endif

SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

# Tracked in git (osm/singapore.poly); kept at its repo path, independent of OSM_DIR.
SINGAPORE_POLY_FILE := osm/singapore.poly

OSM_STREETS_FILE = $(DATA_DIR)/osm-streets.csv
STREET_NAMES_FILE = $(DATA_DIR)/street-names.txt
STREET_CATEGORIES_FILE = $(DATA_DIR)/street_categories.csv
REVIEW_QUEUE_FILE = $(DATA_DIR)/review-queue.csv
CANONICAL_STREETS_FILE = $(DATA_DIR)/canonical-streets.csv
CATEGORY_STATS_FILE = $(DATA_DIR)/category-stats.json
DATASET_FILE = $(DATA_DIR)/dataset/singapore-streets.csv
ALLOWLIST_FILE = data/allowlist.txt
INVALID_ADDRESS_LOG = $(DATA_DIR)/filtered/invalid-address.txt
NOT_STREET_NAMES_LOG = $(DATA_DIR)/filtered/not-street-names.txt
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

# GitHub Pages project site base path. Use SITE_BASE=/ for local root serve.
SITE_BASE ?= /singapore-streets/
SITE_DIST = site/dist
SITE_PORT ?= 8000

install:
	@uv sync

osm: osm-country-fetch

city:
	@mkdir -p $(OSM_DIR)
	@osmconvert $(SINGAPORE_OSM_PATH) \
	-B=$(SINGAPORE_POLY_FILE) \
	-o=$(OSM_DIR)/singapore.osm.pbf

	@osmium cat --overwrite \
	$(SINGAPORE_OSM_CLIPPED) \
	-o $(SINGAPORE_OSM_XML)

streets: install
	@mkdir -p $(DATA_DIR)
	@$(PYTHON) scripts/extract_streets.py \
	$(SINGAPORE_OSM_XML) \
	$(OSM_STREETS_FILE) \
	$(STREET_NAMES_FILE) \
	$(REVIEW_QUEUE_FILE)
clean: install
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
	@$(PYTHON) scripts/category_report.py \
	--input $(STREET_CATEGORIES_FILE) \
	--output $(CATEGORY_STATS_FILE)
dataset: install
	@STREET_NAMES_FILE=$(STREET_NAMES_FILE) \
	STREET_CATEGORIES_FILE=$(STREET_CATEGORIES_FILE) \
	OSM_STREETS_FILE=$(OSM_STREETS_FILE) \
	DATASET_FILE=$(DATASET_FILE) \
	$(PYTHON) scripts/create-dataset.py

# kaggle uploads whatever is in the target dir, so the tracked metadata file
# is copied next to the generated CSV before invoking it.
upload:
	@mkdir -p $(dir $(DATASET_FILE))
	@cp dataset/dataset-metadata.json $(dir $(DATASET_FILE))
	@kaggle datasets version -p $(dir $(DATASET_FILE)) -m "update dataset"

site: install
	@$(PYTHON) scripts/build_site.py \
	--dataset $(DATASET_FILE) \
	--categories $(STREET_CATEGORIES_FILE) \
	--osm $(OSM_STREETS_FILE) \
	--canonical $(CANONICAL_STREETS_FILE) \
	--base-path "$(SITE_BASE)"

site-local: install
	@$(PYTHON) scripts/build_site.py \
	--dataset $(DATASET_FILE) \
	--categories $(STREET_CATEGORIES_FILE) \
	--osm $(OSM_STREETS_FILE) \
	--canonical $(CANONICAL_STREETS_FILE) \
	--base-path /

site-serve: site-local
	@echo "Serving $(SITE_DIST) at http://127.0.0.1:$(SITE_PORT)/"
	@$(PYTHON) -m http.server $(SITE_PORT) --directory $(SITE_DIST)

# Rebuild for Pages and print deploy steps. Push to main triggers Actions deploy.
site-deploy: site
	@echo "Site built at $(SITE_DIST) with base path $(SITE_BASE)"
	@echo "Deploy: commit site/dist (and related files), then:"
	@echo "  git push origin main"
	@echo "GitHub Actions workflow .github/workflows/pages.yml publishes to GitHub Pages."
	@echo "One-time: repo Settings → Pages → Source = GitHub Actions"
	@echo "URL: https://evgeniyarbatov.github.io/singapore-streets/"

test: install
	@$(PYTHON) -m unittest discover -s tests
all: streets clean canonical categorize category-report dataset

reset:
	@rm -f $(GENERATED_DATA)
	@rm -rf $(DATA_DIR)/filtered

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
	@echo "site            - build static site into site/dist (Pages base path)"
	@echo "site-local      - build static site with base path /"
	@echo "site-serve      - build for local root and serve on SITE_PORT (default 8000)"
	@echo "site-deploy     - build site and print GitHub Pages deploy steps"
	@echo "test            - run unit tests"
	@echo "all             - streets, clean, canonical, categorize, category-report, dataset"
	@echo "reset           - remove generated data"
	@echo "reset-osm       - remove downloaded/converted OSM files"
	@echo "fresh           - reset + all"
	@echo "fresh-all       - reset, reset-osm, osm, city, all"
	@echo "lock            - update uv.lock"

.PHONY: install osm city streets clean canonical categorize category-report dataset upload site site-local site-serve site-deploy test all reset reset-osm fresh fresh-all lock help
