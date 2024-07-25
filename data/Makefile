OSM_URL = https://download.openstreetmap.fr/extracts/asia/singapore-latest.osm.pbf
BOUNDS = 103.6137,1.1304,104.0922,1.4713

OSM_PBF_PATH = ~/osm/singapore.osm.pbf
SG_OSM_PBF_PATH = /tmp/singapore.osm.pbf

SG_OSM_PATH = ~/osm/singapore.osm
TMP_SG_STREETS_FILE = /tmp/singapore-streets.txt
SG_STREETS_FILE = singapore-streets.txt

.PHONY: all download convert process extract

all: download convert process extract

download:
	wget $(OSM_URL) -O $(OSM_PBF_PATH)

convert:
	osmconvert $(OSM_PBF_PATH) -b=$(BOUNDS) -o=$(SG_OSM_PBF_PATH)

process:
	osmium cat --overwrite $(SG_OSM_PBF_PATH) -o $(SG_OSM_PATH)

extract:
	grep '<tag k="addr:street" v=' $(SG_OSM_PATH) | sed 's/.*v="\([^"]*\)".*/\1/' | sort | uniq > $(SG_STREETS_FILE)
# <tag k="name /> contains valid streets in <tag k="addr:street" /> but adds a lot of noise
# grep '<tag k="name" v=' $(SG_OSM_PATH) | sed 's/.*v="\([^"]*\)".*/\1/' | sort | uniq >> $(SG_STREETS_FILE)
	sort $(SG_STREETS_FILE) | uniq > $(TMP_SG_STREETS_FILE)
	mv $(TMP_SG_STREETS_FILE) $(SG_STREETS_FILE) 
