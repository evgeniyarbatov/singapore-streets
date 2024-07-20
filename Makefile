.PHONY: process

process:
	cat data/singapore-streets.txt | \
	python3 scripts/invalid-addresses.py \
	> singapore-streets.txt
