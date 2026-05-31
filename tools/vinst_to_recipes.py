#!/usr/bin/env python3
"""
Batch-convert vinst .txt files to structured recipe markdown via LLM.

For matched stubs: overwrites the existing recipe file.
For unmatched:     creates a new recipe file.
Already-structured recipes (schema_version present) are skipped.

Usage:
  python vinst_to_recipes.py [--dry-run] [--limit N] [--skip-existing]
"""

import os, sys, re, json, time, urllib.request, argparse
from datetime import date
from pathlib import Path

VINST_DIR   = Path(r'C:\Users\avi\GitHub\Cookbook\tools\vinst')
RECIPES_DIR = Path(r'C:\Users\avi\GitHub\Cookbook\recipes')
LOG_PATH    = Path(r'C:\Users\avi\GitHub\Cookbook\tools\vinst_import_log.json')
TODAY       = date.today().isoformat()
API_KEY     = os.environ["ANTHROPIC_API_KEY"]

SYSTEM = f"""You are a recipe data extractor. Given the text of a recipe (from a saved webpage or app export), extract structured data and return ONLY a valid markdown file in this exact format — no commentary, no code fences, no extra text:

---
schema_version: 1
title: <clean recipe title>
url: <url if present in the text, else null>
source: <domain or publication name, else null>
image: null
servings: <number or null>
prep_minutes: <number or null>
cook_minutes: <number or null>
imported_at: {TODAY}
ingredients:
  - <ingredient 1>
  - <ingredient 2>
steps:
  - <step 1 as a complete sentence>
  - <step 2 as a complete sentence>
---

# <clean recipe title>

*Source: <source>*

## Ingredients

- <ingredient 1>
- <ingredient 2>

## Instructions

1. <step 1>
2. <step 2>

Rules:
- ingredients: flat list of strings, one item per line
- steps: flat list of complete instruction sentences, no numbering, no sub-bullets
- If you cannot extract structured ingredients or steps, use: ingredients: null / steps: null
- title: clean human-readable recipe title (remove site name suffix if it reads awkwardly)
- url: extract from the text if a source URL appears
- source: domain or publication name (e.g. "allrecipes.com", "The Guardian")
- Remove all navigation text, ads, review sections, photo captions, rating widgets, nutrition tables, social sharing buttons, and email signatures
- If the text is in Hebrew, extract in Hebrew but keep frontmatter keys in English"""


def llm_extract(text: str) -> str:
    payload = json.dumps({
        "model": "anthropic/claude-haiku-4-5",
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text[:60000]},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def sanitize_filename(name: str) -> str:
    """Remove characters unsafe for Windows filenames."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip('. ')
    return name[:200]  # cap length


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--skip-existing', action='store_true',
                        help='Skip vinst files that already have a non-stub recipe')
    args = parser.parse_args()

    recipe_map = {f[:-3]: Path(RECIPES_DIR, f)
                  for f in os.listdir(RECIPES_DIR) if f.endswith('.md')}

    vinst_files = sorted(f for f in os.listdir(VINST_DIR) if f.endswith('.txt'))

    # Load existing log
    log = {}
    if LOG_PATH.exists():
        log = json.loads(LOG_PATH.read_text(encoding='utf-8'))

    todo = []
    for vf in vinst_files:
        base = vf[:-4]
        existing = recipe_map.get(base)

        # Skip if already logged as ok
        if log.get(base) == 'ok':
            continue

        # Skip if existing recipe already has schema_version
        if existing and 'schema_version:' in existing.read_text(encoding='utf-8', errors='replace'):
            if args.skip_existing:
                continue
            log[base] = 'already_structured'
            continue

        todo.append((base, vf, existing))

    print(f"To process: {len(todo)} vinst files")
    if args.limit:
        todo = todo[:args.limit]
        print(f"Limited to: {len(todo)}")

    ok = fail = skip = 0

    for i, (base, vf, existing_path) in enumerate(todo, 1):
        src = VINST_DIR / vf
        # Output path: use existing recipe path or derive new one
        if existing_path:
            out_path = existing_path
        else:
            safe = sanitize_filename(base)
            out_path = RECIPES_DIR / f"{safe}.md"

        safe_base = base[:60].encode('ascii', errors='replace').decode('ascii')
        print(f"[{i}/{len(todo)}] {safe_base}", end=' ... ', flush=True)

        if args.dry_run:
            print("(dry run)")
            continue

        try:
            text = src.read_text(encoding='utf-8', errors='replace')
            if not text.strip():
                print("SKIP (empty)")
                log[base] = 'empty'
                skip += 1
                continue

            result = llm_extract(text)

            # Basic sanity: must start with ---
            if not result.startswith('---'):
                print("WARN (bad output, saving anyway)")

            out_path.write_text(result + "\n", encoding='utf-8')
            log[base] = 'ok'
            ok += 1
            print("ok")

        except Exception as e:
            print(f"FAIL: {e}")
            log[base] = f'fail: {e}'
            fail += 1

        # Save log every 10 items
        if i % 10 == 0:
            LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"  -- progress: {ok} ok, {fail} fail, {skip} skip --")

        time.sleep(0.3)  # light rate-limit courtesy

    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\nDone. ok={ok} fail={fail} skip={skip}")


if __name__ == '__main__':
    main()
