"use client";

import { usePaginatedQuery, useMutation } from "convex/react";
import { api } from "@/convex/_generated/api";
import { useMemo, useState } from "react";
import { format } from "date-fns";

function Badge({ children, tone }: { children: React.ReactNode; tone?: "good" | "bad" | "mid" | "neutral" }) {
  const cls =
    tone === "good"
      ? "bg-emerald-500/15 text-emerald-200 ring-emerald-500/20"
      : tone === "bad"
        ? "bg-rose-500/15 text-rose-200 ring-rose-500/20"
        : tone === "mid"
          ? "bg-amber-500/15 text-amber-200 ring-amber-500/20"
          : "bg-zinc-500/15 text-zinc-200 ring-zinc-500/20";
  return <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs ring-1 ${cls}`}>{children}</span>;
}

export function ActivityFeed() {
  const [agent, setAgent] = useState<string>("");
  const [actionType, setActionType] = useState<string>("");
  const [outcome, setOutcome] = useState<string>("");

  const args = useMemo(() => {
    return {
      agent: agent || undefined,
      actionType: actionType || undefined,
      outcome: (outcome as "success" | "failed" | "partial" | "") || undefined,
    } as const;
  }, [agent, actionType, outcome]);

  const { results, status, loadMore, isLoading } = usePaginatedQuery(api.activities.list, args, { initialNumItems: 30 });

  const log = useMutation(api.activities.log);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Activity</h1>
          <p className="text-sm text-zinc-400">Newest first • Infinite scroll</p>
        </div>

        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <label className="text-xs text-zinc-400">
            Agent
            <input
              value={agent}
              onChange={(e) => setAgent(e.target.value)}
              placeholder="Ellis"
              className="mt-1 w-full rounded border border-white/10 bg-zinc-900 px-2 py-1 text-sm text-zinc-100"
            />
          </label>
          <label className="text-xs text-zinc-400">
            Action type
            <input
              value={actionType}
              onChange={(e) => setActionType(e.target.value)}
              placeholder="ASIN Check"
              className="mt-1 w-full rounded border border-white/10 bg-zinc-900 px-2 py-1 text-sm text-zinc-100"
            />
          </label>
          <label className="text-xs text-zinc-400">
            Outcome
            <select
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="mt-1 w-full rounded border border-white/10 bg-zinc-900 px-2 py-1 text-sm text-zinc-100"
            >
              <option value="">Any</option>
              <option value="success">Success</option>
              <option value="partial">Partial</option>
              <option value="failed">Failed</option>
            </select>
          </label>
        </div>
      </div>

      <div className="flex items-center justify-between rounded border border-white/10 bg-zinc-900/40 px-3 py-2">
        <div className="text-xs text-zinc-400">Tip: agents can log actions via the Convex mutation activities.log.</div>
        <button
          onClick={() =>
            log({
              agent: "Ellis",
              actionType: "Manual Log",
              description: "Test log from UI",
              outcome: "success",
              related: ["/"],
              metadata: { from: "ui" },
            })
          }
          className="rounded bg-white/10 px-2 py-1 text-xs text-zinc-100 hover:bg-white/15"
        >
          + Test log
        </button>
      </div>

      <div className="space-y-2">
        {results?.map((a) => (
          <div key={a._id} className="rounded border border-white/10 bg-zinc-900/40 p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="neutral">{a.agent}</Badge>
                <Badge tone="neutral">{a.actionType}</Badge>
                <Badge tone={a.outcome === "success" ? "good" : a.outcome === "failed" ? "bad" : "mid"}>{a.outcome}</Badge>
              </div>
              <div className="text-xs text-zinc-400">
                {format(new Date(a.timestampMs), "yyyy-MM-dd HH:mm:ss")} ({a.timezone})
              </div>
            </div>
            <div className="mt-2 whitespace-pre-wrap text-sm text-zinc-100">{a.description}</div>
            {a.related?.length ? (
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-300">
                {a.related.map((r, idx) => (
                  <span key={idx} className="rounded bg-white/5 px-2 py-0.5 ring-1 ring-white/10">
                    {r}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))}

        <div className="flex justify-center py-4">
          <button
            disabled={isLoading || status !== "CanLoadMore"}
            onClick={() => loadMore(30)}
            className="rounded bg-white/10 px-4 py-2 text-sm text-zinc-100 disabled:opacity-50"
          >
            {status === "CanLoadMore" ? (isLoading ? "Loading…" : "Load more") : "No more"}
          </button>
        </div>
      </div>
    </div>
  );
}
