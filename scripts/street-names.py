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
        r'Road|'
        r'Street|'
        r'Boulevard|'
        r'Avenue|'
        r'Link|'
        r'Drive|'
        r'Close|'
        r'Hill|'
        r'Crescent|'
        r'Lane|'
        r'Walk|'
        r'Rise|'
        r'Jalan|'
        r'View|'
        r'Terrace|'
        r'Park|'
        r'Lorong|'
        r'Central|'
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
