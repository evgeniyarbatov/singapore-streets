SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf

OSM_DIR = osm
SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

TMP_SG_STREETS_FILE = /tmp/singapore-streets.txt
SG_STREETS_FILE = data/singapore-streets.txt

all: process

osm:
	@if [ ! -f $(SINGAPORE_OSM_PATH) ]; then \
		wget $(SINGAPORE_OSM_URL) -P $(OSM_DIR); \
	fi

city:
	@if [ ! -f $(OSM_DIR)/singapore.osm.pbf ]; then \
		osmconvert $(SINGAPORE_OSM_PATH) -B=$(OSM_DIR)/singapore.poly -o=$(OSM_DIR)/singapore.osm.pbf; \
	fi

	@if [ ! -f $(OSM_DIR)/singapore.osm ]; then \
		osmium cat --overwrite $(OSM_DIR)/singapore.osm.pbf -o $(OSM_DIR)/singapore.osm; \
	fi

streets:
	grep '<tag k="addr:street" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | sort | uniq > $(SG_STREETS_FILE)
	grep '<tag k="name" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | egrep -i '(road$|avenue$|street$|drive$|crescent$|lane$|walk$|jalan|lorong)' | sort | uniq >> $(SG_STREETS_FILE)
	sort $(SG_STREETS_FILE) | uniq > $(TMP_SG_STREETS_FILE)
	mv $(TMP_SG_STREETS_FILE) $(SG_STREETS_FILE) 

clean:
	cat data/singapore-streets.txt | \
	python3 scripts/format-address.py | \
	python3 scripts/invalid-address.py | \
	python3 scripts/street-names.py | \
	sort | uniq > singapore-streets.txt

.PHONY: osm city streets clean