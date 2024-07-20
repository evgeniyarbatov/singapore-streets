import sys
import re

def main():
  with open(
    "filtered/invalid_address.txt", 
    "w",
  ) as f:
    for line in sys.stdin:
      line = line.rstrip()
      
      starts_with_letter = re.match(r'^[A-Z]', line)
      is_block = re.match(r'^Blk', line, re.IGNORECASE)
      contains_punctuation = bool(re.search(r'[;,#()]', line))
      
      if (
        starts_with_letter and 
        not is_block and
        not contains_punctuation
      ):
        print(line)
      else:
        f.write(line + '\n')

if __name__ == "__main__":
    main()
