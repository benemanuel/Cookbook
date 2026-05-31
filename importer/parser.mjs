// parser.mjs — pure HTML→Recipe extraction. No network. Fully unit-testable.
import * as cheerio from "cheerio";

// ISO-8601 duration (PT1H30M) → minutes. Returns null if unparseable.
export function isoDurationToMinutes(d) {
  if (!d || typeof d !== "string") return null;
  const m = d.match(/^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?/);
  if (!m) return null;
  const [, days, hours, mins] = m.map((x) => (x ? parseInt(x, 10) : 0));
  const total = days * 1440 + hours * 60 + mins;
  return total > 0 ? total : null;
}

// schema.org instructions come in many shapes: string, array of strings,
// array of HowToStep objects, or HowToSection with nested itemListElement.
export function normalizeInstructions(ri) {
  if (!ri) return [];
  if (typeof ri === "string") {
    return ri.split(/\r?\n|\.\s+(?=[A-Z])/).map((s) => s.trim()).filter(Boolean);
  }
  const out = [];
  const walk = (node) => {
    if (!node) return;
    if (typeof node === "string") { const t = node.trim(); if (t) out.push(t); return; }
    if (Array.isArray(node)) { node.forEach(walk); return; }
    if (node["@type"] === "HowToSection" && node.itemListElement) { walk(node.itemListElement); return; }
    if (node.text) { const t = String(node.text).trim(); if (t) out.push(t); return; }
    if (node.name) { const t = String(node.name).trim(); if (t) out.push(t); }
  };
  walk(ri);
  return out;
}

export function normalizeImage(img) {
  if (!img) return null;
  if (typeof img === "string") return img;
  if (Array.isArray(img)) return normalizeImage(img[0]);
  if (img.url) return img.url;
  return null;
}

function normalizeYield(y) {
  if (y == null) return null;
  if (Array.isArray(y)) y = y.find((v) => v != null);
  if (typeof y === "number") return y;
  const m = String(y).match(/\d+/);
  return m ? parseInt(m[0], 10) : null;
}

// Find the Recipe node inside any JSON-LD shape (@graph, arrays, nested types).
export function findRecipeNode(json) {
  const isRecipe = (n) => {
    const t = n && n["@type"];
    return t === "Recipe" || (Array.isArray(t) && t.includes("Recipe"));
  };
  const stack = [json];
  while (stack.length) {
    const n = stack.pop();
    if (!n || typeof n !== "object") continue;
    if (isRecipe(n)) return n;
    if (Array.isArray(n)) { stack.push(...n); continue; }
    if (Array.isArray(n["@graph"])) stack.push(...n["@graph"]);
    for (const k of Object.keys(n)) {
      if (typeof n[k] === "object") stack.push(n[k]);
    }
  }
  return null;
}

// Main: HTML string → normalized recipe object, or null if no Recipe schema.
export function parseRecipeFromHtml(html, sourceUrl = null) {
  const $ = cheerio.load(html);
  let node = null;

  // 1) JSON-LD (preferred)
  $('script[type="application/ld+json"]').each((_, el) => {
    if (node) return;
    const raw = $(el).contents().text();
    if (!raw) return;
    try {
      node = findRecipeNode(JSON.parse(raw));
    } catch {
      // some sites emit multiple concatenated objects or trailing commas; try lenient
      try { node = findRecipeNode(JSON.parse(raw.replace(/,\s*([}\]])/g, "$1"))); } catch {}
    }
  });

  // 2) Microdata fallback
  if (!node) {
    const scope = $('[itemtype*="schema.org/Recipe"]').first();
    if (scope.length) {
      const prop = (p) => scope.find(`[itemprop="${p}"]`).map((_, e) => $(e).attr("content") || $(e).text().trim()).get();
      node = {
        name: prop("name")[0],
        recipeIngredient: prop("recipeIngredient"),
        recipeInstructions: prop("recipeInstructions"),
        image: prop("image")[0],
        recipeYield: prop("recipeYield")[0],
        prepTime: scope.find('[itemprop="prepTime"]').attr("datetime"),
        cookTime: scope.find('[itemprop="cookTime"]').attr("datetime"),
      };
    }
  }

  if (!node || !node.name) return null;

  return {
    title: String(node.name).trim(),
    url: sourceUrl,
    source: sourceUrl ? safeHost(sourceUrl) : null,
    image: normalizeImage(node.image),
    servings: normalizeYield(node.recipeYield),
    prep_minutes: isoDurationToMinutes(node.prepTime),
    cook_minutes: isoDurationToMinutes(node.cookTime),
    ingredients: Array.isArray(node.recipeIngredient)
      ? node.recipeIngredient.map((s) => String(s).trim()).filter(Boolean)
      : (node.recipeIngredient ? [String(node.recipeIngredient).trim()] : []),
    steps: normalizeInstructions(node.recipeInstructions),
  };
}

function safeHost(u) { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return null; } }
