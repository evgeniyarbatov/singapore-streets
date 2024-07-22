import sys
import re

def main():
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
        r'Farmway|'
        r'Gardens|'
        r'Green|'
        r'Grove|'
        r'Heights|'
        r'Hill|'
        r'Lane|'
        r'Link|'
        r'Loop|'
        r'Place$|'
        r'Ring|'
        r'Rise|'
        r'Road|'
        r'Street|'
        r'Terrace|'
        r'View|'
        r'Walk|'
        r'Way'
        r')(\s*\d+[A-Za-z]?)?$',
        line,
        re.IGNORECASE,
      ))
            
      if (
        is_street_name or
        is_lorong or
        is_jalan
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
          f.write(line + '\n')
        
if __name__ == "__main__":
    main()
