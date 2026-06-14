/*
 * Recipe Box — pure data helpers (no DOM).
 * Loaded in the browser as window.RecipeLib, and in Node via require() for tests.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.RecipeLib = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var EXPORT_FORMAT = "recipe-box";
  var EXPORT_VERSION = 1;

  function uid() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return "r-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
  }

  function asArray(value) {
    if (value == null) return [];
    return Array.isArray(value) ? value : [value];
  }

  function cleanLines(value) {
    return asArray(value)
      .map(function (v) { return String(v).trim(); })
      .filter(Boolean);
  }

  function cleanTags(value) {
    var parts;
    if (Array.isArray(value)) {
      parts = value.map(String);
    } else if (typeof value === "string") {
      parts = value.split(",");
    } else {
      parts = [];
    }
    var seen = {};
    return parts
      .map(function (t) { return t.trim().toLowerCase(); })
      .filter(function (t) { return t && !seen[t] && (seen[t] = true); });
  }

  /* Build a well-formed recipe object from loosely-shaped input. */
  function normalizeRecipe(raw) {
    if (!raw || typeof raw !== "object") return null;
    var title = String(raw.title || raw.name || "").trim();
    if (!title) return null;
    return {
      id: typeof raw.id === "string" && raw.id ? raw.id : uid(),
      title: title,
      description: String(raw.description || "").trim(),
      image: String(raw.image || raw.imageUrl || "").trim(),
      servings: String(raw.servings || raw.yield || "").trim(),
      prepTime: String(raw.prepTime || "").trim(),
      cookTime: String(raw.cookTime || "").trim(),
      ingredients: cleanLines(raw.ingredients),
      steps: cleanLines(raw.steps || raw.instructions || raw.directions),
      tags: cleanTags(raw.tags),
      notes: String(raw.notes || "").trim(),
      source: String(raw.source || raw.url || "").trim(),
      createdAt: raw.createdAt || new Date().toISOString(),
      updatedAt: raw.updatedAt || new Date().toISOString()
    };
  }

  /* ---- schema.org Recipe (JSON-LD) support ---- */

  function isSchemaRecipe(obj) {
    if (!obj || typeof obj !== "object") return false;
    var type = obj["@type"];
    return asArray(type).indexOf("Recipe") !== -1;
  }

  function schemaText(value) {
    if (value == null) return "";
    if (typeof value === "string") return value;
    if (Array.isArray(value)) return schemaText(value[0]);
    if (typeof value === "object") return schemaText(value.text || value.name || value.url || value["@id"] || "");
    return String(value);
  }

  function schemaSteps(instructions) {
    var steps = [];
    asArray(instructions).forEach(function (item) {
      if (item && typeof item === "object" && asArray(item["@type"]).indexOf("HowToSection") !== -1) {
        steps = steps.concat(schemaSteps(item.itemListElement));
      } else {
        var text = schemaText(item);
        if (text) steps.push(text);
      }
    });
    return steps;
  }

  function fromSchemaRecipe(obj) {
    return normalizeRecipe({
      title: schemaText(obj.name),
      description: schemaText(obj.description),
      image: schemaText(obj.image),
      servings: schemaText(obj.recipeYield),
      prepTime: humanDuration(schemaText(obj.prepTime)),
      cookTime: humanDuration(schemaText(obj.cookTime)),
      ingredients: asArray(obj.recipeIngredient || obj.ingredients).map(schemaText),
      steps: schemaSteps(obj.recipeInstructions),
      tags: typeof obj.keywords === "string" ? obj.keywords : asArray(obj.keywords).map(schemaText),
      source: schemaText(obj.url || obj.mainEntityOfPage)
    });
  }

  /* ISO-8601 durations (PT1H30M) -> "1 h 30 min"; anything else passes through. */
  function humanDuration(value) {
    var m = /^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?/.exec(String(value || "").trim());
    if (!m || (!m[1] && !m[2] && !m[3])) return String(value || "");
    var parts = [];
    if (m[1]) parts.push(m[1] + " d");
    if (m[2]) parts.push(m[2] + " h");
    if (m[3]) parts.push(m[3] + " min");
    return parts.join(" ");
  }

  /* ---- Markdown recipe import ----
   * Reverses toMarkdown(), and also reads recipe files like this project's
   * `recipes/*.md`: optional YAML frontmatter, a "# Title" heading,
   * "## Ingredients" / "## Instructions" lists, and optional
   * "## Notes" / "## Timeline" / "## Images" / "## Source" sections.
   */

  function extractRef(text) {
    var m = /!\[[^\]]*\]\(([^)\s]+)\)/.exec(text);
    if (m) return m[1];
    m = /<(https?:\/\/[^>]+)>/.exec(text);
    if (m) return m[1];
    m = /(https?:\/\/\S+)/.exec(text);
    if (m) return m[1];
    return text.trim();
  }

  /* Turn list-ish lines (bullets, numbered items, wrapped continuations)
     into one entry per item. Sub-headings (###...) are dropped. */
  function parseListItems(lines) {
    var items = [];
    lines.forEach(function (line) {
      var m = /^\s*(?:[-*+]|\d+[.)])\s+(.*)$/.exec(line);
      if (m) {
        items.push(m[1].trim());
      } else if (/^\s*#{1,6}\s/.test(line)) {
        return; // sub-heading inside a list section, not an item
      } else if (line.trim()) {
        if (items.length) items[items.length - 1] += " " + line.trim();
        else items.push(line.trim());
      }
    });
    return items.filter(Boolean);
  }

  /* "*Servings: 4 · Prep: 10 min · Cook: 25 min*" -> { servings, prepTime, cookTime } */
  function parseMetaLine(text) {
    var meta = {};
    var found = false;
    text.split("·").forEach(function (part) {
      var m = /^\s*(Servings|Prep|Cook)\s*:\s*(.+?)\s*$/i.exec(part);
      if (!m) return;
      found = true;
      var key = m[1].toLowerCase();
      if (key === "servings") meta.servings = m[2];
      else if (key === "prep") meta.prepTime = m[2];
      else if (key === "cook") meta.cookTime = m[2];
    });
    return found ? meta : null;
  }

  var MD_SECTIONS = {
    ingredients: "ingredients",
    instructions: "steps",
    steps: "steps",
    directions: "steps",
    notes: "notes",
    timeline: "timeline",
    images: "images",
    source: "source"
  };

  /* Parse a single recipe out of a markdown block into raw normalizeRecipe() input. */
  function fromMarkdownRecipe(block) {
    var raw = { tags: [] };
    var section = null;
    var buckets = { intro: [], ingredients: [], steps: [], notes: [], timeline: [], images: [], source: [] };

    block.split(/\r?\n/).forEach(function (line) {
      var h1 = /^#\s+(.+)$/.exec(line);
      if (h1 && !raw.title) {
        raw.title = h1[1].trim();
        return;
      }
      var h2 = /^##\s+(.+)$/.exec(line);
      if (h2) {
        var name = h2[1].trim().toLowerCase();
        section = MD_SECTIONS[name] || "notes";
        if (!MD_SECTIONS[name]) buckets.notes.push("**" + h2[1].trim() + "**");
        return;
      }
      var trimmed = line.trim();
      var sourceMatch = /^\*?Source:\s*(.+?)\*?$/i.exec(trimmed);
      if (sourceMatch) {
        buckets.source.push(sourceMatch[1]);
        return;
      }
      var tagsMatch = /^Tags:\s*(.+)$/i.exec(trimmed);
      if (tagsMatch) {
        raw.tags = tagsMatch[1];
        return;
      }
      if (!section) {
        var starred = /^\*(.+)\*$/.exec(trimmed);
        var meta = starred && parseMetaLine(starred[1]);
        if (meta) {
          if (meta.servings) raw.servings = meta.servings;
          if (meta.prepTime) raw.prepTime = meta.prepTime;
          if (meta.cookTime) raw.cookTime = meta.cookTime;
          return;
        }
      }
      buckets[section || "intro"].push(line);
    });

    raw.description = buckets.intro.join("\n").trim();
    raw.ingredients = parseListItems(buckets.ingredients);
    raw.steps = parseListItems(buckets.steps);

    var notes = [];
    if (buckets.notes.join("").trim()) notes.push(buckets.notes.join("\n").trim());
    if (buckets.timeline.join("").trim()) notes.push("Timeline:\n" + buckets.timeline.join("\n").trim());
    raw.notes = notes.join("\n\n");

    var images = parseListItems(buckets.images);
    if (images.length) raw.image = extractRef(images[0]);

    if (buckets.source.length) raw.source = extractRef(buckets.source.join(" ").trim());

    return raw;
  }

  /* Split markdown into recipe blocks (toMarkdown() joins multiple recipes
     with a "---" rule), strip any leading YAML frontmatter, and normalize each. */
  function fromMarkdown(text) {
    var body = String(text || "").replace(/^﻿/, "");
    var frontmatter = /^---\r?\n[\s\S]*?\r?\n---\r?\n?/.exec(body);
    if (frontmatter) body = body.slice(frontmatter[0].length);
    var recipes = [];
    body.split(/\r?\n-{3,}\r?\n/).forEach(function (block) {
      if (!block.trim()) return;
      var recipe = normalizeRecipe(fromMarkdownRecipe(block));
      if (recipe) recipes.push(recipe);
    });
    return recipes;
  }

  /* Pull recipe candidates out of any parsed-JSON shape. */
  function collectCandidates(data, out) {
    if (!data || typeof data !== "object") return;
    if (Array.isArray(data)) {
      data.forEach(function (item) { collectCandidates(item, out); });
      return;
    }
    if (data["@graph"]) {
      collectCandidates(data["@graph"], out);
      return;
    }
    if (isSchemaRecipe(data)) {
      out.push(fromSchemaRecipe(data));
      return;
    }
    if (data["@type"]) return; // typed JSON-LD node that isn't a Recipe
    if (Array.isArray(data.recipes)) {
      data.recipes.forEach(function (item) { collectCandidates(item, out); });
      return;
    }
    out.push(normalizeRecipe(data));
  }

  /*
   * Parse the text of an imported file. Accepts:
   *  - a Recipe Box export (object with recipes/collections arrays)
   *  - a bare array of recipes, or a single recipe object
   *  - schema.org Recipe JSON-LD (single, array, or @graph)
   *  - Markdown: either toMarkdown() output, or recipe files like this
   *    project's `recipes/*.md` ("# Title", "## Ingredients", etc.,
   *    with optional YAML frontmatter)
   * Returns { recipes, collections }; throws on unparseable input.
   */
  function parseImport(text) {
    var trimmed = String(text || "").trim();
    var recipes = [];
    var collections = [];
    if (trimmed.charAt(0) === "{" || trimmed.charAt(0) === "[") {
      var data = JSON.parse(text);
      collectCandidates(data, recipes);
      recipes = recipes.filter(Boolean);
      if (data && !Array.isArray(data) && Array.isArray(data.collections)) {
        collections = data.collections
          .map(function (c) {
            if (!c || typeof c !== "object" || !c.name) return null;
            return {
              id: typeof c.id === "string" && c.id ? c.id : uid(),
              name: String(c.name).trim(),
              recipeIds: cleanLines(c.recipeIds)
            };
          })
          .filter(Boolean);
      }
    } else {
      recipes = fromMarkdown(text);
    }
    if (!recipes.length) {
      throw new Error("No recipes found in file (need at least a title/name per recipe, or a '# Title' heading for Markdown).");
    }
    return { recipes: recipes, collections: collections };
  }

  /*
   * Merge imported data into existing data.
   * Recipes matching an existing id, or an existing title (case-insensitive),
   * are skipped as duplicates. Returns { recipes, collections, added, skipped }.
   */
  function mergeImport(existing, imported) {
    var byId = {};
    var byTitle = {};
    existing.recipes.forEach(function (r) {
      byId[r.id] = true;
      byTitle[r.title.toLowerCase()] = true;
    });
    var added = [];
    var skipped = 0;
    imported.recipes.forEach(function (r) {
      if (byId[r.id] || byTitle[r.title.toLowerCase()]) {
        skipped++;
        return;
      }
      byId[r.id] = true;
      byTitle[r.title.toLowerCase()] = true;
      added.push(r);
    });
    var recipes = existing.recipes.concat(added);
    var validIds = {};
    recipes.forEach(function (r) { validIds[r.id] = true; });

    var collections = existing.collections.slice();
    var collNames = {};
    collections.forEach(function (c) { collNames[c.name.toLowerCase()] = c; });
    (imported.collections || []).forEach(function (c) {
      var ids = c.recipeIds.filter(function (id) { return validIds[id]; });
      var current = collNames[c.name.toLowerCase()];
      if (current) {
        ids.forEach(function (id) {
          if (current.recipeIds.indexOf(id) === -1) current.recipeIds.push(id);
        });
      } else {
        var copy = { id: c.id, name: c.name, recipeIds: ids };
        collections.push(copy);
        collNames[c.name.toLowerCase()] = copy;
      }
    });
    return { recipes: recipes, collections: collections, added: added.length, skipped: skipped };
  }

  function toExportJSON(recipes, collections) {
    return JSON.stringify(
      {
        format: EXPORT_FORMAT,
        version: EXPORT_VERSION,
        exportedAt: new Date().toISOString(),
        recipes: recipes,
        collections: collections || []
      },
      null,
      2
    );
  }

  function toMarkdown(recipes) {
    return recipes
      .map(function (r) {
        var lines = ["# " + r.title, ""];
        if (r.description) lines.push(r.description, "");
        var meta = [];
        if (r.servings) meta.push("Servings: " + r.servings);
        if (r.prepTime) meta.push("Prep: " + r.prepTime);
        if (r.cookTime) meta.push("Cook: " + r.cookTime);
        if (meta.length) lines.push("*" + meta.join(" · ") + "*", "");
        if (r.ingredients.length) {
          lines.push("## Ingredients", "");
          r.ingredients.forEach(function (i) { lines.push("- " + i); });
          lines.push("");
        }
        if (r.steps.length) {
          lines.push("## Steps", "");
          r.steps.forEach(function (s, idx) { lines.push(idx + 1 + ". " + s); });
          lines.push("");
        }
        if (r.notes) lines.push("## Notes", "", r.notes, "");
        if (r.source) lines.push("Source: " + r.source, "");
        if (r.tags.length) lines.push("Tags: " + r.tags.join(", "), "");
        return lines.join("\n");
      })
      .join("\n---\n\n");
  }

  return {
    uid: uid,
    normalizeRecipe: normalizeRecipe,
    parseImport: parseImport,
    mergeImport: mergeImport,
    toExportJSON: toExportJSON,
    toMarkdown: toMarkdown,
    fromMarkdown: fromMarkdown,
    humanDuration: humanDuration
  };
});
