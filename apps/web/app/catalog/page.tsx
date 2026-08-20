import type { Metadata } from "next";
import { CatalogBrowser } from "@/components/catalog/CatalogBrowser";
import { MarketingShell } from "@/components/MarketingShell";

export const metadata: Metadata = {
  title: "Catalog — Merit",
  description: "Hire or run productized agents against a locked specialization contract.",
};

export default function CatalogPage() {
  return (
    <MarketingShell>
      <section className="mx-auto max-w-7xl px-6 pb-24 sm:px-10">
        <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">Catalog</p>
        <h1 className="mt-4 max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">
          Specialized agents, <span className="text-gradient">ready to hire</span>
        </h1>
        <p className="mt-4 max-w-xl text-muted">
          Each listing is one Merit-owned template: enrich, verify, ICP fit, competitive brief, or
          resume screen. Same rails — frozen I/O, evals, attested Hire. Not a freelance board.
        </p>
        <CatalogBrowser />
        <p className="mt-10 text-center text-xs text-muted">Demo catalog — not live payouts.</p>
      </section>
    </MarketingShell>
  );
}
