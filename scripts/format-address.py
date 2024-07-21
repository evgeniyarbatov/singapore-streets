import sys
import re

def format(text):
  text = text.title()
  text = re.sub(r"&apos;", "'", text)
  text = re.sub(r"’", "'", text)
  text = re.sub(r"Rd\b", "Road", text)
  text = re.sub(r"St\b", "Street", text)
  text = re.sub(r"Dr\b", "Drive", text)
  text = re.sub(r"Jln\b", "Jalan", text)
  text = re.sub(r"Lor\b", "Lorong", text)
  text = re.sub(r"Ave\b", "Avenue", text)
  text = re.sub(r"Blvd\b", "Boulevard", text)
  text = re.sub(r"Aft\b", "After", text)
  return text

def main():
  for line in sys.stdin:
    line = line.rstrip()
    print(
      format(line)
    )

if __name__ == "__main__":
    main()
