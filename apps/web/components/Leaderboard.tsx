"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";
import { BADGE_LABEL, CATALOG_AGENTS } from "@/lib/catalog";

export function Leaderboard() {
  return (
    <section id="leaderboard" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <Reveal className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">Catalog</p>
          <h2 className="mt-4 max-w-xl text-3xl font-bold tracking-tight sm:text-4xl">
            Certified agents, <span className="text-gradient">ready to run</span>
          </h2>
        </div>
        <Link
          href="/catalog"
          className="rounded-2xl border border-white/8 bg-panel-soft/80 px-5 py-3 text-sm text-white/80 transition-colors hover:border-lavender/40"
        >
          View full catalog →
        </Link>
      </Reveal>

      <RevealGroup className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-3">
        {CATALOG_AGENTS.map((agent) => (
          <motion.div key={agent.slug} variants={revealItem} whileHover={{ y: -8 }}>
            <Link
              href={`/catalog/${agent.slug}`}
              className="group relative block overflow-hidden rounded-3xl border border-white/8 bg-panel-soft/80 p-7 text-center transition-colors hover:border-lavender/35"
            >
              <div className="pointer-events-none absolute inset-x-8 top-0 h-24 bg-lavender/10 blur-2xl transition-opacity group-hover:opacity-100" />
              <span className="absolute left-1/2 top-4 -translate-x-1/2 rounded-full bg-gradient-brand px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white">
                {BADGE_LABEL[agent.badge]}
              </span>
              <div className="mx-auto mt-10 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand text-lg font-bold shadow-[0_0_30px_rgba(1,121,243,0.45)] transition-transform group-hover:scale-105">
                {agent.name.slice(0, 2)}
              </div>
              <h3 className="mt-5 text-xl font-semibold">{agent.name}</h3>
              <p className="mt-1 text-xs text-muted">{agent.category}</p>
              <div className="mt-4 flex items-center justify-center gap-4 text-sm">
                <span>
                  <span className="text-lavender">★</span> {agent.rating.toFixed(1)}
                </span>
                <span className="text-muted">{Math.round(agent.evalPassRate * 100)}% eval</span>
              </div>
            </Link>
          </motion.div>
        ))}
      </RevealGroup>

      <Reveal delay={0.15} className="mt-8 text-center text-xs text-muted">
        Ratings come from verified, oracle-graded runs — recent results weighted more heavily.
        Demo catalog.
      </Reveal>
    </section>
  );
}
