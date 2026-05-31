#!/usr/bin/env python3
"""Extract text from a PDF and call OpenRouter to generate structured recipe markdown."""

import sys
import os
import json
import urllib.request
import pdfplumber
from datetime import date

API_KEY = os.environ["ANTHROPIC_API_KEY"]
TODAY = date.today().isoformat()

SYSTEM = f"""You are a recipe data extractor. Given text extracted from a PDF recipe, extract structured data and return ONLY a valid markdown file in this exact format — no commentary, no code fences:

---
schema_version: 1
title: <title>
url: null
source: <publication/site name or null>
image: null
servings: <number or null>
prep_minutes: <number or null>
cook_minutes: <number or null>
imported_at: {TODAY}
ingredients:
  - <ingredient 1>
  - <ingredient 2>
steps:
  - <step 1>
  - <step 2>
---

# <title>

*Source: <source>*

## Ingredients

- <ingredient 1>

## Instructions

1. <step 1>

Rules:
- ingredients: flat list of strings, each a complete ingredient line
- steps: flat list of strings, each a complete instruction step (no numbering)
- If you can't extract ingredients or steps, use: ingredients: null / steps: null
- title: clean human-readable recipe title
- Remove all nav text, ads, page headers/footers, photo captions, nutrition tables
- If the PDF contains multiple recipes, extract the primary/title recipe only"""


def extract_pdf_text(pdf_path):
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n\n".join(text_parts)


def llm_extract(text):
    payload = json.dumps({
        "model": "anthropic/claude-haiku-4-5",
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text[:50000]},  # cap at ~50k chars
        ],
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def main():
    if len(sys.argv) < 3:
        print("Usage: pdf_to_recipe.py <pdf_path> <output_recipe.md>")
        sys.exit(1)

    pdf_path, out_path = sys.argv[1], sys.argv[2]
    print(f">> {os.path.basename(pdf_path)} ...")
    text = extract_pdf_text(pdf_path)
    if not text.strip():
        print("  WARNING: no text extracted (scanned/image PDF?)")
        sys.exit(1)
    result = llm_extract(text)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result + "\n")
    print(f"   OK written to {out_path}")


if __name__ == "__main__":
    main()
