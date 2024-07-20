.PHONY: process

process:
	cat data/singapore-streets.txt | \
	python3 scripts/format-address.py | \
	python3 scripts/invalid-address.py | \
	sort | uniq > singapore-streets.txt
