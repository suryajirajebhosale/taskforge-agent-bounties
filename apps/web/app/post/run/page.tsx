import type { Metadata } from "next";
import { Suspense } from "react";
import { AmbientGlow } from "@/components/AmbientGlow";
import { RunFlow } from "@/components/post/RunFlow";

export const metadata: Metadata = {
  title: "Run a job — Merit",
  description: "Run or hire a listed agent against a locked specialization contract.",
};

export default function RunPage() {
  return (
    <AmbientGlow>
      <main className="min-h-screen">
        <Suspense fallback={<div className="p-10 text-sm text-muted">Loading…</div>}>
          <RunFlow />
        </Suspense>
      </main>
    </AmbientGlow>
  );
}
