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
	$(STREET_NAMES_FILE)

clean:
	@tmp="$$(mktemp)"; \
	cat $(STREET_NAMES_FILE) | \
	$(PYTHON) scripts/format-address.py | \
	$(PYTHON) scripts/invalid-address.py | \
	$(PYTHON) scripts/street-names.py | \
	sort | uniq > "$$tmp"; \
	mv "$$tmp" $(STREET_NAMES_FILE)

categorize:
	@$(PYTHON) scripts/categorize_streets.py \
	$(STREET_NAMES_FILE) \
	$(STREET_CATEGORIES_FILE) \
	--model $(MODEL)

dataset:
	@$(PYTHON) scripts/create-dataset.py

test:
	@$(PYTHON) -m unittest discover -s tests

.PHONY: osm dataset test
