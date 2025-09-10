SINGAPORE_OSM_URL = https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf

OSM_DIR = osm
SINGAPORE_OSM_PATH = $(OSM_DIR)/$(notdir $(SINGAPORE_OSM_URL))

TMP_SG_STREETS_FILE = /tmp/singapore-streets.txt
SG_STREETS_FILE = data/singapore-streets.txt

STREET_PATTERN = (avenue$$|boulevard$$|central$$|circle$$|close$$|crescent$$|drive$$|expressway$$|farmway$$|gardens$$|green$$|grove$$|heights$$|hill$$|lane$$|link$$|loop$$|parkway$$|ring$$|rise$$|road$$|square$$|street$$|terrace$$|walk$$|way$$|jalan|lorong)

all: process

osm:
	wget $(SINGAPORE_OSM_URL) -P $(OSM_DIR)

city:
	osmconvert $(SINGAPORE_OSM_PATH) -B=$(OSM_DIR)/singapore.poly -o=$(OSM_DIR)/singapore.osm.pbf
	osmium cat --overwrite $(OSM_DIR)/singapore.osm.pbf -o $(OSM_DIR)/singapore.osm

streets:
	# Extract from addr:street tags
	grep '<tag k="addr:street" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | sort | uniq > $(SG_STREETS_FILE)
	
	# Extract from highway name tags (primary source for roads)
	grep -E '<tag k="name" v=.*</tag>' $(OSM_DIR)/singapore.osm | grep -B5 -A5 '<tag k="highway"' | grep '<tag k="name" v=' | sed 's/.*v="\([^"]*\)".*/\1/' | sort | uniq >> $(SG_STREETS_FILE)
	
	# Extract from general name tags with street patterns
	grep '<tag k="name" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | egrep -i '$(STREET_PATTERN)' | sort | uniq >> $(SG_STREETS_FILE)
	
	# Extract from alternative name tags
	grep '<tag k="alt_name" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | egrep -i '$(STREET_PATTERN)' | sort | uniq >> $(SG_STREETS_FILE)
	
	# Extract from official name tags  
	grep '<tag k="official_name" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | egrep -i '$(STREET_PATTERN)' | sort | uniq >> $(SG_STREETS_FILE)
	
	# Extract from addr:housename and addr:place
	grep '<tag k="addr:housename" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | egrep -i '$(STREET_PATTERN)' | sort | uniq >> $(SG_STREETS_FILE)
	grep '<tag k="addr:place" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | egrep -i '$(STREET_PATTERN)' | sort | uniq >> $(SG_STREETS_FILE)
	
	sort $(SG_STREETS_FILE) | uniq > $(TMP_SG_STREETS_FILE)
	mv $(TMP_SG_STREETS_FILE) $(SG_STREETS_FILE) 

clean:
	cat data/singapore-streets.txt | \
	python3 scripts/format-address.py | \
	python3 scripts/invalid-address.py | \
	python3 scripts/fix_typos.py | \
	python3 scripts/street-names.py | \
	sort | uniq > singapore-streets.txt

.PHONY: osm city streets clean