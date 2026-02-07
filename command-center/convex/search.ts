import { v } from "convex/values";
import { query } from "./_generated/server";

export const global = query({
  args: {
    term: v.string(),
    limitPerType: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const term = args.term.trim();
    const limit = Math.min(Math.max(args.limitPerType ?? 10, 1), 25);
    if (!term) {
      return { documents: [], activities: [], tasks: [] };
    }

    const [documents, activities, tasks] = await Promise.all([
      ctx.db
        .query("documents")
        .withSearchIndex("search_content", (q) => q.search("content", term))
        .take(limit),
      ctx.db
        .query("activities")
        .withSearchIndex("search_description", (q) => q.search("description", term))
        .take(limit),
      ctx.db
        .query("tasks")
        .withSearchIndex("search_name", (q) => q.search("name", term))
        .take(limit),
    ]);

    return { documents, activities, tasks };
  },
});
