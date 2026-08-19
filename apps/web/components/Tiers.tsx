"use client";

import { motion } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";

const TIERS = [
  {
    name: "Micro",
    range: "$1 – $25",
    highlight: false,
    features: ["Instant auto-verification", "Objective checks only", "Paid out in minutes", "No review queue"],
  },
  {
    name: "Standard",
    range: "$25 – $500",
    highlight: true,
    features: [
      "Objective + subjective grading",
      "LLM judge with confidence scoring",
      "Dispute & appeal supported",
      "Most bounty categories",
    ],
  },
  {
    name: "Enterprise",
    range: "$500+",
    highlight: false,
    features: ["Human-reviewed before payout", "Custom verification criteria", "Dedicated support", "Volume pricing"],
  },
];

export function Tiers() {
  return (
    <section id="pricing" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">Pricing</p>
        <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
          Priced by <span className="text-gradient">outcome</span>, not by the hour
        </h2>
        <p className="mt-4 text-muted">
          Higher-stakes bounties get more scrutiny before payout. You never pay platform fees on a failed submission.
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
                Most common
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
            <a
              href="/post"
              className={`mt-8 block rounded-full py-3 text-center text-sm font-semibold transition-transform hover:scale-[1.03] ${
                tier.highlight
                  ? "bg-gradient-brand text-white"
                  : "border border-white/15 text-white hover:border-lavender/40"
              }`}
            >
              Post a bounty →
            </a>
          </motion.div>
        ))}
      </RevealGroup>
    </section>
  );
}
