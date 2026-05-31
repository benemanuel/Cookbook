#!/usr/bin/env node
/**
 * triage.mjs — classify every recipe in recipes/ into actionable buckets.
 *
 * Buckets:
 *   FULL   → has real ingredients AND instructions in the body.
 *            Action: paste-ready text written to out/vinst/<name>.txt (beautify via Vinst).
 *   STUB   → title/blurb/metadata only, no real recipe content.
 *            Action: if a source URL exists in body → URL-importer; else manual.
 *   PDF    → content lives in an attachment PDF (present on disk).
 *            Action: extract PDF text, then re-triage.
 *   CLEAN  → already has structured-enough content; Vinst likely unnecessary.
 *
 * Output:
 *   out/triage-report.json   full machine-readable classification
 *   out/triage-report.csv    quick human scan (file, bucket, has_url, has_pdf, reason)
 *   out/vinst/<name>.txt      paste-ready text, FULL bucket only
 *   out/needs-url-import.txt  list of files + their source URL (STUB/PDF with url)
 *
 * No credentials. No network. No account access. Pure local classification.
 * Idempotent: rewrites out/ each run, never touches recipes/.
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync, rmSync } from "node:fs";
import { join } from "node:path";

const RECIPES_DIR = "recipes";
const ATTACH_DIR = "attachments";
const OUT = "out";

// ---------- frontmatter + body parsing ----------
function splitFrontmatter(text) {
  if (!text.startsWith("---")) return { fm: {}, body: text };
  const end = text.indexOf("\n---", 3);
  if (end === -1) return { fm: {}, body: text };
  const fmBlock = text.slice(3, end);
  const body = text.slice(end + 4).replace(/^\s+/, "");
  // light YAML: top-level "key: value" + nested "attachments:" presence
  const fm = {};
  for (const line of fmBlock.split("\n")) {
    const m = line.match(/^([a-z_]+):\s*(.*)$/i);
    if (m) fm[m[1]] = m[2].trim();
  }
  return { fm, body };
}

function getSection(body, names) {
  // returns text under any ## header whose name matches, until next ## or EOF
  const lines = body.split("\n");
  let capturing = false;
  const out = [];
  for (const line of lines) {
    const h = line.match(/^##\s+(.+?)\s*$/);
    if (h) {
      capturing = names.some((n) => h[1].toLowerCase().includes(n));
      continue;
    }
    if (capturing) out.push(line);
  }
  return out.join("\n").trim();
}

function firstUrl(body) {
  const m = body.match(/https?:\/\/[^\s)<>"']+/);
  return m ? m[0] : null;
}

// real content = non-empty, not just a header, more than a couple words
function isSubstantive(section) {
  const stripped = section
    .replace(/^[-*\d.\s]+/gm, "")  // list markers
    .replace(/\s+/g, " ")
    .trim();
  // require at least ~4 words and a digit OR multiple list lines
  const wordCount = stripped.split(" ").filter(Boolean).length;
  const listLines = section.split("\n").filter((l) => /^\s*[-*\d]/.test(l)).length;
  return wordCount >= 4 || listLines >= 2;
}

// ---------- attachment / pdf detection ----------
const attachDirs = existsSync(ATTACH_DIR) ? readdirSync(ATTACH_DIR) : [];
function findPdfFor(fileKey) {
  // attachment dirs look like "<RecipeKey>_<n>"; match by prefix
  const candidates = attachDirs.filter((d) => d.startsWith(fileKey + "_") || d === fileKey);
  for (const d of candidates) {
    const p = join(ATTACH_DIR, d);
    try {
      const inner = readdirSync(p);
      const pdf = inner.find((f) => f.toLowerCase().endsWith(".pdf"));
      if (pdf) return join(p, pdf);
    } catch { /* not a dir */ }
  }
  return null;
}

// ---------- main ----------
if (existsSync(OUT)) rmSync(OUT, { recursive: true, force: true });
mkdirSync(join(OUT, "vinst"), { recursive: true });

const files = readdirSync(RECIPES_DIR).filter((f) => f.endsWith(".md")).sort();
const report = [];
const needsUrl = [];
const counts = { FULL: 0, STUB: 0, PDF: 0, CLEAN: 0 };

for (const filename of files) {
  const fileKey = filename.slice(0, -3);
  const raw = readFileSync(join(RECIPES_DIR, filename), "utf8");
  const { fm, body } = splitFrontmatter(raw);

  const ingredients = getSection(body, ["ingredient", "מצרכים", "רכיבים"]);
  const instructions = getSection(body, ["instruction", "method", "directions", "הוראות", "אופן"]);
  const hasIng = isSubstantive(ingredients);
  const hasInst = isSubstantive(instructions);
  const url = firstUrl(body);
  const pdf = "attachments" in fm ? findPdfFor(fileKey) : null;

  let bucket, reason;
  if (hasIng && hasInst) {
    // both present → is it already clean (good lists) or just full-but-messy?
    const ingLists = ingredients.split("\n").filter((l) => /^\s*[-*\d]/.test(l)).length;
    const instLists = instructions.split("\n").filter((l) => /^\s*[-*\d]/.test(l)).length;
    if (ingLists >= 3 && instLists >= 2) {
      bucket = "CLEAN"; reason = "structured ingredients + steps present";
    } else {
      bucket = "FULL"; reason = "real content, prose-ish → good Vinst candidate";
    }
  } else if (pdf) {
    bucket = "PDF"; reason = `content likely in PDF: ${pdf}`;
  } else if (!hasIng && !hasInst) {
    bucket = "STUB"; reason = url ? "stub w/ source url → URL import" : "stub, no url → manual";
  } else {
    bucket = "FULL"; reason = "partial content → Vinst candidate";
  }

  counts[bucket]++;
  report.push({ file: fileKey, bucket, has_url: !!url, url, has_pdf: !!pdf, pdf, reason,
                title: fm.subject || fileKey });

  if (bucket === "FULL" || bucket === "CLEAN") {
    const title = fm.subject || fileKey.replace(/_/g, " ");
    const paste = [
      title, "",
      ingredients ? "Ingredients:\n" + ingredients : "",
      instructions ? "\nInstructions:\n" + instructions : "",
    ].filter(Boolean).join("\n");
    writeFileSync(join(OUT, "vinst", fileKey + ".txt"), paste, "utf8");
  }
  if ((bucket === "STUB" || bucket === "PDF") && url) {
    needsUrl.push(`${fileKey}\t${url}`);
  }
}

writeFileSync(join(OUT, "triage-report.json"), JSON.stringify(report, null, 2), "utf8");
const csv = ["file,bucket,has_url,has_pdf,reason",
  ...report.map((r) => `"${r.file}",${r.bucket},${r.has_url},${r.has_pdf},"${r.reason.replace(/"/g, "'")}"`)
].join("\n");
writeFileSync(join(OUT, "triage-report.csv"), csv, "utf8");
writeFileSync(join(OUT, "needs-url-import.txt"), needsUrl.join("\n"), "utf8");

console.log("Triage complete:", counts);
console.log(`FULL/CLEAN paste files: out/vinst/  (${counts.FULL + counts.CLEAN})`);
console.log(`STUB/PDF with source URL → out/needs-url-import.txt  (${needsUrl.length})`);
console.log(`Reports: out/triage-report.json, out/triage-report.csv`);
