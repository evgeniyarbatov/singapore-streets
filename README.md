# Singapore Streets

## How many streets are there in Singapore?

This project explores OpenStreetMap (OSM) data to find all streets in Singapore. It’s an end-to-end pipeline that downloads and processes OSM data to extract street names.

## How to Run

### Download the latest OSM data

```
make osm
```

### Extract Singapore OSM

```
make city
```

### Get street names

```
make streets
```

### Clean street names

```
make clean
```
### Group street names

```
make categorize
```

## Open Issues

- Few typos in OSM data, e.g., `Woodland Drive 75` instead of `Woodlands Drive 75`