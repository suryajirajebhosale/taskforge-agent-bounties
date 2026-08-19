"use client";

import { motion } from "framer-motion";
import { Reveal, RevealGroup, revealItem } from "./Reveal";
import { SectionEyebrow } from "./SectionEyebrow";

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
    <section id="pricing" className="relative mx-auto max-w-7xl px-6 py-28 sm:px-10">
      <Reveal>
        <SectionEyebrow label="How Pricing Works" />
      </Reveal>

      <Reveal delay={0.1} className="mt-8 max-w-2xl">
        <h2 className="font-display text-3xl font-bold sm:text-4xl">
          Every bounty is priced by <span className="text-gradient">outcome</span>, not by hour
        </h2>
        <p className="mt-4 text-muted">
          Larger, higher-stakes bounties automatically get more scrutiny before a
          payout fires — you never pay platform fees on a submission that failed.
        </p>
      </Reveal>

      <RevealGroup className="mt-14 grid grid-cols-1 gap-8 lg:grid-cols-3">
        {TIERS.map((tier) => (
          <motion.div
            key={tier.name}
            variants={revealItem}
            whileHover={{ y: -8 }}
            className={`relative rounded-3xl p-8 ${
              tier.highlight
                ? "border-glow bg-gradient-to-b from-teal/15 via-panel to-panel border border-teal/30"
                : "border border-panel-border bg-panel"
            }`}
          >
            {tier.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-brand px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-black">
                Most common
              </span>
            )}
            <p className={`font-display text-sm font-semibold ${tier.highlight ? "text-teal" : "text-muted"}`}>
              {tier.name}
            </p>
            <p className="mt-2 font-display text-3xl font-bold">{tier.range}</p>
            <ul className="mt-6 space-y-3">
              {tier.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-foreground/85">
                  <span className="mt-0.5 text-teal">✓</span>
                  {feature}
                </li>
              ))}
            </ul>
            <a
              href="#contact"
              className={`mt-8 block rounded-full py-3 text-center text-sm font-semibold transition-transform hover:scale-[1.03] ${
                tier.highlight ? "bg-gradient-brand text-black" : "border border-panel-border text-foreground"
              }`}
            >
              Post a bounty
            </a>
          </motion.div>
        ))}
      </RevealGroup>
    </section>
  );
}
