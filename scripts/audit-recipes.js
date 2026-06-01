#!/usr/bin/env node
// audit-recipes.js — Recipe collection health check
// Usage: node scripts/audit-recipes.js
// Or:    node scripts/audit-recipes.js > audit-report.txt

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RECIPES_DIR = path.join(__dirname, '..', 'recipes');

// ── Section header regexes (Hebrew + English) ─────────────────────────────────

const INGREDIENTS_RE  = /^##\s+(Ingredients|מצרכים|רכיבים|חומרים)/im;
const INSTRUCTIONS_RE = /^##\s+(Instructions|Directions|Method|Steps|הכנה|הוראות|אופן הכנה)/im;
const H1_RE           = /^#\s+.+/m;
const ANY_H2_RE       = /^##\s+.+/m;

// ── Typo map (filename only, applied after content read confirms it's a recipe) ──

const TYPO_MAP = {
  'Formented':  'Fermented',
  'kamucha':    'Kombucha',
  'fugie':      'Fudgy',
  'Yougrt':     'Yogurt',
  'vegtables':  'Vegetables',
  'Shepard':    "Shepherd's",
  'musaka':     'Moussaka',
  'mozarella':  'Mozzarella',
  'Biroche':    'Brioche',
  'berakos':    'Burekas',
};

// ── Imperial measurement detection ───────────────────────────────────────────
// Matches units that strongly indicate imperial/US measurements in recipe text.
// oz/lb are most reliable; cups/tbsp/tsp are used in both systems but flagged
// since Israeli home cooks generally work in grams/ml.
// Temperatures: °F or explicit Fahrenheit values (e.g. 350F, 375 degrees F).
// False positives: "fl oz" in drink recipes, "cup" as a vessel description.

const IMPERIAL_UNITS_RE = /\b(\d[\d./]*\s*(?:oz|lb|lbs|ounce|ounces|pound|pounds|fluid ounce)s?)\b/i;
const IMPERIAL_CUPS_RE  = /\b(\d[\d./]*\s*(?:cup|cups|tbsp|tsp|tablespoon|teaspoon)s?)\b/i;
const FAHRENHEIT_RE     = /\b(\d{2,3})\s*°?\s*F\b|\b(\d{2,3})\s+degrees?\s+F(ahrenheit)?\b/i;

// ── Colour helpers ────────────────────────────────────────────────────────────

const bold   = s => `\x1b[1m${s}\x1b[0m`;
const red    = s => `\x1b[31m${s}\x1b[0m`;
const yellow = s => `\x1b[33m${s}\x1b[0m`;
const green  = s => `\x1b[32m${s}\x1b[0m`;
const dim    = s => `\x1b[2m${s}\x1b[0m`;

function stripFrontmatter(content) {
  if (content.startsWith('---')) {
    const end = content.indexOf('\n---', 3);
    if (end !== -1) return content.slice(end + 4);
  }
  return content;
}

function baseKey(filename) {
  return filename.replace(/\.md$/, '').replace(/_\d+$/, '').toLowerCase().trim();
}

function section(title) {
  console.log('\n' + bold('═'.repeat(60)));
  console.log(bold(`  ${title}`));
  console.log(bold('═'.repeat(60)));
}

function item(icon, label, detail = '') {
  const d = detail ? dim(`  →  ${detail}`) : '';
  console.log(`  ${icon}  ${label}${d}`);
}

// ── Read all files once ───────────────────────────────────────────────────────

if (!fs.existsSync(RECIPES_DIR)) {
  console.error(red(`recipes/ directory not found at: ${RECIPES_DIR}`));
  console.error('Run this script from the project root, or from scripts/ inside the repo.');
  process.exit(1);
}

const allFiles = fs.readdirSync(RECIPES_DIR).sort();
const mdFiles  = allFiles.filter(f => f.endsWith('.md'));
const pdfFiles = allFiles.filter(f => f.toLowerCase().endsWith('.pdf'));
const other    = allFiles.filter(f => !f.endsWith('.md') && !f.toLowerCase().endsWith('.pdf'));

