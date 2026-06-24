VENV_PATH := .venv

PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
REQUIREMENTS := requirements.txt

OSM_DIR = osm
SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf
SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

OSM_STREETS_FILE = data/osm-streets.csv
STREET_NAMES_FILE = data/street-names.txt
STREET_CATEGORIES_FILE = data/street_categories.csv
REVIEW_QUEUE_FILE = data/review-queue.csv
CANONICAL_STREETS_FILE = data/canonical-streets.csv
ALLOWLIST_FILE = data/allowlist.txt
INVALID_ADDRESS_LOG = filtered/invalid-address.txt
NOT_STREET_NAMES_LOG = filtered/not-street-names.txt

MODEL = mistral-nemo:latest

venv:
	@python3 -m venv $(VENV_PATH)

install: venv
	@$(PIP) install --disable-pip-version-check -q --upgrade pip
	@$(PIP) install --disable-pip-version-check -q -r $(REQUIREMENTS)

osm:
	@rm -f $(SINGAPORE_OSM_PATH)
	@wget $(SINGAPORE_OSM_URL) -P $(OSM_DIR)

city:
	@osmconvert $(SINGAPORE_OSM_PATH) \
	-B=$(OSM_DIR)/singapore.poly \
	-o=$(OSM_DIR)/singapore.osm.pbf

	@osmium cat --overwrite \
	$(OSM_DIR)/singapore.osm.pbf \
	-o $(OSM_DIR)/singapore.osm

streets:
	@$(PYTHON) scripts/extract_streets.py \
	$(OSM_DIR)/singapore.osm \
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

canonical:
	@$(PYTHON) scripts/canonical_streets.py \
	$(STREET_NAMES_FILE) \
	$(CANONICAL_STREETS_FILE)

categorize:
	@$(PYTHON) scripts/categorize_streets.py \
	$(STREET_NAMES_FILE) \
	$(STREET_CATEGORIES_FILE) \
	--model $(MODEL)

category-report:
	@$(PYTHON) scripts/category_report.py

dataset:
	@$(PYTHON) scripts/create-dataset.py

upload:
	@kaggle datasets version -p dataset -m "update dataset"

test:
	@$(PYTHON) -m unittest discover -s tests

.PHONY: osm dataset upload test category-report canonical
