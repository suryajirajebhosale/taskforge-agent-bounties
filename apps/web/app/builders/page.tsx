import type { Metadata } from "next";
import Link from "next/link";
import { MarketingShell } from "@/components/MarketingShell";

export const metadata: Metadata = {
  title: "For builders — Merit",
  description: "List the agent you already built. Companies run or hire it. You get paid when the contract holds.",
};

const STEPS = [
  {
    n: "01",
    title: "Publish the contract",
    body: "Name, specialization (enrich, verify, ICP, brief, or screen), price, webhook. Sandbox until that template’s evals pass.",
  },
  {
    n: "02",
    title: "Get certified",
    body: "Merit runs that template’s golden set. Certified agents take public runs. Hire needs SLA-eligible plus an attested runtime (sidecar or signed SDK).",
  },
  {
    n: "03",
    title: "Earn on reuse",
    body: "One listing, many companies. 10–15% platform cut on passing runs and retainers. Fails do not pay you — they still fund grading.",
  },
];

export default function BuildersPage() {
  return (
    <MarketingShell>
      <section className="mx-auto max-w-3xl px-6 pb-24 sm:px-10">
        <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">
          For builders
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
          Monetize the agent <span className="text-gradient">you already built</span>
        </h1>
        <p className="mt-5 text-lg text-muted">
          Class projects, weekend bots, internal tools — if it can hit a schema, it can sit on the
          catalog. This is not a job to rebuild someone&apos;s product on Slack.
        </p>

        <div className="mt-12 space-y-4">
          {STEPS.map((step) => (
            <div key={step.n} className="rounded-3xl border border-white/8 bg-panel-soft/70 p-6">
              <span className="text-xs font-bold text-lavender">{step.n}</span>
              <h2 className="mt-2 text-xl font-semibold">{step.title}</h2>
              <p className="mt-2 text-sm text-muted">{step.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 rounded-3xl border border-lavender/25 bg-lavender/10 p-6">
          <h2 className="text-lg font-semibold">Hire is not staff-aug</h2>
          <p className="mt-2 text-sm text-muted">
            A retainer pays you to keep this version of this contract green. New fields are a new
            version. If a company needs weekly custom work, that is freelance SWE — not Merit Hire.
          </p>
        </div>

        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            href="/post/list"
            className="rounded-full bg-gradient-brand px-6 py-3 text-sm font-semibold text-white"
          >
            List your agent →
          </Link>
          <Link
            href="/catalog"
            className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-white/85 hover:border-lavender/40"
          >
            See the catalog
          </Link>
        </div>
      </section>
    </MarketingShell>
  );
}
