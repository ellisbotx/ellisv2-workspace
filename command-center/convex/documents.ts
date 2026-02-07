import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const upsert = mutation({
  args: {
    path: v.string(),
    docType: v.union(v.literal("memory"), v.literal("document"), v.literal("scheduled_tasks")),
    content: v.string(),
    updatedAtMs: v.number(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("documents")
      .withIndex("by_path", (q) => q.eq("path", args.path))
      .unique();

    if (existing) {
      await ctx.db.patch(existing._id, {
        docType: args.docType,
        content: args.content,
        updatedAtMs: args.updatedAtMs,
      });
      return existing._id;
    }

    return await ctx.db.insert("documents", {
      path: args.path,
      docType: args.docType,
      content: args.content,
      updatedAtMs: args.updatedAtMs,
    });
  },
});

export const getByPath = query({
  args: { path: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("documents")
      .withIndex("by_path", (q) => q.eq("path", args.path))
      .unique();
  },
});

export const search = query({
  args: {
    term: v.string(),
    limit: v.optional(v.number()),
    docType: v.optional(v.union(v.literal("memory"), v.literal("document"), v.literal("scheduled_tasks"))),
  },
  handler: async (ctx, args) => {
    const limit = Math.min(Math.max(args.limit ?? 20, 1), 50);
    return await ctx.db
      .query("documents")
      .withSearchIndex("search_content", (q) => {
        let qq = q.search("content", args.term);
        if (args.docType) qq = qq.eq("docType", args.docType);
        return qq;
      })
      .take(limit);
  },
});

export const listRecent = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = Math.min(Math.max(args.limit ?? 50, 1), 200);
    const all = await ctx.db.query("documents").collect();
    return all.sort((a, b) => b.updatedAtMs - a.updatedAtMs).slice(0, limit);
  },
});
