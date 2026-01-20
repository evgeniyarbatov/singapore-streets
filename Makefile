VENV_PATH := .venv

PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
REQUIREMENTS := requirements.txt

SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf

OSM_DIR = osm
SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

SG_STREETS_FILE = data/singapore-streets.txt

STREET_FILE        := singapore-streets.txt
MODEL              := mistral-nemo:latest

venv:
	@python3 -m venv $(VENV_PATH)

install: venv
	@$(PIP) install --disable-pip-version-check -q --upgrade pip
	@$(PIP) install --disable-pip-version-check -q -r $(REQUIREMENTS)

osm:
	@rm -f $(SINGAPORE_OSM_PATH)
	@wget $(SINGAPORE_OSM_URL) -P $(OSM_DIR)

city:
	@osmconvert $(SINGAPORE_OSM_PATH) -B=$(OSM_DIR)/singapore.poly -o=$(OSM_DIR)/singapore.osm.pbf
	@osmium cat --overwrite $(OSM_DIR)/singapore.osm.pbf -o $(OSM_DIR)/singapore.osm

streets:
	@$(PYTHON) scripts/extract_streets.py $(OSM_DIR)/singapore.osm data/singapore-streets.csv
	@$(PYTHON) -c "import csv; [print(row[0]) for row in csv.reader(open('data/singapore-streets.csv'))][1:]" | sort | uniq > $(SG_STREETS_FILE)

clean:
	@cat data/singapore-streets.txt | \
	$(PYTHON) scripts/format-address.py | \
	$(PYTHON) scripts/invalid-address.py | \
	$(PYTHON) scripts/street-names.py | \
	sort | uniq > singapore-streets.txt

categorize:
	@echo "▶ Starting street name categorization"
	@$(PYTHON) scripts/categorize_streets.py $(STREET_FILE) street_categories.csv --model $(MODEL)
	@echo "✓ Categorization complete"

dataset:
	@$(PYTHON) scripts/create-dataset.py

.PHONY: osm dataset