/* Node smoke tests for lib.js: run with `node test-lib.js` */
"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const Lib = require("./lib.js");

// 1. Sample data parses and round-trips through export/import
const sampleText = fs.readFileSync(path.join(__dirname, "sample-recipes.json"), "utf8");
const sample = Lib.parseImport(sampleText);
assert.strictEqual(sample.recipes.length, 3);
assert.strictEqual(sample.collections.length, 1);
assert.strictEqual(sample.recipes[0].title, "Shakshuka");
assert.ok(sample.recipes[0].ingredients.length > 5);

const exported = Lib.toExportJSON(sample.recipes, sample.collections);
const reimported = Lib.parseImport(exported);
assert.deepStrictEqual(reimported.recipes, sample.recipes);
assert.deepStrictEqual(reimported.collections, sample.collections);

// 2. Bare array and single-object imports
assert.strictEqual(Lib.parseImport('[{"title":"A"},{"name":"B"}]').recipes.length, 2);
assert.strictEqual(Lib.parseImport('{"title":"Solo","ingredients":"1 egg"}').recipes[0].ingredients[0], "1 egg");

// 3. schema.org Recipe JSON-LD (incl. @graph, HowToStep, HowToSection, ISO durations)
const jsonld = JSON.stringify({
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "WebPage", "name": "ignored" },
    {
      "@type": "Recipe",
      "name": "Site Pancakes",
      "image": ["https://example.com/p.jpg"],
      "recipeYield": "4 servings",
      "prepTime": "PT15M",
      "cookTime": "PT1H30M",
      "keywords": "breakfast, quick",
      "recipeIngredient": ["1 cup flour", "1 egg"],
      "recipeInstructions": [
        { "@type": "HowToStep", "text": "Mix everything." },
        {
          "@type": "HowToSection",
          "name": "Frying",
          "itemListElement": [{ "@type": "HowToStep", "text": "Fry until golden." }]
        }
      ]
    }
  ]
});
const ld = Lib.parseImport(jsonld);
assert.strictEqual(ld.recipes.length, 1);
const r = ld.recipes[0];
assert.strictEqual(r.title, "Site Pancakes");
assert.strictEqual(r.image, "https://example.com/p.jpg");
assert.strictEqual(r.prepTime, "15 min");
assert.strictEqual(r.cookTime, "1 h 30 min");
assert.deepStrictEqual(r.tags, ["breakfast", "quick"]);
assert.deepStrictEqual(r.steps, ["Mix everything.", "Fry until golden."]);

// 4. Merge skips duplicates by id and by title, keeps collections consistent
const existing = { recipes: sample.recipes, collections: sample.collections };
const incoming = Lib.parseImport(JSON.stringify({
  recipes: [
    { id: "sample-shakshuka", title: "Shakshuka v2" }, // dup by id
    { title: "tahini cookies" },                        // dup by title (case-insensitive)
    { id: "new-1", title: "Brand New Dish" }
  ],
  collections: [
    { id: "c-new", name: "Weeknight favorites", recipeIds: ["new-1", "missing-id"] }
  ]
}));
const merged = Lib.mergeImport(existing, incoming);
assert.strictEqual(merged.added, 1);
assert.strictEqual(merged.skipped, 2);
assert.strictEqual(merged.recipes.length, 4);
assert.strictEqual(merged.collections.length, 1); // merged into existing collection by name
assert.ok(merged.collections[0].recipeIds.includes("new-1"));
assert.ok(!merged.collections[0].recipeIds.includes("missing-id"));

// 5. Invalid input throws
assert.throws(() => Lib.parseImport("[]"));
assert.throws(() => Lib.parseImport('[{"noTitle":true}]'));
assert.throws(() => Lib.parseImport("not json"));

// 6. Markdown export contains the essentials
const md = Lib.toMarkdown(sample.recipes);
assert.ok(md.includes("# Shakshuka"));
assert.ok(md.includes("## Ingredients"));
assert.ok(md.includes("1. Heat the olive oil"));

// 7. Markdown export round-trips back through parseImport
const fromMd = Lib.parseImport(md);
assert.strictEqual(fromMd.recipes.length, sample.recipes.length);
assert.strictEqual(fromMd.recipes[0].title, "Shakshuka");
assert.deepStrictEqual(fromMd.recipes[0].ingredients, sample.recipes[0].ingredients);
assert.deepStrictEqual(fromMd.recipes[0].steps, sample.recipes[0].steps);
assert.deepStrictEqual(fromMd.recipes[0].tags, sample.recipes[0].tags);
assert.strictEqual(fromMd.recipes[0].servings, sample.recipes[0].servings);
assert.strictEqual(fromMd.recipes[0].prepTime, sample.recipes[0].prepTime);
assert.strictEqual(fromMd.recipes[0].cookTime, sample.recipes[0].cookTime);
assert.strictEqual(fromMd.recipes[1].notes, sample.recipes[1].notes);

// 8. Markdown recipe in this project's `recipes/*.md` style: YAML frontmatter,
//    "## Instructions" (not "## Steps"), "## Notes", "## Timeline", "## Images",
//    and a "## Source" section with a bare link.
const cookbookStyle = `---
title: French Lentil Salad
labels: [dairy, fish]
---

# French Lentil Salad

A hearty, tangy salad.

## Ingredients

### For the salad

- 200g French green lentils
- 1 bay leaf

### For the dressing

- 30ml olive oil
- 15ml red wine vinegar

## Instructions

1. Cook the lentils.
2. Whisk the dressing.
3. Toss together.

## Timeline

**Morning** — Cook the lentils ahead of time.

## Notes

- Best served at room temperature.

## Images

![salad](images/lentil-salad.jpg)

## Source

<https://example.com/lentil-salad>
`;
const cb = Lib.parseImport(cookbookStyle);
assert.strictEqual(cb.recipes.length, 1);
const cbRecipe = cb.recipes[0];
assert.strictEqual(cbRecipe.title, "French Lentil Salad");
assert.strictEqual(cbRecipe.description, "A hearty, tangy salad.");
assert.deepStrictEqual(cbRecipe.ingredients, [
  "200g French green lentils",
  "1 bay leaf",
  "30ml olive oil",
  "15ml red wine vinegar"
]);
assert.deepStrictEqual(cbRecipe.steps, [
  "Cook the lentils.",
  "Whisk the dressing.",
  "Toss together."
]);
assert.ok(cbRecipe.notes.includes("Best served at room temperature."));
assert.ok(cbRecipe.notes.includes("Timeline:"));
assert.ok(cbRecipe.notes.includes("Morning"));
assert.strictEqual(cbRecipe.image, "images/lentil-salad.jpg");
assert.strictEqual(cbRecipe.source, "https://example.com/lentil-salad");

// 9. Multiple recipes in one Markdown file, separated by "---"
const multi = Lib.parseImport(`# First\n\n## Ingredients\n\n- a\n\n---\n\n# Second\n\n## Ingredients\n\n- b\n`);
assert.strictEqual(multi.recipes.length, 2);
assert.strictEqual(multi.recipes[0].title, "First");
assert.strictEqual(multi.recipes[1].title, "Second");

console.log("All lib.js tests passed.");
