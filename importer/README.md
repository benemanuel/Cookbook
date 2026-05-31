# Recipe URL Importer

Fetches recipes from source URLs, parses schema.org/Recipe (JSON-LD or microdata),
and writes markdown files with YAML frontmatter. Falls back to the Wayback Machine
when a live page is dead (important for older recipes).

## Why this runs on YOUR machine
The parser is fully tested offline. The *fetch* step needs open network access to
recipe sites and archive.org, so run the live import locally — not in a restricted
sandbox.

## Install
    cd importer
    npm install        # installs cheerio

## Use
Single URL (prints markdown to stdout):
    node import-urls.mjs "https://www.daringgourmet.com/.../goulash/"

Batch from the triage list (key<TAB>url per line), writing files:
    node import-urls.mjs --list ../out/needs-url-import.txt --out ../recipes-imported --delay 1500

- --out DIR   write <key>.md per recipe + _import-log.json (review failures here)
- --delay MS  politeness delay between requests (default 1200)

## How fallback works
1. Fetch live URL → parse. If a Recipe is found, done.
2. On HTTP error / dead host / no-schema → query Wayback availability API,
   fetch nearest snapshot, parse that. Canonical `url` stays the original.
3. Still nothing → logged as fail for manual handling.

## Test
    node --test

## Notes / honest limits
- Sites without schema.org markup return null (logged as fail) — those need the
  LLM-cleanup path, not this importer.
- Review _import-log.json: `via` tells you live vs wayback vs fail.
- Imported files land in a separate dir; diff/review before merging into recipes/.
