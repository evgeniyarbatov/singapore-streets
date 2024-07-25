GIST_ID = 2297910
FILE_NAME = singapore-streets.txt
URL = https://gist.githubusercontent.com/choonkeat/$(GIST_ID)/raw

FILE1 = ../singapore-streets.txt
FILE2 = singapore-streets.txt
SG_OSM_PATH = ~/osm/singapore.osm

SAMPLE_SIZE = 20

VALIDATON_RESULT_FILE = 'validation-result.txt'

all: summary unique_streets

download:
	curl -o $(FILE_NAME) $(URL)

summary:
	@echo "Summary" | tee $(VALIDATON_RESULT_FILE)
	@echo "" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "$$(wc -l < $(FILE1)) streets in OSM file" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "$$(wc -l < $(FILE2)) streets in validation file" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "$$(comm -12 $(FILE1) $(FILE2) | wc -l) same streets" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "$$(comm -3 $(FILE1) $(FILE2) | wc -l) different streets" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "" | tee -a $(VALIDATON_RESULT_FILE)

unique_streets:
	@echo "Lines only in OSM file:" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "" | tee -a $(VALIDATON_RESULT_FILE)
	@comm -23 $(FILE1) $(FILE2) | gshuf -n $(SAMPLE_SIZE) | tee -a $(VALIDATON_RESULT_FILE)
	@echo "" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "Lines only in validation file:" | tee -a $(VALIDATON_RESULT_FILE)
	@echo "" | tee -a $(VALIDATON_RESULT_FILE)
	@comm -13 $(FILE1) $(FILE2) | gshuf -n $(SAMPLE_SIZE) | tee -a $(VALIDATON_RESULT_FILE)

osm:
	comm -13 $(FILE1) $(FILE2) | gshuf -n $(SAMPLE_SIZE) | xargs -I '{}' grep {} ${SG_OSM_PATH} | sort | uniq
