#!/usr/bin/env node
// llm-cleanup.mjs — use Claude API to extract structured frontmatter from messy recipe files.
// Usage: node llm-cleanup.mjs <recipe.md> [recipe2.md ...]
// Writes output to ../recipes/<filename> (overwrites).

import fs from "fs";
import path from "path";
const apiKey = process.env.ANTHROPIC_API_KEY;
const isOpenRouter = apiKey?.startsWith("sk-or-");
const today = new Date().toISOString().slice(0, 10);

const SYSTEM = `You are a recipe data extractor. Given a messy recipe markdown file, extract structured data and return ONLY a valid markdown file in this exact format — no commentary, no code fences:

---
schema_version: 1
title: <title>
url: <url or null>
source: <domain or null>
image: null
servings: <number or null>
prep_minutes: <number or null>
cook_minutes: <number or null>
imported_at: ${today}
ingredients:
  - <ingredient 1>
  - <ingredient 2>
steps:
  - <step 1>
  - <step 2>
---

# <title>

*Source: <domain>*

## Ingredients

- <ingredient 1>

## Instructions

1. <step 1>

Rules:
- ingredients: flat list of strings, each a complete ingredient line
- steps: flat list of strings, each a complete instruction step (no numbering)
- If you can't extract ingredients or steps, use: ingredients: null / steps: null
- Preserve the URL from the original if present
- title: clean human-readable title (no site name suffix unless it's part of the recipe name)
- Keep image: null (we don't reuse scraped images from messy files)
- Remove all nav text, ads, review sections, photo captions, nutrition tables`;

async function processFile(filePath) {
  const content = fs.readFileSync(filePath, "utf8");
  const filename = path.basename(filePath);
  console.log(`→ ${filename} ...`);

  let result;
  if (isOpenRouter) {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: { "Authorization": `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "anthropic/claude-haiku-4-5",
        max_tokens: 4096,
        messages: [
          { role: "system", content: SYSTEM },
          { role: "user", content },
        ],
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(JSON.stringify(data));
    result = data.choices[0].message.content.trim();
  } else {
    const { default: Anthropic } = await import("@anthropic-ai/sdk");
    const client = new Anthropic({ apiKey });
    const msg = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 4096,
      system: SYSTEM,
      messages: [{ role: "user", content }],
    });
    result = msg.content[0].text.trim();
  }
  const outPath = path.resolve(path.dirname(filePath), "..", "recipes", filename);
  fs.writeFileSync(outPath, result + "\n", "utf8");
  console.log(`   ✓ written to recipes/${filename}`);
}

const files = process.argv.slice(2);
if (!files.length) {
  console.error("Usage: node llm-cleanup.mjs <file.md> [file2.md ...]");
  process.exit(1);
}

for (const f of files) {
  await processFile(path.resolve(f));
}
console.log("Done.");
