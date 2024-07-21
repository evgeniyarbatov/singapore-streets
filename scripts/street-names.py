import sys
import re

def main():
  with open(
    "filtered/not-street-names.txt", 
    "w",
  ) as f:
    for line in sys.stdin:
      line = line.rstrip()
      
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
        r'Jalan|'
        r'Lane|'
        r'Link|'
        r'Loop|'
        r'Lorong|'
        r'Place|'
        r'Ring|'
        r'Rise|'
        r'Road|'
        r'Street|'
        r'Terrace|'
        r'View|'
        r'Walk|'
        r'Way'
        r')\b',
        line,
        re.IGNORECASE,
      ))
      
      if is_street_name:
        print(line)
      else:
        f.write(line + '\n')

if __name__ == "__main__":
    main()
