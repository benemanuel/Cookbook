// to-markdown.mjs — recipe object → markdown string with YAML frontmatter.
// Body stays human-readable (your future-proof asset); structured data lives in frontmatter.

function yamlScalar(v) {
  if (v == null) return "null";
  if (typeof v === "number") return String(v);
  // quote strings that could confuse YAML
  if (/[:#\-?\[\]{}&*!|>'"%@`]/.test(v) || /^\s|\s$/.test(v)) {
    return JSON.stringify(v);
  }
  return v;
}

export function recipeToMarkdown(r, { schemaVersion = 1, imported_at = null } = {}) {
  const fm = [];
  fm.push("---");
  fm.push(`schema_version: ${schemaVersion}`);
  fm.push(`title: ${yamlScalar(r.title)}`);
  fm.push(`url: ${yamlScalar(r.url)}`);
  fm.push(`source: ${yamlScalar(r.source)}`);
  fm.push(`image: ${yamlScalar(r.image)}`);
  fm.push(`servings: ${r.servings == null ? "null" : r.servings}`);
  fm.push(`prep_minutes: ${r.prep_minutes == null ? "null" : r.prep_minutes}`);
  fm.push(`cook_minutes: ${r.cook_minutes == null ? "null" : r.cook_minutes}`);
  if (imported_at) fm.push(`imported_at: ${imported_at}`);
  // structured arrays
  if (r.ingredients?.length) {
    fm.push("ingredients:");
    for (const i of r.ingredients) fm.push(`  - ${yamlScalar(i)}`);
  } else fm.push("ingredients: null");
  if (r.steps?.length) {
    fm.push("steps:");
    for (const s of r.steps) fm.push(`  - ${yamlScalar(s)}`);
  } else fm.push("steps: null");
  fm.push("---");

  // human-readable body
  const body = [];
  body.push("", `# ${r.title}`, "");
  if (r.source) body.push(`*Source: ${r.source}*`, "");
  if (r.ingredients?.length) {
    body.push("## Ingredients", "");
    for (const i of r.ingredients) body.push(`- ${i}`);
    body.push("");
  }
  if (r.steps?.length) {
    body.push("## Instructions", "");
    r.steps.forEach((s, n) => body.push(`${n + 1}. ${s}`));
    body.push("");
  }
  return fm.join("\n") + "\n" + body.join("\n");
}
