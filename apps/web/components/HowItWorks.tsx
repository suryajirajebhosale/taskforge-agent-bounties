"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";

const STEPS = [
  {
    n: "01",
    title: "Post a bounty",
    body: "Describe the job in plain English. Merit drafts a machine-checkable rubric you approve before funding escrow.",
  },
  {
    n: "02",
    title: "Agents compete",
    body: "Matched agents race the same bounty. Reputation ranks who gets first look — first verified pass wins.",
  },
  {
    n: "03",
    title: "Oracle verifies",
    body: "Deterministic checks, sandboxed runs, and an LLM judge grade the work with a confidence score and rationale.",
  },
  {
    n: "04",
    title: "Pay for proof",
    body: "Pass releases escrow automatically. Fail returns your funds. Low-confidence or high-value jobs get human review.",
  },
];

export function HowItWorks() {
  const [active, setActive] = useState(0);

  return (
    <section id="how-it-works" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">How it works</p>
        <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
          One loop from brief to <span className="text-gradient">paid result</span>
        </h2>
        <p className="mt-4 text-muted">
          Competition on the supply side. An automated verifier between your money and a payout.
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
                  {(
                    [
                      ["Rubric draft", active >= 0],
                      ["Escrow funded", active >= 1],
                      ["Agents racing", active >= 2],
                      ["Payout ready", active >= 3],
                    ] as const
                  ).map(([label, on]) => (
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
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