// Read every .md file once; derive all checks from content
const parsed = mdFiles.map(filename => {
  const raw     = fs.readFileSync(path.join(RECIPES_DIR, filename), 'utf8');
  const content = stripFrontmatter(raw);
  const lower   = content.toLowerCase();
  const len     = content.trim().length;

  const hasIngredients  = INGREDIENTS_RE.test(content);
  const hasInstructions = INSTRUCTIONS_RE.test(content);
  const hasH1           = H1_RE.test(content);
  const hasAnyH2        = ANY_H2_RE.test(content);
  const isStub          = len < 200;

  // A file is a real recipe if it has both Ingredients and Instructions sections.
  // Stubs and single-section files are flagged separately, not as "non-recipes".
  const isRecipe = hasIngredients && hasInstructions && !isStub;

  // Non-recipe: has no recipe structure at all (not just missing one section)
  const isNonRecipe = !hasIngredients && !hasInstructions && !isStub;

  // Imperial measurements — collect the actual matching strings for display
  const imperialMatches = [];
  if (isRecipe) {
    // Scan line by line so we can report which line, and collect unique matches
    const seen = new Set();
    for (const line of content.split('\n')) {
      const l = line.trim();
      if (!l) continue;
      for (const re of [IMPERIAL_UNITS_RE, IMPERIAL_CUPS_RE, FAHRENHEIT_RE]) {
        const m = l.match(re);
        if (m) {
          const key = m[0].trim().toLowerCase();
          if (!seen.has(key)) {
            seen.add(key);
            imperialMatches.push(m[0].trim());
          }
        }
      }
    }
  }
  const hasImperial = imperialMatches.length > 0;

  // Typos — only flag if it's actually a recipe (avoid noise on non-recipe files)
  const typos = isRecipe
    ? Object.entries(TYPO_MAP).filter(([typo]) => filename.includes(typo))
    : [];

  return {
    filename, content, lower, len,
    hasIngredients, hasInstructions, hasH1, hasAnyH2,
    isStub, isRecipe, isNonRecipe, hasImperial, imperialMatches, typos,
  };
});

console.log(bold(`\n🔍 Recipe Audit — ${new Date().toLocaleDateString()}`));
console.log(dim(`   Scanning: ${RECIPES_DIR}`));
console.log(dim(`   Total files: ${allFiles.length}  (${mdFiles.length} .md, ${pdfFiles.length} .pdf, ${other.length} other)`));

// ── 1. PDFs ───────────────────────────────────────────────────────────────────
section('1. PDF files in recipes/ (renderer cannot display these)');
if (pdfFiles.length === 0) {
  console.log(green('  ✓ None'));
} else {
  pdfFiles.forEach(f => item('📄', red(f), 'Remove or convert to .md'));
}

// ── 2. Other non-.md files ────────────────────────────────────────────────────
if (other.length > 0) {
  section('2. Non-.md, non-.pdf files in recipes/');
  other.forEach(f => item('❓', yellow(f)));
}

// ── 3. Duplicates ─────────────────────────────────────────────────────────────
section('3. Duplicates (same base name with _N suffix)');
const groups = {};
mdFiles.forEach(f => {
  const k = baseKey(f);
  (groups[k] = groups[k] || []).push(f);
});
const dupes = Object.entries(groups).filter(([, v]) => v.length > 1);
if (dupes.length === 0) {
  console.log(green('  ✓ None'));
} else {
  dupes.forEach(([key, files]) => {
    console.log(`\n  ${yellow('⚠')}  ${bold(key)}  (${files.length} copies)`);
    files.forEach(f => console.log(`       ${dim(f)}`));
  });
  console.log(`\n  ${dim(`Total duplicate groups: ${dupes.length}`)}`);
}

