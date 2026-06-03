# Format Recipe Command

Reformat a recipe file to match the standard template and conventions of this cookbook.

## Usage

`/format-recipe <filename>`

If no filename is given, ask the user which file to format.

## Template (from recipe-template.md)

```markdown
# Recipe Title

A description of the recipe (or even better an image).

## Ingredients

A list with all ingredients. Can use all markdown feature including "smaller"
headings.

## Instructions

A list with the instructions. Can use all markdown feature including "smaller"
headings.

## Timeline

A list with working timeline (optional).

## Notes

A list with notes (optional).

## Images

A list with images (optional).
```

## What to fix

1. **YAML frontmatter** — Ensure a `---` frontmatter block exists with at minimum:
   - `title:` (human-readable name)
   - `labels:` (array, can be empty `[]` if none apply)
   - Preserve any existing fields (`url`, `source`, `servings`, `prep_minutes`, `cook_minutes`, etc.)

2. **Title** — `# Recipe Title` as the first heading in the body (after frontmatter). Use the recipe's real name, not forwarded-email subject lines like "Fwd: ...".

3. **Ingredients section** — Must have `## Ingredients` (or `## מרכיבים` for Hebrew). Format as a bullet list. Group into subsections with `###` if the recipe has distinct components.

4. **Instructions section** — Must have `## Instructions` (or `## הוראות הכנה` for Hebrew). Format as a numbered list. Group into `###` subsections if needed.

5. **Measurements** — Convert all imperial to metric:
   - °F → °C (formula: (F−32)×5/9, round to nearest degree)
   - oz → g (1 oz = 28g)
   - lb → kg/g (1 lb = 454g)
   - cups → ml (1 cup = 240ml)
   - tablespoons → ml (1 tbsp = 15ml)
   - teaspoons → ml (1 tsp = 5ml)
   - inches → cm (1 inch = 2.54cm)

6. **Remove noise** — Strip forwarded-email boilerplate, "—— Forwarded message ——", signatures, URLs in the instructions body (keep them in frontmatter `url:` field).

7. **Timeline section** — If the recipe has a multi-step schedule (e.g. overnight fermentation, multi-day process), collect it under `## Timeline`. Omit if the recipe is straightforward.

8. **Notes section** — Collect tips, substitutions, serving suggestions, and "why it works" commentary under `## Notes`. Omit if there are none.

9. **Images section** — Add `## Images` only if there are actual image links to list; omit if empty.

## After formatting

1. Write the corrected content back to the file.
2. Run:
   ```bash
   python build_index.py
   python add_labels.py
   ```
3. Confirm with the user that the result looks correct before committing.
