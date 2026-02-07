"use client";

import { api } from "@/convex/_generated/api";
import { useQuery } from "convex/react";
import { format } from "date-fns";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

function highlight(text: string, term: string) {
  const t = term.trim();
  if (!t) return text;
  const idx = text.toLowerCase().indexOf(t.toLowerCase());
  if (idx === -1) return text.slice(0, 280);
  const start = Math.max(0, idx - 80);
  const end = Math.min(text.length, idx + t.length + 160);
  const prefix = start > 0 ? "…" : "";
  const suffix = end < text.length ? "…" : "";
  const snippet = text.slice(start, end);
  const before = snippet.slice(0, idx - start);
  const match = snippet.slice(idx - start, idx - start + t.length);
  const after = snippet.slice(idx - start + t.length);
  return (
    <>
      {prefix}
      {before}
      <mark className="rounded bg-amber-400/20 px-1 text-amber-200 ring-1 ring-amber-400/20">{match}</mark>
      {after}
      {suffix}
    </>
  );
}

export function SearchPanel() {
  const [value, setValue] = useState("");
  const [term, setTerm] = useState("");

  useEffect(() => {
    const id = setTimeout(() => setTerm(value), 200);
    return () => clearTimeout(id);
  }, [value]);

  const data = useQuery(api.search.global, { term, limitPerType: 10 });

  const counts = useMemo(() => {
    return {
      documents: data?.documents.length ?? 0,
      activities: data?.activities.length ?? 0,
      tasks: data?.tasks.length ?? 0,
    };
  }, [data]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Global Search</h1>
        <p className="text-sm text-zinc-400">Search memory, docs, activity history, scheduled tasks</p>
      </div>

      <div className="rounded border border-white/10 bg-zinc-900/40 p-3">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Search as you type…"
          className="w-full rounded border border-white/10 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
        />
        <div className="mt-2 text-xs text-zinc-400">
          Results: {counts.documents} docs • {counts.activities} activities • {counts.tasks} tasks
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <section className="rounded border border-white/10 bg-zinc-900/40 p-3">
          <div className="mb-2 text-sm font-medium">Documents</div>
          <div className="space-y-2">
            {data?.documents?.length ? (
              data.documents.map((d) => (
                <Link
                  href={`/docs?path=${encodeURIComponent(d.path)}`}
                  key={d._id}
                  className="block rounded bg-zinc-950/40 p-2 ring-1 ring-white/10 hover:bg-zinc-950/60"
                >
                  <div className="truncate text-xs text-zinc-300">{d.path}</div>
                  <div className="mt-1 text-xs text-zinc-100">{highlight(d.content, term)}</div>
                </Link>
              ))
            ) : (
              <div className="text-xs text-zinc-500">No document matches</div>
            )}
          </div>
        </section>

        <section className="rounded border border-white/10 bg-zinc-900/40 p-3">
          <div className="mb-2 text-sm font-medium">Activity</div>
          <div className="space-y-2">
            {data?.activities?.length ? (
              data.activities.map((a) => (
                <div key={a._id} className="rounded bg-zinc-950/40 p-2 ring-1 ring-white/10">
                  <div className="flex items-center justify-between gap-2">
                    <div className="truncate text-xs text-zinc-300">
                      {a.agent} • {a.actionType}
                    </div>
                    <div className="shrink-0 text-[11px] text-zinc-500">{format(new Date(a.timestampMs), "MMM d HH:mm")}</div>
                  </div>
                  <div className="mt-1 text-xs text-zinc-100">{highlight(a.description, term)}</div>
                </div>
              ))
            ) : (
              <div className="text-xs text-zinc-500">No activity matches</div>
            )}
          </div>
        </section>

        <section className="rounded border border-white/10 bg-zinc-900/40 p-3">
          <div className="mb-2 text-sm font-medium">Tasks</div>
          <div className="space-y-2">
            {data?.tasks?.length ? (
              data.tasks.map((t) => (
                <div key={t._id} className="rounded bg-zinc-950/40 p-2 ring-1 ring-white/10">
                  <div className="truncate text-xs text-zinc-100">{highlight(t.name, term)}</div>
                  <div className="mt-1 text-[11px] text-zinc-500">
                    {t.nextRunAtMs ? `Next: ${format(new Date(t.nextRunAtMs), "MMM d HH:mm")}` : "Next: —"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-zinc-500">No task matches</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