// ── 4. Non-recipe files (content-based) ───────────────────────────────────────
section('4. Non-recipe files (no Ingredients AND no Instructions in content)');
const nonRecipes = parsed.filter(p => p.isNonRecipe);
if (nonRecipes.length === 0) {
  console.log(green('  ✓ None'));
} else {
  nonRecipes.forEach(({ filename, len, hasAnyH2 }) => {
    const hint = hasAnyH2 ? 'has headings but no recipe structure' : 'plain text / article';
    item('📰', yellow(filename), `${hint}  (${len} chars)`);
  });
}

// ── 5. Structural issues ──────────────────────────────────────────────────────
section('5. Structural issues (stub, or missing one required section)');
const structIssues = parsed.filter(p =>
  !p.isNonRecipe && (p.isStub || !p.hasIngredients || !p.hasInstructions)
);
if (structIssues.length === 0) {
  console.log(green('  ✓ All non-stub files have both sections'));
} else {
  structIssues.forEach(({ filename, hasIngredients, hasInstructions, hasH1, isStub, len }) => {
    const flags = [
      isStub            ? red('STUB')              : null,
      !hasH1            ? yellow('no title')        : null,
      !hasIngredients   ? yellow('no Ingredients')  : null,
      !hasInstructions  ? yellow('no Instructions') : null,
    ].filter(Boolean).join(', ');
    item('⚠', filename, `${flags}  (${len} chars)`);
  });
}

// ── 6. Typos in filenames (only for confirmed recipes) ────────────────────────
section('6. Likely typos in filenames (confirmed recipes only)');
const typoFound = parsed.filter(p => p.typos.length > 0);
if (typoFound.length === 0) {
  console.log(green('  ✓ None detected'));
} else {
  typoFound.forEach(({ filename, typos }) => {
    typos.forEach(([typo, correct]) => {
      item('✏', filename, `"${red(typo)}" → "${green(correct)}"`);
    });
  });
}

// ── 7. Imperial measurements (confirmed recipes only) ─────────────────────────
section('7. Imperial measurements — needs conversion to metric');
const imperialFiles = parsed.filter(p => p.hasImperial);
if (imperialFiles.length === 0) {
  console.log(green('  ✓ None detected'));
} else {
  imperialFiles.forEach(({ filename, imperialMatches }) => {
    // Show up to 5 sample matches so the line doesn't get too long
    const sample = imperialMatches.slice(0, 5).join(', ');
    const more   = imperialMatches.length > 5 ? ` (+${imperialMatches.length - 5} more)` : '';
    item('📐', filename, `${sample}${more}`);
  });
  console.log(dim('\n  Note: cups/tbsp/tsp may be intentional in some recipes. Review before converting.'));
}

// ── 8. Summary ────────────────────────────────────────────────────────────────
section('Summary');
const totalIssues =
  pdfFiles.length + other.length + dupes.length +
  nonRecipes.length + structIssues.length + typoFound.length + imperialFiles.length;

console.log(`  Total .md recipe files:  ${bold(mdFiles.length)}`);
console.log(`  PDF files in recipes/:   ${pdfFiles.length > 0 ? red(pdfFiles.length) : green(0)}`);
console.log(`  Duplicate groups:        ${dupes.length > 0 ? yellow(dupes.length) : green(0)}`);
console.log(`  Non-recipe files:        ${nonRecipes.length > 0 ? yellow(nonRecipes.length) : green(0)}`);
console.log(`  Structural issues:       ${structIssues.length > 0 ? yellow(structIssues.length) : green(0)}`);
console.log(`  Filename typos:          ${typoFound.length > 0 ? yellow(typoFound.length) : green(0)}`);
console.log(`  Imperial measurements:   ${imperialFiles.length > 0 ? yellow(imperialFiles.length) : green(0)}`);
console.log('');
if (totalIssues === 0) {
  console.log(green('  ✓ Collection looks clean!'));
} else {
  console.log(yellow(`  ${totalIssues} issue groups to review.`));
}
console.log('');