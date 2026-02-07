import { ConvexHttpClient } from "convex/browser";
import { api } from "@/convex/_generated/api";

export type ActivityOutcome = "success" | "failed" | "partial";

export async function logActivity(input: {
  agent: string;
  actionType: string;
  description: string;
  outcome: ActivityOutcome;
  related?: string[];
  metadata?: unknown;
  timestampMs?: number;
  timezone?: string;
}) {
  const url = process.env.NEXT_PUBLIC_CONVEX_URL;
  if (!url) throw new Error("Missing NEXT_PUBLIC_CONVEX_URL");
  const client = new ConvexHttpClient(url);
  return await client.mutation(api.activities.log, {
    timestampMs: input.timestampMs,
    timezone: input.timezone ?? "America/Chicago",
    agent: input.agent,
    actionType: input.actionType,
    description: input.description,
    outcome: input.outcome,
    related: input.related,
    metadata: input.metadata,
  });
}
