# Singapore Streets

How many streets are there in Singapore? 

## Preqs

```
brew install coreutils
brew install wget
```

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

## Open issues

- Typos in OSM like `Woodland Drive 75` instead of `Woodlands Drive 75`