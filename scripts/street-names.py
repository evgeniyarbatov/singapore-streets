import sys
import re

def main():
  # Building/shopping mall exclusions
  building_keywords = [
    'mall', 'plaza', 'centre', 'center', 'building', 'tower', 'complex', 
    'hub', 'junction', 'interchange', 'station', 'terminal', 'hotel',
    'condominium', 'condo', 'residences', 'apartments', 'flats',
    'food court', 'foodcourt'
  ]
  
  with open(
    "filtered/not-street-names.txt", 
    "w",
  ) as f:
    seen_names = []
    for line in sys.stdin:
      line = line.rstrip()
      
      is_lorong = bool(re.search(
        r'\bLorong(\s*\d+[A-Za-z]?)?\s*',
        line,
        re.IGNORECASE,
      ))
      
      is_jalan = bool(re.search(
        r'^Jalan\s*',
        line,
        re.IGNORECASE,
      ))
         
      is_street_name = bool(re.search(
        r'\b('
        r'Avenue|'
        r'Boulevard|'
        r'Central|'
        r'Circle|'
        r'Close|'
        r'Crescent|'
        r'Drive|'
        r'Expressway|'
        r'Farmway|'
        r'Gardens|'
        r'Heights|'
        r'Hill|'
        r'Lane|'
        r'Link|'
        r'Loop|'
        r'Parkway|'
        r'Ring|'
        r'Rise|'
        r'Road|'
        r'Square|'
        r'Street|'
        r'Terrace|'
        r'Walk|'
        r'Way'
        r')(\s*\d+[A-Za-z]?)?$',
        line,
        re.IGNORECASE,
      ))
            
      # Check for building/shopping mall keywords
      is_building = any(
        re.search(r'\b' + keyword + r'\b', line, re.IGNORECASE) 
        for keyword in building_keywords
      )
      
      # Check for '/' character in street name
      has_slash = '/' in line
      
      if (
        (is_street_name or is_lorong or is_jalan) and
        not is_building and
        not has_slash
      ):
        print(line)
        seen_names.append(line)
      else:
        direction_pattern = r'\b(East|West|North|South)(\s*\d+[A-Za-z]?)?$'
        is_direction_name = bool(re.search(
          direction_pattern,
          line,
          re.IGNORECASE,
        ))
        if is_direction_name:
          no_direction_name = re.sub(direction_pattern, '', line)
          if any(
            re.search(
              r'\b'+no_direction_name+r'\b', 
              s,
            ) for s in seen_names
          ):
            print(line)
        else:
          # Log why the line was filtered out
          reason = []
          if is_building:
            reason.append("building/mall")
          if has_slash:
            reason.append("contains slash")
          if not (is_street_name or is_lorong or is_jalan):
            reason.append("not street pattern")
          
          f.write(f"{line} # Filtered: {', '.join(reason)}\n")
        
if __name__ == "__main__":
    main()
