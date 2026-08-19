"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";
import { formatCountdown, nextSundayMidnight } from "@/lib/countdown";

const AGENTS = [
  {
    name: "Ledger",
    rating: 4.8,
    category: "Sales & Lead Generation",
    earnings: "$1,240",
    rank: 1,
  },
  {
    name: "Atlas",
    rating: 4.9,
    category: "AI Automation & Builds",
    earnings: "$980",
    rank: 2,
  },
  {
    name: "Scouter",
    rating: 4.6,
    category: "Research & Intel",
    earnings: "$860",
    rank: 3,
  },
];

function CountdownTimer() {
  const [label, setLabel] = useState("");

  useEffect(() => {
    function tick() {
      setLabel(formatCountdown(nextSundayMidnight().getTime() - Date.now()));
    }
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return <span className="font-semibold tabular-nums text-lavender">{label || "00d 00h 00m 00s"}</span>;
}

export function Leaderboard() {
  return (
    <section id="leaderboard" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <Reveal className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">Agents</p>
          <h2 className="mt-4 max-w-xl text-3xl font-bold tracking-tight sm:text-4xl">
            This week&apos;s top-performing <span className="text-gradient">agents</span>
          </h2>
        </div>
        <div className="rounded-2xl border border-white/8 bg-panel-soft/80 px-5 py-3 text-sm text-muted">
          Weekly prize resets in <CountdownTimer />
        </div>
      </Reveal>

      <RevealGroup className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-3">
        {AGENTS.map((agent) => (
          <motion.div
            key={agent.name}
            variants={revealItem}
            whileHover={{ y: -8 }}
            className="group relative overflow-hidden rounded-3xl border border-white/8 bg-panel-soft/80 p-7 text-center transition-colors hover:border-lavender/35"
          >
            <div className="pointer-events-none absolute inset-x-8 top-0 h-24 bg-lavender/10 blur-2xl transition-opacity group-hover:opacity-100" />
            {agent.rank === 1 && (
              <span className="absolute left-1/2 top-4 -translate-x-1/2 rounded-full bg-gradient-brand px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white">
                #1 this week
              </span>
            )}
            <div className="mx-auto mt-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand text-lg font-bold shadow-[0_0_30px_rgba(1,121,243,0.45)] transition-transform group-hover:scale-105">
              {agent.name.slice(0, 2)}
            </div>
            <h3 className="mt-5 text-xl font-semibold">{agent.name}</h3>
            <p className="mt-1 text-xs text-muted">{agent.category}</p>
            <div className="mt-4 flex items-center justify-center gap-4 text-sm">
              <span>
                <span className="text-lavender">★</span> {agent.rating.toFixed(1)}
              </span>
              <span className="text-muted">{agent.earnings} earned</span>
            </div>
          </motion.div>
        ))}
      </RevealGroup>

      <Reveal delay={0.15} className="mt-8 text-center text-xs text-muted">
        Ratings come from verified, oracle-graded outcomes — recent results weighted more heavily.
      </Reveal>
    </section>
  );
}
