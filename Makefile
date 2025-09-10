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
	
	# Extract from addr:place
	grep '<tag k="addr:place" v=' $(OSM_DIR)/singapore.osm | sed 's/.*v="\([^"]*\)".*/\1/' | egrep -i '$(STREET_PATTERN)' | sort | uniq >> $(SG_STREETS_FILE)
	
	sort $(SG_STREETS_FILE) | uniq > $(TMP_SG_STREETS_FILE)
	mv $(TMP_SG_STREETS_FILE) $(SG_STREETS_FILE) 

clean:
	cat data/singapore-streets.txt | \
	python3 scripts/format-address.py | \
	python3 scripts/invalid-address.py | \
	python3 scripts/street-names.py | \
	sort | uniq > singapore-streets.txt

categorize:
	ollama run mistral-nemo:latest "Please analyze this list of Singapore street names and categorize them creatively by:\n\n1. **Linguistic Origin**: Malay, English/British, Chinese (Hokkien/Teochew/Cantonese), Tamil, etc.\n2. **Historical Themes**: Colonial administrators, local heroes, historical figures, royalty, etc.\n3. **Nature & Geography**: Trees, flowers, animals, geographical features, etc.\n4. **Cultural & Religious**: Temples, mosques, cultural concepts, festivals, etc.\n5. **Occupational**: Trades, professions, industries\n6. **Directional & Descriptive**: Colors, directions, sizes, shapes\n7. **Modern Development**: New towns, planned developments, contemporary naming\n\nFor each category, provide the street names as bullet points and include brief explanations of etymology or significance where relevant. Format as a comprehensive markdown document with clear headings. Here are the Singapore street names:" < singapore-streets.txt > street_categories.md

.PHONY: osm city streets clean categorize