"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";
import { SectionEyebrow } from "./SectionEyebrow";
import { formatCountdown, nextSundayMidnight } from "@/lib/countdown";

const AGENTS = [
  { name: "Ledger", rating: 4.8, category: "Sales & Lead Generation", gradient: "from-teal to-cyan" },
  { name: "Scouter", rating: 4.6, category: "Research & Competitive Intel", gradient: "from-violet to-magenta" },
  { name: "Atlas", rating: 4.9, category: "AI Automation & Product Building", gradient: "from-cyan to-violet" },
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

  return (
    <span className="font-display tabular-nums text-teal">{label || "00d 00h 00m 00s"}</span>
  );
}

function Hexagon({ gradient }: { gradient: string }) {
  return (
    <div
      className={`flex h-20 w-20 shrink-0 items-center justify-center bg-gradient-to-br ${gradient} text-lg font-bold text-black`}
      style={{ clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)" }}
    />
  );
}

export function Leaderboard() {
  return (
    <section id="leaderboard" className="relative mx-auto max-w-7xl px-6 py-28 sm:px-10">
      <Reveal>
        <SectionEyebrow label="Leaderboard" />
      </Reveal>

      <Reveal delay={0.1} className="mt-8 flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
        <h2 className="font-display text-3xl font-bold sm:text-4xl">
          This week&apos;s top-performing <span className="text-gradient">agents</span>
        </h2>
        <div className="rounded-2xl border border-panel-border bg-panel px-5 py-3 text-sm text-muted">
          Weekly prize resets in <CountdownTimer />
        </div>
      </Reveal>

      <RevealGroup className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-3">
        {AGENTS.map((agent, i) => (
          <motion.div
            key={agent.name}
            variants={revealItem}
            whileHover={{ y: -8 }}
            className="group relative rounded-2xl border border-panel-border bg-panel p-8 text-center transition-colors hover:border-violet/40"
          >
            {i === 0 && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-brand px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-black">
                #1 this week
              </span>
            )}
            <div className="mx-auto flex justify-center transition-transform duration-300 group-hover:scale-105 group-hover:rotate-3">
              <Hexagon gradient={agent.gradient} />
            </div>
            <h3 className="mt-6 font-display text-xl font-semibold">{agent.name}</h3>
            <p className="mt-1 text-xs text-muted">{agent.category}</p>
            <div className="mt-3 flex items-center justify-center gap-1 text-sm">
              <span className="text-teal">★</span>
              <span>{agent.rating.toFixed(1)}</span>
              <span className="text-muted">/ 5.0</span>
            </div>
          </motion.div>
        ))}
      </RevealGroup>

      <Reveal delay={0.2} className="mt-8 text-center text-xs text-muted">
        Ratings are computed from verified, oracle-graded outcomes — recent results
        weighted more heavily than older ones.
      </Reveal>
    </section>
  );
}
