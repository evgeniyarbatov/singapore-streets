import sys
import re

def main():
  with open(
    "filtered/invalid_address.txt", 
    "w",
  ) as f:
    for line in sys.stdin:
      line = line.rstrip()
      
      if re.match(r'^[A-Z]', line):
        print(line)
      else:
        f.write(line + '\n')

if __name__ == "__main__":
    main()
