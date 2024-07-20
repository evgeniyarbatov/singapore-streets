# Singapore Streets

How many streets are there in Singapore? 

## Steps

Download latest OSM data:

```
cd data
make
```

Cleanup street names:

```
make
```

Grep:

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