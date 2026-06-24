# Categorize Singapore Street — Prompt v1

Classify a Singapore street name using the fixed taxonomy below.

## Primary categories (pick exactly one)

{{CATEGORIES}}

## Secondary tags (optional, pick zero or more)

{{TAGS}}

## Instructions

1. Choose the single best **primary category** from the list above.
2. Add **secondary tags** only when clearly supported by the name.
3. Respond with **valid JSON only** — no markdown, no explanation:

```json
{
  "primary_category": "<category id>",
  "tags": ["tag_id"],
  "confidence": "high|medium|low"
}
```

Use category **ids** (snake_case), not display names. If uncertain, use `uncategorized` and `confidence: low`.

## Street

{{STREET_NAME}}