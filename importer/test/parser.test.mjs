// parser.test.mjs — run with: node --test
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  parseRecipeFromHtml, isoDurationToMinutes,
  normalizeInstructions, normalizeImage, findRecipeNode,
} from "../parser.mjs";
import { recipeToMarkdown } from "../to-markdown.mjs";

const FX = join(dirname(fileURLToPath(import.meta.url)), "fixtures");
const fx = (f) => readFileSync(join(FX, f), "utf8");

test("ISO durations", () => {
  assert.equal(isoDurationToMinutes("PT20M"), 20);
  assert.equal(isoDurationToMinutes("PT1H30M"), 90);
  assert.equal(isoDurationToMinutes("P1DT2H"), 1560);
  assert.equal(isoDurationToMinutes("garbage"), null);
  assert.equal(isoDurationToMinutes(null), null);
});

test("JSON-LD @graph + HowToStep", () => {
  const r = parseRecipeFromHtml(fx("jsonld-graph-howtostep.html"), "https://www.daringgourmet.com/goulash/");
  assert.equal(r.title, "Hungarian Goulash");
  assert.equal(r.servings, 6);
  assert.equal(r.prep_minutes, 20);
  assert.equal(r.cook_minutes, 90);
  assert.equal(r.source, "daringgourmet.com");
  assert.equal(r.image, "https://x/goulash.jpg");
  assert.equal(r.ingredients.length, 3);
  assert.deepEqual(r.steps, ["Brown the beef.", "Add onions and paprika.", "Simmer 90 minutes."]);
});

test("HowToSection nesting + type array + image array", () => {
  const r = parseRecipeFromHtml(fx("jsonld-howtosection.html"), "https://x/cake");
  assert.equal(r.title, "Layered Cake");
  assert.equal(r.servings, 8);
  assert.equal(r.image, "https://x/a.jpg");
  assert.deepEqual(r.steps, ["Mix dry.", "Add wet.", "Bake at 180C."]);
});

test("microdata fallback", () => {
  const r = parseRecipeFromHtml(fx("microdata.html"), "https://x/marinara");
  assert.equal(r.title, "Simple Marinara");
  assert.equal(r.prep_minutes, 10);
  assert.equal(r.ingredients.length, 2);
  assert.ok(r.steps.length >= 1);
});

test("string instructions split into steps", () => {
  const r = parseRecipeFromHtml(fx("string-instructions.html"), "https://x/toast");
  assert.equal(r.title, "Quick Toast");
  assert.ok(r.steps.length >= 2);
});

test("no recipe → null", () => {
  assert.equal(parseRecipeFromHtml(fx("no-recipe.html"), "https://x/article"), null);
});

test("markdown output well-formed", () => {
  const r = parseRecipeFromHtml(fx("jsonld-graph-howtostep.html"), "https://www.daringgourmet.com/goulash/");
  const md = recipeToMarkdown(r, { imported_at: "2026-05-31" });
  assert.match(md, /^---\n/);
  assert.match(md, /schema_version: 1/);
  assert.match(md, /title: Hungarian Goulash/);
  assert.match(md, /cook_minutes: 90/);
  assert.match(md, /^# Hungarian Goulash$/m);
  assert.match(md, /## Ingredients/);
  assert.match(md, /1\. Brown the beef\./);
  // frontmatter must have exactly two --- fences
  assert.equal((md.match(/^---$/gm) || []).length, 2);
});

test("findRecipeNode digs through arrays and graph", () => {
  assert.equal(findRecipeNode([{ "@type": "X" }, { "@type": "Recipe", name: "n" }]).name, "n");
  assert.equal(findRecipeNode({ "@graph": [{ "@type": "Recipe", name: "g" }] }).name, "g");
  assert.equal(findRecipeNode({ "@type": "Article" }), null);
});
