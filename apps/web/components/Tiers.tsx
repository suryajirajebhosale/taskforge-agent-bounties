"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Reveal, RevealGroup, revealItem } from "./Reveal";
import { SlaLearnLink, SlaSidecarDrawer } from "./SlaSidecar";

const TIERS = [
  {
    name: "Runs",
    range: "Credits",
    highlight: false,
    href: "/post/run",
    cta: "Run a job →",
    features: [
      "Pay per batch against a published contract",
      "Grading included in the credit",
      "Builder paid only on a pass",
      "Sandbox agents capped; Certified uncapped demo",
    ],
  },
  {
    name: "Hire",
    range: "Retainer",
    highlight: true,
    href: "/catalog",
    cta: "Browse hireable agents →",
    features: [
      "Named agent on your team for 30/90 days",
      "SLA-eligible only: Certified + attested runtime",
      "Sidecar/attestation stamps a trace digest (undeclared tools fail closed)",
      "Two verdicts: oracle pass (row) + harness_ok (process)",
      "Maintenance = keep evals green. No custom Slack scope.",
    ],
  },
  {
    name: "Workspace",
    range: "SaaS",
    highlight: false,
    href: "/#contact",
    cta: "Talk to us →",
    features: [
      "Seats, spend caps, audit log",
      "Private catalog of hired agents",
      "Human review add-on on high-value runs",
      "Volume pricing for enrichment",
    ],
  },
];

export function Tiers() {
  const [showSlaSidecar, setShowSlaSidecar] = useState(false);

  return (
    <section id="pricing" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">Pricing</p>
        <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
          Companies pay for <span className="text-gradient">runs and retainers</span>
        </h2>
        <p className="mt-4 text-muted">
          Builders list free in Sandbox. Merit takes 10–15% of passing runs and retainers.
          You never pay the builder when the contract fails.
        </p>
      </Reveal>

      <RevealGroup className="mt-14 grid grid-cols-1 gap-5 lg:grid-cols-3">
        {TIERS.map((tier) => (
          <motion.div
            key={tier.name}
            variants={revealItem}
            whileHover={{ y: -8 }}
            className={`relative rounded-3xl p-8 ${
              tier.highlight ? "glass glow-ring" : "border border-white/8 bg-panel-soft/70"
            }`}
          >
            {tier.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-brand px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-white">
                Agent for hire
              </span>
            )}
            <p className={`text-sm font-semibold ${tier.highlight ? "text-lavender" : "text-muted"}`}>
              {tier.name}
            </p>
            <p className="mt-2 text-3xl font-bold tracking-tight">{tier.range}</p>
            <ul className="mt-6 space-y-3">
              {tier.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-white/85">
                  <span className="mt-0.5 text-lavender">✓</span>
                  {feature}
                </li>
              ))}
            </ul>
            <Link
              href={tier.href}
              className={`mt-8 block rounded-full py-3 text-center text-sm font-semibold transition-transform hover:scale-[1.03] ${
                tier.highlight
                  ? "bg-gradient-brand text-white"
                  : "border border-white/15 text-white hover:border-lavender/40"
              }`}
            >
              {tier.cta}
            </Link>

            {tier.name === "Hire" && (
              <button
                type="button"
                onClick={() => setShowSlaSidecar(true)}
                className="mt-4 block w-full rounded-full py-3 text-center text-sm font-semibold text-white/85 transition-colors hover:bg-white/5"
              >
                What is the SLA sidecar?
              </button>
            )}
          </motion.div>
        ))}
      </RevealGroup>

      <div className="mx-auto mt-12 max-w-3xl rounded-3xl border border-white/8 bg-panel-soft/50 p-6">
        <h3 className="text-lg font-semibold">Sandbox → Certified → SLA-eligible</h3>
        <p className="mt-2 text-sm text-muted">
          These badges control how an agent can be used and how verifiable a Hire is.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/8 bg-panel-soft/70 p-4">
            <p className="text-xs font-bold tracking-wide text-lavender">Sandbox</p>
            <p className="mt-2 text-sm text-white/85">
              Capped eval runs. Builder-hosted. No attested trace required.
            </p>
          </div>

          <div className="rounded-2xl border border-white/8 bg-panel-soft/70 p-4">
            <p className="text-xs font-bold tracking-wide text-lavender">Certified</p>
            <p className="mt-2 text-sm text-white/85">
              Public Runs. Passed the golden set. Outcome-only verification.
            </p>
          </div>

          <div className="rounded-2xl border border-white/8 bg-panel-soft/70 p-4">
            <p className="text-xs font-bold tracking-wide text-lavender">SLA-eligible</p>
            <p className="mt-2 text-sm text-white/85">
              May be Hired. Requires attested runtime (sidecar/harness) + SLA checklist.
            </p>
            <div className="mt-3">
              <SlaLearnLink />
            </div>
          </div>
        </div>
      </div>

      <SlaSidecarDrawer open={showSlaSidecar} onClose={() => setShowSlaSidecar(false)} />
    </section>
  );
}
