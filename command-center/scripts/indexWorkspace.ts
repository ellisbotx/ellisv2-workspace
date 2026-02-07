import dotenv from "dotenv";

dotenv.config({ path: ".env.local" });

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api";

const DEFAULT_ROOT = "/Users/ellisbot/.openclaw/workspace";

async function* walk(dir: string): AsyncGenerator<string> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    if (e.name === "node_modules" || e.name === ".git" || e.name === ".next" || e.name === "dist") continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      yield* walk(p);
    } else {
      yield p;
    }
  }
}

function classify(p: string): "memory" | "scheduled_tasks" | "document" {
  const norm = p.replaceAll("\\", "/");
  if (norm.endsWith("/MEMORY.md") || norm.includes("/memory/")) return "memory";
  if (norm.endsWith("/SCHEDULED_TASKS.md")) return "scheduled_tasks";
  return "document";
}

async function main() {
  const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;
  if (!convexUrl) throw new Error("Missing NEXT_PUBLIC_CONVEX_URL in env (.env.local)");
  const root = process.env.WORKSPACE_ROOT ?? DEFAULT_ROOT;

  const client = new ConvexHttpClient(convexUrl);

  let count = 0;
  for await (const filePath of walk(root)) {
    if (!filePath.endsWith(".md") && !filePath.endsWith(".txt")) continue;
    // Skip very large files
    const stat = await fs.stat(filePath);
    if (stat.size > 2_000_000) continue;

    const content = await fs.readFile(filePath, "utf8");
    const rel = path.relative(root, filePath).replaceAll("\\", "/");
    await client.mutation(api.documents.upsert, {
      path: rel,
      docType: classify(filePath),
      content,
      updatedAtMs: stat.mtimeMs,
    });
    count++;
  }

  console.log(`Indexed ${count} files from ${root}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
