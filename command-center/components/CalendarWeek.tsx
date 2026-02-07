"use client";

import { api } from "@/convex/_generated/api";
import { useQuery } from "convex/react";
import { addDays, format, startOfWeek } from "date-fns";
import { useMemo, useState } from "react";

function tone(status: string) {
  if (status === "completed") return "bg-emerald-500/15 text-emerald-200 ring-emerald-500/20";
  if (status === "failed") return "bg-rose-500/15 text-rose-200 ring-rose-500/20";
  if (status === "running") return "bg-sky-500/15 text-sky-200 ring-sky-500/20";
  return "bg-zinc-500/15 text-zinc-200 ring-zinc-500/20";
}

export function CalendarWeek() {
  const [anchor, setAnchor] = useState(() => new Date());

  const weekStart = useMemo(() => startOfWeek(anchor, { weekStartsOn: 1 }), [anchor]); // Monday
  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart]);
  const weekEnd = useMemo(() => addDays(weekStart, 7), [weekStart]);

  const tasks = useQuery(api.tasks.listWeek, {
    weekStartMs: weekStart.getTime(),
    weekEndMs: weekEnd.getTime(),
  });

  const byDay = useMemo(() => {
    const map: Record<string, typeof tasks> = {};
    (tasks ?? []).forEach((t) => {
      const d = new Date(t.nextRunAtMs ?? 0);
      const key = format(d, "yyyy-MM-dd");
      map[key] = map[key] ?? [];
      map[key]!.push(t);
    });
    Object.values(map).forEach((arr) => arr!.sort((a, b) => (a.nextRunAtMs ?? 0) - (b.nextRunAtMs ?? 0)));
    return map;
  }, [tasks]);

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold">Calendar</h1>
          <p className="text-sm text-zinc-400">Weekly view • scheduled tasks + next/last run</p>
        </div>
        <div className="flex gap-2">
          <button className="rounded bg-white/10 px-3 py-1 text-sm hover:bg-white/15" onClick={() => setAnchor(addDays(anchor, -7))}>
            ← Prev
          </button>
          <button className="rounded bg-white/10 px-3 py-1 text-sm hover:bg-white/15" onClick={() => setAnchor(new Date())}>
            Today
          </button>
          <button className="rounded bg-white/10 px-3 py-1 text-sm hover:bg-white/15" onClick={() => setAnchor(addDays(anchor, 7))}>
            Next →
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-7">
        {days.map((d) => {
          const key = format(d, "yyyy-MM-dd");
          const items = byDay[key] ?? [];
          return (
            <div key={key} className="rounded border border-white/10 bg-zinc-900/40 p-3">
              <div className="flex items-baseline justify-between">
                <div className="text-sm font-medium">{format(d, "EEE")}</div>
                <div className="text-xs text-zinc-400">{format(d, "MMM d")}</div>
              </div>
              <div className="mt-2 space-y-2">
                {items.length === 0 ? <div className="text-xs text-zinc-500">No tasks</div> : null}
                {items.map((t) => (
                  <div key={t._id} className="rounded bg-zinc-950/40 p-2 ring-1 ring-white/10">
                    <div className="flex items-center justify-between gap-2">
                      <div className="truncate text-sm text-zinc-100" title={t.name}>
                        {t.name}
                      </div>
                      <span className={`shrink-0 rounded px-2 py-0.5 text-[11px] ring-1 ${tone(t.status)}`}>{t.status}</span>
                    </div>
                    <div className="mt-1 text-xs text-zinc-400">
                      {t.nextRunAtMs ? `Next: ${format(new Date(t.nextRunAtMs), "HH:mm")}` : "Next: —"}
                    </div>
                    <div className="text-xs text-zinc-500">
                      {t.lastRunAtMs
                        ? `Last: ${format(new Date(t.lastRunAtMs), "MMM d HH:mm")} (${t.lastOutcome ?? "—"})`
                        : "Last: —"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded border border-white/10 bg-zinc-900/40 p-3 text-xs text-zinc-400">
        Data sources: parsed SCHEDULED_TASKS.md + (optional) OpenClaw cron import.
      </div>
    </div>
  );
}
