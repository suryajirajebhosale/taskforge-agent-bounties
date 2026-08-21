"use client";

import { useMemo, useState, type ReactNode } from "react";
import { AgentCard } from "@/components/catalog/AgentCard";
import { SlaLearnLink } from "@/components/SlaSidecar";
import {
  CATALOG_AGENTS,
  SPECIALIZATIONS,
  compileCatalogQuery,
  searchCatalogAgents,
} from "@/lib/catalog";

export function CatalogBrowser() {
  const [query, setQuery] = useState("");
  const [specialty, setSpecialty] = useState<string | null>(null);
  const compiled = useMemo(() => compileCatalogQuery(query), [query]);
  const agents = useMemo(
    () => searchCatalogAgents(query, CATALOG_AGENTS, specialty),
    [query, specialty],
  );

  return (
    <>
      <div className="mt-10 flex flex-wrap gap-2">
        <Chip active={specialty === null} onClick={() => setSpecialty(null)}>
          All
        </Chip>
        {SPECIALIZATIONS.map((spec) => (
          <Chip
            key={spec.id}
            active={specialty === spec.id}
            onClick={() => setSpecialty(spec.id)}
          >
            {spec.title}
          </Chip>
        ))}
      </div>
      <label className="mt-6 block">
        <span className="text-xs font-medium text-muted">Search</span>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="bounce emails, hire ICP, cheap enrich…"
          className="mt-2 w-full rounded-xl border border-white/10 bg-panel-soft px-4 py-3 text-sm outline-none focus:border-lavender"
        />
      </label>
      <p className="mt-3 text-xs text-muted">
        Query compiler: {compiled.explanation}. Rank is eval, then rating, then price — not the
        listing blurb. SLA-eligible agents may be Hired;{" "}
        <SlaLearnLink label="learn why SLA is verified →" />
      </p>
      <div className="mt-8 grid grid-cols-1 gap-5 md:grid-cols-3">
        {agents.map((agent) => (
          <AgentCard key={agent.slug} agent={agent} />
        ))}
      </div>
      {agents.length === 0 && (
        <p className="mt-8 text-center text-sm text-muted">No listings match those filters.</p>
      )}
    </>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
        active
          ? "bg-lavender/20 text-brand-bright"
          : "border border-white/10 text-muted hover:border-lavender/40 hover:text-white"
      }`}
    >
      {children}
    </button>
  );
}
