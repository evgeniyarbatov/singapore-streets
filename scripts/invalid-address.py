import sys
import re

def main():
  with open(
    "filtered/invalid-address.txt", 
    "w",
  ) as f:
    for line in sys.stdin:
      line = line.rstrip()
      
      starts_with_letter = re.match(r'^[A-Z]', line)
      is_block = re.match(r'^Blk', line, re.IGNORECASE)
      contains_punctuation = bool(re.search(r'[;,:#()]', line))
      has_stop_words = bool(re.search(r'(^After|^Before|Opposite|^Entrance|Station|Temple|Park$|Playground|Fitness Centre|Market$|Terminal$)', line))
      has_special_characters = bool(re.search(r'@', line))
      has_invalid_lorongs = bool(re.search(r'^Lorong\s+\d+$', line))
      
      if (
        starts_with_letter and 
        not is_block and
        not contains_punctuation and 
        not has_stop_words and
        not has_special_characters and
        not has_invalid_lorongs
      ):
        print(line)
      else:
        f.write(line + '\n')

if __name__ == "__main__":
    main()
