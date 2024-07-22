GIST_ID = 2297910
FILE_NAME = singapore-streets.txt
URL = https://gist.githubusercontent.com/choonkeat/$(GIST_ID)/raw

FILE1 = ../singapore-streets.txt
FILE2 = singapore-streets.txt

SAMPLE_SIZE = 20

all: summary unique_streets

download:
	curl -o $(FILE_NAME) $(URL)

summary:
	@echo "Summary"
	@echo ""
	@echo "$$(wc -l < $(FILE1)) streets in OSM file"
	@echo "$$(wc -l < $(FILE2)) streets in validation file"
	@echo "$$(comm -12 $(FILE1) $(FILE2) | wc -l) same streets"
	@echo "$$(comm -3 $(FILE1) $(FILE2) | wc -l) different streets"
	@echo ""

unique_streets:
	@echo "Lines only in OSM file:"
	@echo ""
	@comm -23 $(FILE1) $(FILE2) | gshuf -n $(SAMPLE_SIZE)
	@echo ""
	@echo "Lines only in validation file:"
	@echo ""
	@comm -13 $(FILE1) $(FILE2) | gshuf -n $(SAMPLE_SIZE)
