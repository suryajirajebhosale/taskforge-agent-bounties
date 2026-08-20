import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { MarketingShell } from "@/components/MarketingShell";
import { BADGE_LABEL, CATALOG_AGENTS, canHire, getAgent, specializationTitle } from "@/lib/catalog";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return CATALOG_AGENTS.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const agent = getAgent(slug);
  return { title: agent ? `${agent.name} — Merit` : "Agent — Merit" };
}

export default async function AgentPage({ params }: Props) {
  const { slug } = await params;
  const agent = getAgent(slug);
  if (!agent) notFound();

  return (
    <MarketingShell>
      <section className="mx-auto max-w-3xl px-6 pb-24 sm:px-10">
        <Link href="/catalog" className="text-sm text-muted hover:text-lavender">
          ← Catalog
        </Link>
        <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">
              {specializationTitle(agent.templateId)} · {agent.category}
            </p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight">{agent.name}</h1>
            <p className="mt-3 text-muted">{agent.tagline}</p>
          </div>
          <span className="rounded-full bg-lavender/15 px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-brand-bright">
            {BADGE_LABEL[agent.badge]}
          </span>
        </div>

        <p className="mt-8 text-sm leading-relaxed text-white/80">{agent.description}</p>

        <dl className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="Rating" value={agent.rating.toFixed(1)} />
          <Stat label="Eval pass" value={`${Math.round(agent.evalPassRate * 100)}%`} />
          <Stat label="Per run" value={agent.pricePerRun} />
          <Stat label="Hire" value={agent.hireMonthly ?? "—"} />
        </dl>

        <div className="mt-10 grid gap-5 sm:grid-cols-2">
          <SchemaBlock title="Input" rows={agent.inputSchema} sample={agent.sampleInput} />
          <SchemaBlock title="Output" rows={agent.outputSchema} sample={agent.sampleOutput} />
        </div>

        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            href={`/post/run?agent=${agent.slug}`}
            className="rounded-full bg-gradient-brand px-6 py-3 text-sm font-semibold text-white"
          >
            Run this agent →
          </Link>
          {canHire(agent) ? (
            <Link
              href={`/post/run?agent=${agent.slug}&hire=1`}
              className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-white/90 hover:border-lavender/40"
            >
              Hire {agent.hireMonthly}
            </Link>
          ) : (
            <span className="rounded-full border border-white/10 px-6 py-3 text-sm text-muted">
              Hire unlocks at SLA-eligible
            </span>
          )}
        </div>
      </section>
    </MarketingShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-panel-soft/70 px-4 py-3">
      <dt className="text-[11px] text-muted">{label}</dt>
      <dd className="mt-1 text-lg font-semibold">{value}</dd>
    </div>
  );
}

function SchemaBlock({ title, rows, sample }: { title: string; rows: string[]; sample: string }) {
  return (
    <div className="rounded-3xl border border-white/8 bg-panel-soft/70 p-5">
      <p className="text-xs font-semibold tracking-wide text-lavender uppercase">{title}</p>
      <ul className="mt-3 space-y-1.5 text-sm text-white/80">
        {rows.map((row) => (
          <li key={row}>• {row}</li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-muted">Sample: {sample}</p>
    </div>
  );
}
