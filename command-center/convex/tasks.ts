import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const upsert = mutation({
  args: {
    name: v.string(),
    source: v.union(v.literal("SCHEDULED_TASKS.md"), v.literal("openclaw"), v.literal("manual")),
    cron: v.optional(v.string()),
    scheduleText: v.optional(v.string()),
    status: v.optional(
      v.union(v.literal("upcoming"), v.literal("running"), v.literal("completed"), v.literal("failed"))
    ),
    lastRunAtMs: v.optional(v.number()),
    lastOutcome: v.optional(v.union(v.literal("success"), v.literal("failed"), v.literal("partial"))),
    nextRunAtMs: v.optional(v.number()),
    tags: v.optional(v.array(v.string())),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("tasks")
      .withSearchIndex("search_name", (q) => q.search("name", args.name).eq("source", args.source))
      .take(1);

    if (existing[0]) {
      await ctx.db.patch(existing[0]._id, {
        cron: args.cron,
        scheduleText: args.scheduleText,
        status: args.status ?? existing[0].status,
        lastRunAtMs: args.lastRunAtMs,
        lastOutcome: args.lastOutcome,
        nextRunAtMs: args.nextRunAtMs,
        tags: args.tags,
        metadata: args.metadata,
      });
      return existing[0]._id;
    }

    return await ctx.db.insert("tasks", {
      name: args.name,
      source: args.source,
      cron: args.cron,
      scheduleText: args.scheduleText,
      status: args.status ?? "upcoming",
      lastRunAtMs: args.lastRunAtMs,
      lastOutcome: args.lastOutcome,
      nextRunAtMs: args.nextRunAtMs,
      tags: args.tags,
      metadata: args.metadata,
    });
  },
});

export const listWeek = query({
  args: {
    weekStartMs: v.number(),
    weekEndMs: v.number(),
  },
  handler: async (ctx, args) => {
    // Pull all tasks that have a nextRunAt in the week window.
    // (If we later track recurring occurrences, we'd materialize runs.)
    const all = await ctx.db.query("tasks").collect();
    return all
      .filter((t) => t.nextRunAtMs != null && t.nextRunAtMs >= args.weekStartMs && t.nextRunAtMs < args.weekEndMs)
      .sort((a, b) => (a.nextRunAtMs ?? 0) - (b.nextRunAtMs ?? 0));
  },
});

export const search = query({
  args: {
    term: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = Math.min(Math.max(args.limit ?? 20, 1), 50);
    return await ctx.db
      .query("tasks")
      .withSearchIndex("search_name", (q) => q.search("name", args.term))
      .take(limit);
  },
});

export const all = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("tasks").collect();
  },
});
