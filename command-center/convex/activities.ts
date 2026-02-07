import { paginationOptsValidator } from "convex/server";
import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const log = mutation({
  args: {
    timestampMs: v.optional(v.number()),
    timezone: v.optional(v.string()),
    agent: v.string(),
    actionType: v.string(),
    description: v.string(),
    outcome: v.union(v.literal("success"), v.literal("failed"), v.literal("partial")),
    related: v.optional(v.array(v.string())),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const timestampMs = args.timestampMs ?? Date.now();
    const timezone = args.timezone ?? "America/Chicago";
    return await ctx.db.insert("activities", {
      timestampMs,
      timezone,
      agent: args.agent,
      actionType: args.actionType,
      description: args.description,
      outcome: args.outcome,
      related: args.related,
      metadata: args.metadata,
    });
  },
});

export const list = query({
  args: {
    paginationOpts: paginationOptsValidator,
    // filters
    agent: v.optional(v.string()),
    actionType: v.optional(v.string()),
    outcome: v.optional(v.union(v.literal("success"), v.literal("failed"), v.literal("partial"))),
    fromMs: v.optional(v.number()),
    toMs: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    // For a simple, fast newest-first feed, we scan by timestamp index and filter in memory.
    // (Convex doesn't support range filtering on a different field without a composite index.)
    const page = await ctx.db
      .query("activities")
      .withIndex("by_timestamp")
      .order("desc")
      .paginate(args.paginationOpts);

    const filtered = page.page.filter((a) => {
      if (args.agent && a.agent !== args.agent) return false;
      if (args.actionType && a.actionType !== args.actionType) return false;
      if (args.outcome && a.outcome !== args.outcome) return false;
      if (args.fromMs && a.timestampMs < args.fromMs) return false;
      if (args.toMs && a.timestampMs > args.toMs) return false;
      return true;
    });

    return { ...page, page: filtered };
  },
});

export const search = query({
  args: {
    term: v.string(),
    limit: v.optional(v.number()),
    agent: v.optional(v.string()),
    actionType: v.optional(v.string()),
    outcome: v.optional(v.union(v.literal("success"), v.literal("failed"), v.literal("partial"))),
  },
  handler: async (ctx, args) => {
    const limit = Math.min(Math.max(args.limit ?? 20, 1), 50);
    const q = ctx.db
      .query("activities")
      .withSearchIndex("search_description", (q) => {
        let qq = q.search("description", args.term);
        if (args.agent) qq = qq.eq("agent", args.agent);
        if (args.actionType) qq = qq.eq("actionType", args.actionType);
        if (args.outcome) qq = qq.eq("outcome", args.outcome);
        return qq;
      })
      .take(limit);
    return await q;
  },
});
