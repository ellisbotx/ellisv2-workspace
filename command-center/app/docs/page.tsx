import { DocViewerClient } from "@/components/DocViewerClient";
import { Suspense } from "react";

export default function Page() {
  return (
    <Suspense fallback={<div className="text-sm text-zinc-400">Loading…</div>}>
      <DocViewerClient />
    </Suspense>
  );
}
