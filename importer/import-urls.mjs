#!/usr/bin/env node
// import-urls.mjs — fetch recipes (live, then Wayback fallback), parse, write markdown.
//
// Usage:
//   node import-urls.mjs <url>                       # single, prints to stdout
//   node import-urls.mjs --list needs-url-import.txt # batch (tab: key<TAB>url)
//   node import-urls.mjs --list f.txt --out ../recipes-imported --delay 1500
//
// Runs on YOUR machine (needs open network). Sandbox network is allowlisted and
// cannot reach recipe sites or archive.org — that's why fetch is isolated here.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { parseRecipeFromHtml } from "./parser.mjs";
import { recipeToMarkdown } from "./to-markdown.mjs";

const UA = "Mozilla/5.0 (compatible; PersonalCookbookImporter/1.0)";

async function fetchText(url, timeoutMs = 15000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, { headers: { "User-Agent": UA }, signal: ctrl.signal, redirect: "follow" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.text();
  } finally { clearTimeout(t); }
}

// Wayback availability API → nearest snapshot URL, or null.
async function waybackUrl(url) {
  try {
    const api = `https://archive.org/wayback/available?url=${encodeURIComponent(url)}`;
    const res = await fetch(api, { headers: { "User-Agent": UA } });
    const j = await res.json();
    const snap = j?.archived_snapshots?.closest;
    return snap?.available ? snap.url : null;
  } catch { return null; }
}

// Try live; on any failure or no-recipe-found, try Wayback snapshot.
export async function importOne(url) {
  let html, via = "live";
  try {
    html = await fetchText(url);
    const r = parseRecipeFromHtml(html, url);
    if (r) return { recipe: r, via };
  } catch (e) { via = `live-failed (${e.message})`; }

  const wb = await waybackUrl(url);
  if (wb) {
    try {
      html = await fetchText(wb);
      const r = parseRecipeFromHtml(html, url); // keep ORIGINAL url as canonical
      if (r) return { recipe: r, via: `wayback (${wb})` };
    } catch (e) { return { recipe: null, via: `wayback-failed (${e.message})` }; }
  }
  return { recipe: null, via: `${via}; no recipe schema found` };
}

function slug(s) { return s.replace(/[^\w\u0590-\u05FF]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 80); }

async function main() {
  const args = process.argv.slice(2);
  const listIdx = args.indexOf("--list");
  const outIdx = args.indexOf("--out");
  const delayIdx = args.indexOf("--delay");
  const outDir = outIdx !== -1 ? args[outIdx + 1] : null;
  const delay = delayIdx !== -1 ? parseInt(args[delayIdx + 1], 10) : 1200;

  if (listIdx === -1) {
    const url = args[0];
    if (!url) { console.error("usage: node import-urls.mjs <url> | --list file.txt [--out dir] [--delay ms]"); process.exit(1); }
    const { recipe, via } = await importOne(url);
    if (!recipe) { console.error("FAIL:", via); process.exit(2); }
    console.error("OK via", via);
    console.log(recipeToMarkdown(recipe, { imported_at: new Date().toISOString().slice(0, 10) }));
    return;
  }

  const lines = readFileSync(args[listIdx + 1], "utf8").split("\n").map((l) => l.trim()).filter(Boolean);
  if (outDir && !existsSync(outDir)) mkdirSync(outDir, { recursive: true });
  const log = [];
  let ok = 0, fail = 0;
  for (const line of lines) {
    const [key, url] = line.includes("\t") ? line.split("\t") : [slug(line), line];
    process.stderr.write(`→ ${key} ... `);
    const { recipe, via } = await importOne(url);
    if (recipe) {
      ok++;
      const md = recipeToMarkdown(recipe, { imported_at: new Date().toISOString().slice(0, 10) });
      if (outDir) writeFileSync(join(outDir, `${key}.md`), md, "utf8");
      console.error(`OK (${via})`);
      log.push({ key, url, status: "ok", via });
    } else {
      fail++; console.error(`FAIL (${via})`);
      log.push({ key, url, status: "fail", via });
    }
    await new Promise((r) => setTimeout(r, delay)); // be polite to servers
  }
  if (outDir) writeFileSync(join(outDir, "_import-log.json"), JSON.stringify(log, null, 2));
  console.error(`\nDone. ok=${ok} fail=${fail}. Review failures in _import-log.json`);
}

main().catch((e) => { console.error(e); process.exit(1); });
