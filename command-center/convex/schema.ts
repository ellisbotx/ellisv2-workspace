import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  activities: defineTable({
    timestampMs: v.number(),
    timezone: v.string(), // e.g. "America/Chicago"
    agent: v.string(), // "Ellis" | "Codex" | ...
    actionType: v.string(),
    description: v.string(),
    outcome: v.union(v.literal("success"), v.literal("failed"), v.literal("partial")),
    related: v.optional(v.array(v.string())), // files/links
    metadata: v.optional(v.any()),
  })
    .index("by_timestamp", ["timestampMs"])
    .searchIndex("search_description", {
      searchField: "description",
      filterFields: ["agent", "actionType", "outcome"],
    }),

  tasks: defineTable({
    name: v.string(),
    source: v.union(v.literal("SCHEDULED_TASKS.md"), v.literal("openclaw"), v.literal("manual")),
    cron: v.optional(v.string()), // cron string in CST
    scheduleText: v.optional(v.string()),
    status: v.union(
      v.literal("upcoming"),
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed")
    ),
    lastRunAtMs: v.optional(v.number()),
    lastOutcome: v.optional(v.union(v.literal("success"), v.literal("failed"), v.literal("partial"))),
    nextRunAtMs: v.optional(v.number()),
    tags: v.optional(v.array(v.string())),
    metadata: v.optional(v.any()),
  })
    .index("by_next_run", ["nextRunAtMs"])
    .searchIndex("search_name", {
      searchField: "name",
      filterFields: ["status", "source"],
    }),

  documents: defineTable({
    path: v.string(),
    docType: v.union(
      v.literal("memory"),
      v.literal("document"),
      v.literal("scheduled_tasks")
    ),
    content: v.string(),
    updatedAtMs: v.number(),
  })
    .index("by_path", ["path"])
    .searchIndex("search_content", {
      searchField: "content",
      filterFields: ["docType", "path"],
    }),
});
