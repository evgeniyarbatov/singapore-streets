# Singapore Streets

How many streets are there in Singapore?

## Steps

Download latest OSM data:

```
cd data
make
```

Get cleaned up street names:

```
make
```

Validate against a known list:

```
cd validate
make
```

Check which OSM tags the missing steets belong to:

```
cd validate
make osm
```

## Open issues

- Typos in OSM like `Woodland Drive 75` instead of `Woodlands Drive 75`
