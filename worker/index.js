const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, X-Api-Key",
};

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // GET /ratings — return all ratings
    if (request.method === "GET" && path === "/ratings") {
      const data = await env.RATINGS.get("ratings");
      return new Response(data ?? "{}", {
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    // POST /ratings/:recipe — add a rating (requires API key)
    const postMatch = path.match(/^\/ratings\/(.+)$/);
    if (request.method === "POST" && postMatch) {
      const apiKey = request.headers.get("X-Api-Key");
      if (!apiKey || apiKey !== env.API_KEY) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
          status: 401,
          headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
        });
      }

      const recipe = decodeURIComponent(postMatch[1]);
      let body;
      try {
        body = await request.json();
      } catch {
        return new Response(JSON.stringify({ error: "Invalid JSON" }), {
          status: 400,
          headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
        });
      }

      const score = parseInt(body.rating);
      if (!score || score < 1 || score > 5) {
        return new Response(JSON.stringify({ error: "Rating must be 1–5" }), {
          status: 400,
          headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
        });
      }

      const existing = JSON.parse((await env.RATINGS.get("ratings")) ?? "{}");
      const entry = existing[recipe] ?? { avg: 0, count: 0, ratings: [] };
      entry.ratings.push(score);
      entry.count = entry.ratings.length;
      entry.avg = Math.round((entry.ratings.reduce((a, b) => a + b, 0) / entry.count) * 10) / 10;
      existing[recipe] = entry;

      await env.RATINGS.put("ratings", JSON.stringify(existing));

      return new Response(JSON.stringify(existing[recipe]), {
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    return new Response("Not found", { status: 404, headers: CORS_HEADERS });
  },
};
