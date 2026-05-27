# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal recipe collection rendered as a static website. Recipes are markdown files with YAML frontmatter; `index.html` is a single-page app that fetches and renders them client-side. Deployed via GitHub Pages.

## Key commands

**Rebuild the search index** (run after adding/editing recipes):
```
python build_index.py
```

**Auto-label recipes** (adds/updates `labels:` frontmatter in all recipe files):
```
python add_labels.py
```

**Deploy the Cloudflare Worker** (ratings backend):
```
cd worker && npx wrangler deploy
```

There is no build step or test suite — the site is plain HTML/JS served directly from the repo root.

## Architecture

### Recipe format
Each recipe in `recipes/` is a `.md` file with optional YAML frontmatter:
```
---
labels: [bread, dairy]
subject: "Human-readable title (used if no # heading)"
---
# Recipe Title
...
## Ingredients
...
## Instructions
...
## Images   ← optional
```
The frontmatter `labels` field drives categorization and filtering. `build_index.py` strips frontmatter and generates `search-index.json` (title, labels, cleaned text per recipe).

### Frontend (`index.html`)
Single HTML file with inline CSS and JS. Two views:
- **List view** (`/`): fetches `search-index.json`, renders filterable/searchable recipe list with label chips. Ratings loaded async from the Worker after initial render.
- **Recipe view** (`/?recipe=<filename-without-.md>`): fetches the raw `.md`, parses it with `parseMarkdown()`, renders sections using `markdown-it`.

No bundler, no npm. Dependencies (`markdown-it`, `modern-normalize`, `water.css`) are vendored in `libs/`.

### Ratings backend (`worker/`)
Cloudflare Worker (`worker/index.js`) backed by KV storage (`RATINGS` binding). Two endpoints:
- `GET /ratings` — returns all ratings as `{ [recipeFile]: { avg, count, ratings[] } }`
- `POST /ratings/:recipe` — requires `X-Api-Key` header matching `env.API_KEY`

The Worker URL is hardcoded in `index.html` as `WORKER_URL`.

### Utility scripts
- `add_labels.py` — scores recipe content and filename against keyword dictionaries to assign labels; writes them back into each file's frontmatter. Handles English and Hebrew.
- `build_index.py` — generates `search-index.json` from all recipe files.
- `categorize.py`, `show_unlabeled.py`, `fix_suffixes.py`, `strip_prefixes.py` — one-off maintenance scripts.

## Recipe labels
Supported labels (defined in `add_labels.py`): `bread`, `cake`, `candy`, `dairy`, `fish`, `meat`. Each maps to an emoji in `index.html`'s `LABEL_EMOJI` constant.
