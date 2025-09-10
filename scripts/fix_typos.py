import sys
import re
from collections import Counter
from difflib import SequenceMatcher

def find_similar_words(words, threshold=0.85):
  """Group similar words and return the most common spelling for each group"""
  word_groups = {}
  canonical_forms = {}
  
  for word in words:
    # Find if this word is similar to any existing canonical form
    matched = False
    for canonical in canonical_forms:
      if SequenceMatcher(None, word.lower(), canonical.lower()).ratio() >= threshold:
        word_groups[canonical].append(word)
        matched = True
        break
    
    if not matched:
      canonical_forms[word] = True
      word_groups[word] = [word]
  
  # For each group, return the most frequent spelling
  corrections = {}
  for canonical, variants in word_groups.items():
    if len(variants) > 1:
      most_common = Counter(variants).most_common(1)[0][0]
      for variant in variants:
        if variant != most_common:
          corrections[variant.lower()] = most_common
  
  return corrections

def main():
  # Read all input first to analyze for typos
  all_lines = [line.rstrip() for line in sys.stdin]
  
  # Extract base words (without street suffixes) for typo detection
  base_words = []
  for line in all_lines:
    # Remove common street suffixes to get the base name
    base = re.sub(r'\b(Avenue|Boulevard|Central|Circle|Close|Court|Crescent|Drive|Expressway|Farmway|Gardens|Green|Grove|Heights|Hill|Lane|Link|Loop|Park|Parkway|Place|Ring|Rise|Road|Square|Street|Terrace|View|Walk|Way|Jalan|Lorong)(\s*\d+[A-Za-z]?)?$', '', line, flags=re.IGNORECASE).strip()
    if base:
      # Extract individual words from the base name
      words = re.findall(r'\b\w+\b', base)
      base_words.extend(words)
  
  # Find automatic typo corrections based on frequency
  typo_corrections = find_similar_words(base_words)
  
  # Apply corrections and output
  for line in all_lines:
    # Apply automatic typo corrections
    corrected_line = line
    for typo, correction in typo_corrections.items():
      corrected_line = re.sub(r'\b' + re.escape(typo) + r'\b', correction, corrected_line, flags=re.IGNORECASE)
    
    print(corrected_line)

if __name__ == "__main__":
    main()