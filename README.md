# Singapore Streets

How many streets are there in Singapore? 

```
$ wc -l singapore-streets-clean.txt
    3479 singapore-streets-clean.txt
```

## Details

- `singapore-streets.txt`: street names based on OSM data
- `singapore-streets-clean.txt`: cleaned up version of street names

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
sed 's/^[0-9]* //' | \
grep '^[A-Z]' | \
grep -v '^Blk [0-9 ]\+' | \
sed -E 's/[Bb][Ll][Kk] [0-9]+[A-Za-z] //i' | \
sed -E 's/Block [0-9 ]+//i' | \
awk -F ',' '{print $1}' | \
sed 's/ #.*//' | \
sed "s/&apos;/'/g" | \
sed "s/’/'/g" | \
sed 's/[^a-zA-Z0-9 ]//g; s/;//g' | \
sed 's/ Rd$/ Road/g; s/ St$/ Street/g; s/Jln/Jalan/g;' | \
sort | uniq \
> singapore-streets-clean.txt
```
