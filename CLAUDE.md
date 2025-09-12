# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project is an end-to-end pipeline for extracting and analyzing street names from OpenStreetMap (OSM) data for Singapore. It downloads OSM data, processes it to extract street names, cleans the data using Python scripts, and categorizes streets using AI models via Ollama.

## Core Architecture

### Data Processing Pipeline
The project follows a sequential Makefile-based pipeline:

1. **Data Acquisition** (`make osm`): Downloads Malaysia-Singapore-Brunei OSM data from Geofabrik
2. **Geographic Filtering** (`make city`): Extracts Singapore-specific data using osmconvert and osmium
3. **Street Extraction** (`make streets`): Extracts street names from multiple OSM tag sources
4. **Data Cleaning** (`make clean`): Processes streets through Python filtering scripts
5. **AI Categorization** (`make categorize`): Uses Ollama/Mistral to categorize streets by linguistic and thematic patterns

### Key Directories
- `osm/`: Raw and processed OSM data files
- `data/`: Intermediate processed street data
- `filtered/`: Invalid addresses and non-street names removed during cleaning
- `scripts/`: Python data processing utilities
- `chunks/` (temporary): Created during categorization for batch processing

### Street Extraction Strategy
The pipeline extracts street names from multiple OSM tag sources:
- `addr:street` tags (address references)
- Highway name tags (primary roads)  
- General name tags matching street patterns
- `addr:place` tags with street patterns

Street patterns are defined by the regex: `(avenue|boulevard|central|circle|close|crescent|drive|expressway|farmway|gardens|green|grove|heights|hill|lane|link|loop|parkway|ring|rise|road|square|street|terrace|walk|way|jalan|lorong)`

## Development Commands

### Primary Pipeline Commands
```bash
# Full pipeline
make osm city streets clean categorize

# Individual stages
make osm          # Download OSM data
make city         # Extract Singapore region  
make streets      # Extract street names
make clean        # Clean and filter data
make categorize   # AI categorization (requires Ollama)
```

### Data Processing Scripts
Located in `scripts/` directory:
- `format-address.py`: Standardizes abbreviations and formatting (Rd→Road, St→Street, etc.)
- `invalid-address.py`: Filters out invalid addresses using pattern matching
- `street-names.py`: Final filtering for actual street names vs buildings/complexes

### Testing Individual Scripts
```bash
# Test individual Python scripts in pipeline
cat data/singapore-streets.txt | python3 scripts/format-address.py | head -20
cat data/singapore-streets.txt | python3 scripts/invalid-address.py | head -20  
cat data/singapore-streets.txt | python3 scripts/street-names.py | head -20
```

## AI Categorization System

The `make categorize` command uses Ollama with Mistral-Nemo to categorize streets by:
1. Linguistic Origin (Malay, English/British, Chinese, Tamil)
2. Historical Themes (colonial figures, local heroes, royalty)
3. Nature & Geography (trees, flowers, animals, places)
4. Cultural & Religious (temples, festivals, concepts)
5. Occupational (trades, professions)  
6. Descriptive (colors, directions, shapes)
7. Modern Development (transportation, new towns, business parks)

**Prerequisites**: Requires Ollama with mistral-nemo:latest model installed.

## File Dependencies

The pipeline expects these external tools:
- `wget`: For downloading OSM data
- `osmconvert`: For geographic filtering
- `osmium`: For OSM file format conversion  
- `ollama`: For AI categorization (with mistral-nemo:latest)
- Python 3 with `re` and `sys` modules

## Key Output Files

- `singapore-streets.txt`: Final cleaned list of Singapore street names
- `street_categories.md`: AI-generated categorization of streets
- `data/singapore-streets.txt`: Intermediate extracted street data
- `filtered/invalid-address.txt`: Addresses filtered out as invalid
- `filtered/not-street-names.txt`: Names filtered out as non-streets