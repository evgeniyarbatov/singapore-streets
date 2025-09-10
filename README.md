# 🗺️ Singapore Streets

## How many streets are there in Singapore?

This project explores OpenStreetMap (OSM) data to find all streets in Singapore. It’s an end-to-end pipeline that downloads and processes OSM data to extract street names.

## 🚀 Overview

This project includes:

- Retrieval of the latest OSM data for Singapore
- Extraction and cleanup of street names
- Validation of the resulting list

Useful for:

- Exploring Singapore on foot
- Discovering unusual and interesting street names

## 🛠️ How to Run

### 1. Download the latest OSM data

```
make osm
```

### 2. Extract Singapore OSM

```
make city
```

### 3. Get street names

```
make streets
```

### 3. Clean street names

```
make clean
```
### 4. Group street names

```
make categorize
```

## 📌 Open Issues

- Few typos in OSM data, e.g., `Woodland Drive 75` instead of `Woodlands Drive 75`