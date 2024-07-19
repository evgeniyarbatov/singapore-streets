# how-many-streets

How many streets are there in the city?

## Steps

Make sure only Singapore map is included:

```
osmconvert \
~/osm/singapore.osm.pbf \
-b=103.6137,1.1304,104.0922,1.4713 \
-o=/Users/zhenya/osm/singapore-filtered.osm.pbf
```

Convert PBF file to plain XML:

```
osmium cat \
--overwrite \
~/osm/singapore-filtered.osm.pbf \
-o ~/osm/singapore.osm
```

Get streets:

```
grep "<tag k=\"addr:street\" v=" ~/osm/singapore.osm | sed 's/.*v=\"\(.*\)\".*/\1/' | sort | uniq > singapore-streets.txt
```