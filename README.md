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

Cleanup street names:

```
cat singapore-streets.txt | \
grep -v ^# |
grep -v '^[0-9 ]\+' | \
grep -v '^Blk [0-9 ]\+' | \
awk -F ',' '{print $1}' | \
sed 's/ #.*//' | \
sed 's/^[0-9]* //' | \
sed "s/&apos;/'/g" | \
sed 's/Blk [0-9]* //i' | \
sort | uniq | \
less
```