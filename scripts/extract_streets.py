#!/usr/bin/env python3

import sys
import csv
import re
import osmium
import polyline

def encode_polyline(coords):
    """
    Encode coordinates as polyline string using Google's polyline algorithm
    """
    if not coords:
        return ""
    if len(coords) == 1:
        # Single point - just return lat,lon
        return None
    # Multiple points - encode as polyline
    return polyline.encode(coords)

class StreetHandler(osmium.SimpleHandler):
    """OSM handler to extract street names from various sources"""
    
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.streets = []
        self.nodes = {}
    
    def node(self, n):
        # Store node coordinates
        self.nodes[n.id] = (n.location.lat, n.location.lon)
        
    def way(self, w):
        # Check for highway with name
        if 'highway' in w.tags and 'name' in w.tags:
            name = w.tags['name']
            coords = []
            for node_ref in w.nodes:
                if node_ref.ref in self.nodes:
                    coords.append(self.nodes[node_ref.ref])
            
            polyline = encode_polyline(coords)
            self.streets.append({
                'name': name,
                'polyline': polyline,
                'osm_source': 'highway_name'
            })
        
        # Check for general name tags with street patterns
        elif 'name' in w.tags and is_street_pattern(w.tags['name']):
            name = w.tags['name']
            coords = []
            for node_ref in w.nodes:
                if node_ref.ref in self.nodes:
                    coords.append(self.nodes[node_ref.ref])
            
            polyline = encode_polyline(coords)
            self.streets.append({
                'name': name,
                'polyline': polyline,
                'osm_source': 'name_pattern'
            })
        
def extract_streets_from_osm(osm_file_path, output_csv_path):
    """
    Extract street names, coordinates, and source tags from OSM file using osmium
    """
    
    print("Processing OSM file with osmium...")
    
    handler = StreetHandler()
    handler.apply_file(osm_file_path)
    
    print(f"Extracted {len(handler.streets)} street entries")
    
    # Write to CSV
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['name', 'polyline', 'osm_source']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        for street in handler.streets:
            writer.writerow(street)
    
    print(f"Saved to {output_csv_path}")


def is_street_pattern(name):
    """Check if name matches street patterns"""
    street_pattern = re.compile(
        r'\b('
        r'avenue|boulevard|central|circle|close|crescent|drive|expressway|'
        r'farmway|gardens|green|grove|heights|hill|lane|link|loop|parkway|'
        r'ring|rise|road|square|street|terrace|walk|way|jalan|lorong'
        r')\b',
        re.IGNORECASE
    )
    return bool(street_pattern.search(name))

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 extract_streets.py <input_osm_file> <output_csv_file>")
        sys.exit(1)
    
    osm_file = sys.argv[1]
    csv_file = sys.argv[2]
    
    extract_streets_from_osm(osm_file, csv_file)

if __name__ == "__main__":
    main()