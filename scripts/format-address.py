import sys
import re

def format(text):
  text = re.sub(r"&apos;", "'", text)
  text = re.sub(r"’", "'", text)
  text = text.title()
  return text

def main():
  for line in sys.stdin:
    line = line.rstrip()
    print(
      format(line)
    )

if __name__ == "__main__":
    main()
