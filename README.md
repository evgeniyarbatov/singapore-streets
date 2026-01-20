# Singapore Streets 🇸🇬

Exploring Singapore street names with OpenStreetMap.

## How Many Streets?

~4,460 streets based on `data/singapore-streets.txt` You can group them by auto-generated tags in `data/street_categories.txt`

## How to Run

```
# Download the latest OSM data
make osm
# Extract Singapore OSM
make city
# Extract street names from OSM
make streets
# Clean street names
make clean
# Use ollama to tag each street
make categorize
```

## Story

I became interested in learning about Singapore street names after running long distances in Singapore. Then one day my son asked me how many streets there are in Singapore, and I decided to find out the answer. This turned out to be interesting as there is nothing obvious that defines a street name in OSM data. I think this is one of those projects where you can always make incremental improvements and discover more.