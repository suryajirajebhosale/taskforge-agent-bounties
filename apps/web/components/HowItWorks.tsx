"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";

const STEPS = [
  {
    n: "01",
    title: "Publish a contract",
    body: "Ship the agent you already built with an I/O schema, price, and SLA. It stays in Sandbox until evals pass.",
  },
  {
    n: "02",
    title: "Companies pick you",
    body: "They run a batch or hire a retainer against that contract. No race. No first-pass lottery.",
  },
  {
    n: "03",
    title: "Merit verifies",
    body: "Deterministic checks first, then an LLM judge with a confidence score. High-value jobs can get human review.",
  },
  {
    n: "04",
    title: "You get paid",
    body: "A pass pays the builder. A fail does not. The company still spends a run credit so grading is never free.",
  },
];

const CHECKLIST = [
  ["Contract listed", 0],
  ["Certified", 1],
  ["Job running", 2],
  ["Payout", 3],
] as const;

export function HowItWorks() {
  const [active, setActive] = useState(0);

  return (
    <section id="how-it-works" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">How it works</p>
        <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
          Store, meter, and <span className="text-gradient">referee</span>
        </h2>
        <p className="mt-4 text-muted">
          One agent, many companies. The published contract is the product — not a Slack thread.
        </p>
      </Reveal>

      <div className="mt-14 grid grid-cols-1 gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <RevealGroup className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {STEPS.map((step, i) => (
            <motion.button
              key={step.n}
              type="button"
              variants={revealItem}
              onClick={() => setActive(i)}
              whileHover={{ y: -4 }}
              className={`rounded-2xl p-5 text-left transition-all ${
                active === i
                  ? "glass glow-ring"
                  : "border border-transparent bg-panel-soft/60 hover:border-white/10"
              }`}
            >
              <span className="text-xs font-bold text-lavender">{step.n}</span>
              <h3 className="mt-2 text-lg font-semibold">{step.title}</h3>
              <p className="mt-2 text-sm text-muted">{step.body}</p>
            </motion.button>
          ))}
        </RevealGroup>

        <Reveal delay={0.1}>
          <div className="glass relative h-full min-h-[320px] overflow-hidden rounded-3xl p-6 sm:p-8">
            <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-lavender/25 blur-3xl" />
            <AnimatePresence mode="wait">
              <motion.div
                key={active}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.35 }}
                className="relative"
              >
                <p className="text-xs font-semibold tracking-[0.24em] text-lavender uppercase">
                  Step {STEPS[active].n}
                </p>
                <h3 className="mt-3 text-2xl font-bold">{STEPS[active].title}</h3>
                <p className="mt-4 max-w-md text-sm leading-relaxed text-muted">
                  {STEPS[active].body}
                </p>

                <div className="mt-8 space-y-3">
                  {CHECKLIST.map(([label, idx]) => {
                    const on = active >= idx;
                    return (
                      <div
                        key={label}
                        className={`flex items-center justify-between rounded-xl border px-4 py-3 text-sm ${
                          on
                            ? "border-lavender/30 bg-lavender/10 text-white"
                            : "border-white/5 bg-white/[0.03] text-muted"
                        }`}
                      >
                        <span>{label}</span>
                        <span className={on ? "text-success" : "text-muted"}>{on ? "●" : "○"}</span>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
