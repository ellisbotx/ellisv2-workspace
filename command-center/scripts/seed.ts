import dotenv from "dotenv";

dotenv.config({ path: ".env.local" });

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import { CronExpressionParser } from "cron-parser";
import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api";

const WORKSPACE_ROOT = process.env.WORKSPACE_ROOT ?? "/Users/ellisbot/.openclaw/workspace";
const TZ = "America/Chicago";

function nextFromCron(cron: string, now = new Date()): number | undefined {
  try {
    const it = CronExpressionParser.parse(cron, { tz: TZ, currentDate: now });
    return it.next().getTime();
  } catch {
    return undefined;
  }
}

async function seedTasks(client: ConvexHttpClient) {
  // Baseline tasks (requirements)
  const now = new Date();
  const tasks = [
    {
      name: "Daily ASIN checks",
      source: "manual" as const,
      cron: "0 1 * * *",
      scheduleText: "Every day at 1:00 AM CST",
    },
    {
      name: "Weekly memory consolidation",
      source: "manual" as const,
      cron: "0 20 * * 0",
      scheduleText: "Sundays at 8:00 PM CST",
    },
  ];

  for (const t of tasks) {
    await client.mutation(api.tasks.upsert, {
      name: t.name,
      source: t.source,
      cron: t.cron,
      scheduleText: t.scheduleText,
      status: "upcoming",
      nextRunAtMs: nextFromCron(t.cron, now),
      metadata: { seeded: true, tz: TZ },
    });
  }

  // Parse SCHEDULED_TASKS.md if present
  const schedPath = path.join(WORKSPACE_ROOT, "SCHEDULED_TASKS.md");
  try {
    const content = await fs.readFile(schedPath, "utf8");
    // Minimal heuristic parsing: store the doc itself (document indexing script does this too)
    // and add one task per heading/bullet that looks like a schedule line.
    const lines = content.split(/\r?\n/);
    for (const line of lines) {
      const m = line.match(/^\s*[-*]\s+(.*)$/);
      if (!m) continue;
      const name = m[1].trim();
      if (!name) continue;
      // Avoid noisy entries
      if (name.length < 6) continue;
      await client.mutation(api.tasks.upsert, {
        name,
        source: "SCHEDULED_TASKS.md",
        scheduleText: "From SCHEDULED_TASKS.md",
        status: "upcoming",
        metadata: { sourceLine: line },
      });
    }
  } catch {
    // ok
  }
}

async function seedActivities(client: ConvexHttpClient) {
  // Parse yesterday memory log for recent activities if present.
  const p = path.join(WORKSPACE_ROOT, "memory", "2026-02-05.md");
  try {
    const content = await fs.readFile(p, "utf8");
    const lines = content.split(/\r?\n/).filter(Boolean);
    // very lightweight: log first N non-empty lines as "File Updated"/"Task Completed" items
    const now = Date.now();
    const sample = lines.slice(0, 30);
    for (let i = 0; i < sample.length; i++) {
      await client.mutation(api.activities.log, {
        timestampMs: now - (30 - i) * 60_000,
        timezone: TZ,
        agent: "Ellis",
        actionType: "Seeded From Memory",
        description: sample[i],
        outcome: "partial",
        related: ["memory/2026-02-05.md"],
        metadata: { seeded: true },
      });
    }
  } catch {
    // ok
  }
}

async function main() {
  const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;
  if (!convexUrl) throw new Error("Missing NEXT_PUBLIC_CONVEX_URL in env (.env.local)");
  const client = new ConvexHttpClient(convexUrl);

  await seedTasks(client);
  await seedActivities(client);

  console.log("Seed complete");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
