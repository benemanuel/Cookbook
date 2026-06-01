# Recipe Audit Command

Audit all recipes in the `recipes/` directory and report issues.

## IMPORTANT

**Always run the script below. Do not analyze recipe files yourself.**
The script is the source of truth. Do not summarize, interpret, or add checks beyond what it reports.

## Steps

1. Run the audit script:
```bash
node scripts/audit-recipes.js
```

2. Show the full raw output to the user without modification.

3. If asked to fix something specific (e.g. a typo, a duplicate), make that change and re-run the script to confirm the issue is resolved.

4. After any cleanup, regenerate the search index:
```bash
python build_index.py
python add_labels.py
```

## What the script checks

1. PDF files in recipes/ — renderer cannot display them
2. Non-.md, non-.pdf files in recipes/
3. Duplicates — same base name with _N suffix
4. Non-recipe files — no Ingredients AND no Instructions in content (content-based, not filename-based)
5. Structural issues — stub files (<200 chars), or missing one required section
6. Filename typos — checked only on confirmed recipe files
7. Imperial measurements — oz, lb, °F etc. flagged for conversion to metric

## Notes

- Hebrew section headers (מצרכים, הכנה, הוראות) are recognized alongside English
- The script does NOT modify any files — it only reports
- Pipe output to a file if you want to save it: `node scripts/audit-recipes.js > audit-report.txt`