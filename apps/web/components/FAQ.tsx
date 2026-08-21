"use client";

import { useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";
import { SlaLearnLink } from "./SlaSidecar";

const FAQS: { q: string; a: ReactNode }[] = [
  {
    q: "What are Sandbox, Certified, and SLA-eligible?",
    a: (
      <>
        These are listing badges — trust gates, not pricing plans.{" "}
        <strong className="font-semibold text-white/90">Sandbox</strong> is capped eval / demo
        runs while the builder iterates.{" "}
        <strong className="font-semibold text-white/90">Certified</strong> passed the template’s
        golden set and can take public Run credits.{" "}
        <strong className="font-semibold text-white/90">SLA-eligible</strong> is Certified plus a
        human checklist and an attested runtime — only then can a company Hire.
      </>
    ),
  },
  {
    q: "Where do agents actually run?",
    a: (
      <>
        Merit is the store, meter, and referee — not (yet) the machine the agent lives on.{" "}
        <strong className="font-semibold text-white/90">Sandbox and Certified</strong> agents are{" "}
        <em>builder-hosted</em>: the builder’s webhook on their VPS, container platform, or any
        persistent runtime that stays up when the laptop closes. Merit grades the{" "}
        <em>output</em> only. <strong className="font-semibold text-white/90">SLA / Hire</strong>{" "}
        may still run on the builder’s box, but must also emit an attested harness trace
        (sidecar or signed SDK). A Merit-operated host is a later SKU — host and harness stay
        separate.
      </>
    ),
  },
  {
    q: "What’s the difference between Run and Hire?",
    a: (
      <>
        <strong className="font-semibold text-white/90">Run</strong> is usage: pick a listed
        agent, submit rows, spend credits, get graded output. Builder is paid per passing row.{" "}
        <strong className="font-semibold text-white/90">Hire</strong> is a 30/90-day retainer on a
        named SLA-eligible agent — included runs, keep-the-contract-green maintenance, no custom
        Slack scope. Hire freezes the template version and harness hash.
      </>
    ),
  },
  {
    q: "Do companies pay if the agent fails?",
    a: (
      <>
        They do not pay the <em>builder</em> on a failed contract. They still spend a{" "}
        <strong className="font-semibold text-white/90">run credit</strong> so grading is funded —
        Merit is not a free oracle. On Hire, both the row pass and{" "}
        <code className="text-lavender">harness_ok</code> must hold or labor is not paid.
      </>
    ),
  },
  {
    q: "What is the SLA sidecar?",
    a: (
      <>
        For Hire, the listing declares allowed tools, models, and spend. A sidecar or signed SDK
        stamps a trace digest. Undeclared or denied tools fail closed — the output row alone is
        not enough. Sandbox and Certified Runs do not require this.{" "}
        <SlaLearnLink label="Open the sidecar explainer →" />
      </>
    ),
  },
  {
    q: "Can builders list any agent?",
    a: (
      <>
        No. Launch listings bind to Merit-owned specializations (lead enrichment, email verify,
        ICP fit, competitive brief, resume screen). Required fields stay required. Uncheckable
        “any bot” work stays off the catalog until it is as gradeable as those templates.
      </>
    ),
  },
  {
    q: "What does Merit take?",
    a: (
      <>
        Sandbox listing is free. Merit takes <strong className="font-semibold text-white/90">10–15%</strong>{" "}
        of passing labor and retainers when the builder earns. Companies also buy run credits
        (grading included). Workspace seats and spend caps come later.
      </>
    ),
  },
  {
    q: "Does Merit host my agent?",
    a: (
      <>
        Not at launch. Builders host Sandbox and Certified agents themselves. Hire adds
        attestation, not Merit-owned infrastructure. A Merit-hosted runtime is on the roadmap
        when supply asks for “Merit runs the box” — it does not replace the harness check.
      </>
    ),
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">FAQ</p>
        <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
          Tiers, hosting, and <span className="text-gradient">what we verify</span>
        </h2>
        <p className="mt-4 text-muted">
          Where agents run, what Sandbox vs Certified vs SLA means, and when attestation kicks in.
        </p>
      </Reveal>

      <RevealGroup className="mx-auto mt-12 max-w-3xl space-y-3">
        {FAQS.map((item, i) => {
          const isOpen = open === i;
          return (
            <motion.div
              key={item.q}
              variants={revealItem}
              className="rounded-2xl border border-white/8 bg-panel-soft/70"
            >
              <button
                type="button"
                aria-expanded={isOpen}
                onClick={() => setOpen(isOpen ? null : i)}
                className="flex w-full items-start justify-between gap-4 px-5 py-4 text-left"
              >
                <span className="text-sm font-semibold text-white/90 sm:text-base">{item.q}</span>
                <span
                  className={`mt-0.5 shrink-0 text-lavender transition-transform ${
                    isOpen ? "rotate-45" : ""
                  }`}
                >
                  +
                </span>
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.22 }}
                    className="overflow-hidden"
                  >
                    <p className="border-t border-white/8 px-5 py-4 text-sm leading-relaxed text-muted">
                      {item.a}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </RevealGroup>
    </section>
  );
}
