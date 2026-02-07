"use client";

import { api } from "@/convex/_generated/api";
import { useQuery } from "convex/react";
import { useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function DocViewerClient() {
  const sp = useSearchParams();
  const path = sp.get("path") ?? "";
  const doc = useQuery(api.documents.getByPath, path ? { path } : "skip");

  if (!path) {
    return <div className="text-sm text-zinc-400">Missing ?path=…</div>;
  }

  if (doc === undefined) {
    return <div className="text-sm text-zinc-400">Loading…</div>;
  }

  if (doc === null) {
    return <div className="text-sm text-zinc-400">Not indexed: {path}</div>;
  }

  return (
    <div className="space-y-3">
      <div>
        <h1 className="text-lg font-semibold">{doc.path}</h1>
        <div className="text-xs text-zinc-500">Type: {doc.docType}</div>
      </div>

      <article className="prose prose-invert max-w-none rounded border border-white/10 bg-zinc-900/40 p-4">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{doc.content}</ReactMarkdown>
      </article>
    </div>
  );
}
