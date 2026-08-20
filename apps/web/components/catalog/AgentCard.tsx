"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { BADGE_LABEL, canHire, specializationTitle, type CatalogAgent } from "@/lib/catalog";

export function AgentCard({ agent }: { agent: CatalogAgent }) {
  return (
    <motion.div whileHover={{ y: -6 }}>
      <Link
        href={`/catalog/${agent.slug}`}
        className="block h-full rounded-3xl border border-white/8 bg-panel-soft/80 p-6 transition-colors hover:border-lavender/35"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-brand text-sm font-bold">
            {agent.name.slice(0, 2)}
          </div>
          <span className="rounded-full bg-lavender/15 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-brand-bright">
            {BADGE_LABEL[agent.badge]}
          </span>
        </div>
        <h3 className="mt-4 text-xl font-semibold">{agent.name}</h3>
        <p className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-lavender/80">
          {specializationTitle(agent.templateId)}
        </p>
        <p className="mt-2 text-sm text-muted">{agent.tagline}</p>
        <div className="mt-5 flex flex-wrap gap-3 text-xs text-white/70">
          <span>★ {agent.rating.toFixed(1)}</span>
          <span>{Math.round(agent.evalPassRate * 100)}% eval</span>
          <span>{agent.pricePerRun}</span>
        </div>
        <p className="mt-4 text-xs text-muted">
          {canHire(agent) ? `Hire ${agent.hireMonthly}` : "Run only · Hire after certification"}
        </p>
      </Link>
    </motion.div>
  );
}
