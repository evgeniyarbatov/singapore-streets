# Singapore Streets

How many streets are there in Singapore? 

```
$ wc -l singapore-streets-clean.txt
    3438 singapore-streets-clean.txt
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
grep '^[A-Z]' | \
awk -F ',' '{print $1}' | \
sed -E 's/^[0-9]+ //; s/[Bb][Ll][Kk] [0-9]+[A-Za-z]? ?//i; s/Block [0-9 ]+//i; s/ #.*//' | \
sed -E "s/&apos;/'/g; s/’/'/g; s/;//g; s/ Rd$/ Road/g; s/ St$/ Street/g; s/Jln/Jalan/g; s/Ave /Avenue /g; s/Ave$/Avenue/g; s/Blvd/Boulevard/g;" | \
grep -v ^$ | \
sort | uniq > singapore-streets-clean.txt
```

## References

- https://gist.github.com/choonkeat/2297910