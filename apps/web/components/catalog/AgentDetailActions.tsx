"use client";

import Link from "next/link";
import { BADGE_LABEL, canHire, type CatalogAgent } from "@/lib/catalog";
import { SlaLearnLink } from "@/components/SlaSidecar";

export function AgentDetailActions({ agent }: { agent: CatalogAgent }) {
  const hireable = canHire(agent);

  return (
    <div className="mt-10 space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className="rounded-full bg-lavender/15 px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-brand-bright">
          {BADGE_LABEL[agent.badge]}
        </span>
        {agent.badge === "sla" && <SlaLearnLink />}
        {agent.badge === "certified" && (
          <p className="text-xs text-muted">Hire unlocks after SLA-eligible + attested sidecar.</p>
        )}
        {agent.badge === "sandbox" && (
          <p className="text-xs text-muted">Sandbox: capped runs until golden-set cert.</p>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        <Link
          href={`/post/run?agent=${agent.slug}`}
          className="rounded-full bg-gradient-brand px-6 py-3 text-sm font-semibold text-white"
        >
          Run this agent →
        </Link>
        {hireable ? (
          <Link
            href={`/post/run?agent=${agent.slug}&hire=1`}
            className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-white/90 hover:border-lavender/40"
          >
            Hire {agent.hireMonthly}
          </Link>
        ) : (
          <span className="rounded-full border border-white/10 px-6 py-3 text-sm text-muted">
            Hire unlocks at SLA-eligible
          </span>
        )}
      </div>

      {hireable && (
        <p className="text-xs text-muted">
          Hire jobs require a sidecar (or signed SDK) so Merit can verify tools/models against the
          declared harness — not just the output row.{" "}
          <SlaLearnLink label="How the sidecar works →" />
        </p>
      )}
    </div>
  );
}
