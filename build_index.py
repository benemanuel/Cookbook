#!/usr/bin/env python3
"""Build search-index.json from all recipe markdown files."""

import json
import os
import re

RECIPES_DIR = "recipes"
OUTPUT = "search-index.json"


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end]
    rest = text[end + 3:].strip()
    fm = {}
    for line in fm_block.splitlines():
        m = re.match(r'^(\w+):\s*(.+)', line.strip())
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                items = [i.strip().strip('"\'') for i in val[1:-1].split(',') if i.strip()]
                fm[key] = items
            else:
                fm[key] = val.strip('"\'')
    return fm, rest


def extract_title(body):
    m = re.search(r'^#\s+(.+)', body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def clean_text(body):
    # Remove markdown syntax for cleaner search text
    text = re.sub(r'!\[.*?\]\(.*?\)', '', body)   # images
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links → text
    text = re.sub(r'#{1,6}\s+', '', text)          # headings
    text = re.sub(r'[*_`~>]', '', text)            # formatting
    text = re.sub(r'\s+', ' ', text)               # whitespace
    return text.strip().lower()


def main():
    index = []
    recipes_path = RECIPES_DIR

    for filename in sorted(os.listdir(recipes_path)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(recipes_path, filename)
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        fm, body = parse_frontmatter(content)
        title = extract_title(body) or fm.get("subject", filename[:-3])
        labels = fm.get("labels", [])
        if isinstance(labels, str):
            labels = [labels]
        text = clean_text(body)
        file_key = filename[:-3]  # strip .md

        index.append({
            "file": file_key,
            "title": title,
            "labels": labels,
            "text": text,
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Built {OUTPUT} with {len(index)} recipes.")


if __name__ == "__main__":
    main()
