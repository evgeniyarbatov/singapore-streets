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
	@rm -f street_categories.md chunks/*.txt chunks/*.md 2>/dev/null || true
	@mkdir -p chunks
	@split -l 500 singapore-streets.txt chunks/streets_chunk_
	@for chunk in chunks/streets_chunk_*; do \
		echo "Processing $$chunk..."; \
		if ollama run mistral-nemo:latest "Analyze these Singapore street names and categorize them by: 1) Linguistic Origin (Malay, English/British, Chinese, Tamil, etc.) 2) Historical Themes (colonial figures, local heroes, royalty) 3) Nature & Geography (trees, flowers, animals, places) 4) Cultural & Religious (temples, festivals, concepts) 5) Occupational (trades, professions) 6) Descriptive (colors, directions, shapes) 7) Modern Development. List street names under each category with brief explanations. Format as markdown with clear headings:" < $$chunk > chunks/category_$$(basename $$chunk).md; then \
			echo "✓ Completed $$chunk"; \
		else \
			echo "✗ Failed processing $$chunk"; \
			exit 1; \
		fi; \
	done
	@echo "Consolidating results into common headings..."
	@cat chunks/category_*.md > chunks/all_categories.md
	@if ollama run mistral-nemo:latest "Please consolidate this fragmented categorization of Singapore street names into a single, well-organized markdown document. Merge duplicate categories, combine street names under common headings, remove redundancy, and create a comprehensive final categorization. Maintain the 7 main categories: 1) Linguistic Origin 2) Historical Themes 3) Nature & Geography 4) Cultural & Religious 5) Occupational 6) Descriptive 7) Modern Development. Format with clear headings and bullet points:" < chunks/all_categories.md > street_categories.md; then \
		echo "✓ Consolidation completed"; \
	else \
		echo "✗ Consolidation failed"; \
		exit 1; \
	fi
	@rm -rf chunks
	@echo "Cleaned up temporary chunk files"

.PHONY: osm city streets clean categorize