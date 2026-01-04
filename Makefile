VENV_PATH := .venv

PYTHON := $(VENV_PATH)/bin/python
BLACK := $(VENV_PATH)/bin/black
FLAKE8 := $(VENV_PATH)/bin/flake8
PIP := $(VENV_PATH)/bin/pip

REQUIREMENTS := requirements.txt

SCRIPTS_DIR = scripts
PYTHON_FILES := $(shell find $(SCRIPTS_DIR) -name "*.py")

SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf

OSM_DIR = osm
SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

TMP_SG_STREETS_FILE = /tmp/singapore-streets.txt
SG_STREETS_FILE = data/singapore-streets.txt

STREET_PATTERN = (avenue$$|boulevard$$|central$$|circle$$|close$$|crescent$$|drive$$|expressway$$|farmway$$|gardens$$|green$$|grove$$|heights$$|hill$$|lane$$|link$$|loop$$|parkway$$|ring$$|rise$$|road$$|square$$|street$$|terrace$$|walk$$|way$$|jalan|lorong)

STREET_FILE        := singapore-streets.txt

venv:
	@python3 -m venv $(VENV_PATH)

install: venv
	@$(PIP) install --disable-pip-version-check -q --upgrade pip
	@$(PIP) install --disable-pip-version-check -q -r $(REQUIREMENTS)

format:
	@if [ -n "$(PYTHON_FILES)" ]; then \
		$(BLACK) $(PYTHON_FILES); \
	else \
		echo "No Python files"; \
	fi

lint:
	@if [ -n "$(PYTHON_FILES)" ]; then \
		$(FLAKE8) $(PYTHON_FILES); \
	else \
		echo "No Python files"; \
	fi

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
	@$(PYTHON) scripts/categorize_streets.py $(STREET_FILE) street_categories.md
	@echo "✓ Categorization complete"

cleanvenv:
	@rm -rf $(VENV_PATH)

.PHONY: venv osm city streets clean categorize
