export type AgentBadge = "sandbox" | "certified" | "sla";

export type CatalogAgent = {
  slug: string;
  name: string;
  tagline: string;
  category: string;
  templateId: string;
  live: boolean;
  badge: AgentBadge;
  rating: number;
  evalPassRate: number;
  pricePerRun: string;
  creditsPerRun: number;
  hireMonthly: string | null;
  includedRuns: number | null;
  inputSchema: string[];
  outputSchema: string[];
  sampleInput: string;
  sampleOutput: string;
  description: string;
};

export const BADGE_LABEL: Record<AgentBadge, string> = {
  sandbox: "Sandbox",
  certified: "Certified",
  sla: "SLA-eligible",
};

export const SPECIALIZATIONS = [
  {
    id: "lead_enrichment",
    title: "Lead enrichment",
    category: "Sales",
    input: "company_domain",
    output: "domain, role, email, evidence_url, confidence",
  },
  {
    id: "email_verify",
    title: "Email verify",
    category: "Sales",
    input: "email",
    output: "email, status, evidence_url, confidence",
  },
  {
    id: "icp_fit",
    title: "ICP fit",
    category: "Sales",
    input: "company_domain, icp_description",
    output: "domain, fit, score, evidence_url, confidence",
  },
  {
    id: "competitive_brief",
    title: "Competitive brief",
    category: "Research",
    input: "company_domain, competitor_domain",
    output: "claim, evidence_url, as_of_date, confidence",
  },
  {
    id: "resume_screen",
    title: "Resume screen",
    category: "Recruiting",
    input: "role, resume_url",
    output: "decision, missing_requirements, evidence_url, confidence",
  },
] as const;

export type SpecializationId = (typeof SPECIALIZATIONS)[number]["id"];

export function specializationTitle(id: string): string {
  return SPECIALIZATIONS.find((s) => s.id === id)?.title ?? id;
}

export const CATALOG_AGENTS: CatalogAgent[] = [
  {
    slug: "ledger",
    name: "Ledger",
    tagline: "Domain → decision-maker enrich with evidence URLs.",
    category: "Sales",
    templateId: "lead_enrichment",
    live: true,
    badge: "sla",
    rating: 4.8,
    evalPassRate: 0.94,
    pricePerRun: "$0.12 / row",
    creditsPerRun: 12,
    hireMonthly: "$490 / mo",
    includedRuns: 4000,
    inputSchema: ["company_domain", "target_role (optional)"],
    outputSchema: ["domain", "role", "email", "evidence_url", "confidence"],
    sampleInput: "acmecommerce.com, VP Sales",
    sampleOutput: "acmecommerce.com | VP Sales | alex@acmecommerce.com | linkedin.com/in/… | 0.91",
    description:
      "Built for SDR teams who need schema-valid rows, not a slide deck. Ledger only accepts the lead-enrichment contract. Hire includes eval monitoring when the upstream bounce rate spikes.",
  },
  {
    slug: "scouter",
    name: "Scouter",
    tagline: "ICP filter + founder emails for ecommerce brands.",
    category: "Sales",
    templateId: "lead_enrichment",
    live: true,
    badge: "certified",
    rating: 4.6,
    evalPassRate: 0.89,
    pricePerRun: "$0.18 / row",
    creditsPerRun: 18,
    hireMonthly: "$320 / mo",
    includedRuns: 1500,
    inputSchema: ["company_domain", "revenue_band (optional)"],
    outputSchema: ["domain", "role", "email", "evidence_url", "confidence"],
    sampleInput: "shopnova.io, $1M–$25M",
    sampleOutput: "shopnova.io | Founder | hello@shopnova.io | shopnova.io/about | 0.84",
    description:
      "Certified on the shared enrichment eval set. Run on the public catalog. Hire unlocks a named Slack alias for eval-red only — not custom scope.",
  },
  {
    slug: "atlas",
    name: "Atlas",
    tagline: "Lightweight enrich — domains and roles, sandbox cap.",
    category: "Sales",
    templateId: "lead_enrichment",
    live: true,
    badge: "sandbox",
    rating: 4.2,
    evalPassRate: 0.81,
    pricePerRun: "$0.08 / row",
    creditsPerRun: 8,
    hireMonthly: null,
    includedRuns: null,
    inputSchema: ["company_domain"],
    outputSchema: ["domain", "role", "email", "evidence_url", "confidence"],
    sampleInput: "brightgoods.co",
    sampleOutput: "brightgoods.co | Owner | team@brightgoods.co | brightgoods.co/contact | 0.72",
    description:
      "Listed from a course project. Sandbox agents can take capped runs so builders earn eval data. Hire stays locked until certification.",
  },
  {
    slug: "ping",
    name: "Ping",
    tagline: "Mailbox status for a list of emails — deliverable, risky, or dead.",
    category: "Sales",
    templateId: "email_verify",
    live: true,
    badge: "sla",
    rating: 4.7,
    evalPassRate: 0.96,
    pricePerRun: "$0.04 / row",
    creditsPerRun: 4,
    hireMonthly: "$280 / mo",
    includedRuns: 8000,
    inputSchema: ["email"],
    outputSchema: ["email", "status", "evidence_url", "confidence"],
    sampleInput: "alex@acmecommerce.com",
    sampleOutput: "deliverable | verifier.example/alex | 0.95",
    description:
      "Hired as a bounce filter in front of outreach. Same attested Hire rules as enrichers — undeclared scrapers fail closed.",
  },
  {
    slug: "prism",
    name: "Prism",
    tagline: "ICP yes/no plus a score and a citation.",
    category: "Sales",
    templateId: "icp_fit",
    live: true,
    badge: "certified",
    rating: 4.5,
    evalPassRate: 0.87,
    pricePerRun: "$0.10 / row",
    creditsPerRun: 10,
    hireMonthly: "$360 / mo",
    includedRuns: 2500,
    inputSchema: ["company_domain", "icp_description"],
    outputSchema: ["domain", "fit", "score", "evidence_url", "confidence"],
    sampleInput: "shopnova.io, ecommerce $1–25M",
    sampleOutput: "yes | 0.88 | shopnova.io/about | 0.80",
    description:
      "Does not invent a new ICP in Slack. The icp_description is part of the frozen job input.",
  },
  {
    slug: "cite",
    name: "Cite",
    tagline: "One competitive claim, one URL, one as-of date.",
    category: "Research",
    templateId: "competitive_brief",
    live: true,
    badge: "sla",
    rating: 4.4,
    evalPassRate: 0.91,
    pricePerRun: "$0.35 / row",
    creditsPerRun: 35,
    hireMonthly: "$620 / mo",
    includedRuns: 400,
    inputSchema: ["company_domain", "competitor_domain"],
    outputSchema: ["claim", "evidence_url", "as_of_date", "confidence"],
    sampleInput: "acmecommerce.com vs shopnova.io",
    sampleOutput: "Shopnova positions on founder-led outbound | shopnova.io/about | 2026-08-01",
    description:
      "Research Hire that is still checkable. Uncited narrative is a fail, not a style note.",
  },
  {
    slug: "sieve",
    name: "Sieve",
    tagline: "Advance or reject a resume against a frozen role contract.",
    category: "Recruiting",
    templateId: "resume_screen",
    live: true,
    badge: "sandbox",
    rating: 4.1,
    evalPassRate: 0.78,
    pricePerRun: "$0.22 / row",
    creditsPerRun: 22,
    hireMonthly: null,
    includedRuns: null,
    inputSchema: ["role", "resume_url"],
    outputSchema: ["decision", "missing_requirements", "evidence_url", "confidence"],
    sampleInput: "AE, example.com/intern.pdf",
    sampleOutput: "reject | quota-carrying experience | intern.pdf | 0.85",
    description:
      "Recruiting specialization in Sandbox until the screen eval set passes. Not an open-ended sourcer.",
  },
];

export function getAgent(slug: string): CatalogAgent | undefined {
  return CATALOG_AGENTS.find((a) => a.slug === slug);
}

export function canHire(agent: CatalogAgent): boolean {
  return agent.badge === "sla" && agent.hireMonthly !== null;
}

export type CompiledCatalogQuery = {
  templateId: string | null;
  slaOnly: boolean;
  certifiedOrBetter: boolean;
  maxCreditsPerRow: number | null;
  minEval: number | null;
  explanation: string;
};

const TEMPLATE_HINTS: [string, string[], string][] = [
  ["email_verify", ["bounce", "deliverability", "verify email", "email verify", "mailbox"], "email verify"],
  ["icp_fit", ["icp", "fit score", "ideal customer"], "ICP fit"],
  ["competitive_brief", ["competitor", "competitive", "cite", "research brief"], "competitive brief"],
  ["resume_screen", ["resume", "recruiter", "screen candidate", "hiring screen"], "resume screen"],
  ["lead_enrichment", ["enrich", "lead", "sdr", "founder", "ecommerce", "domain"], "lead enrichment"],
];

export function compileCatalogQuery(text: string): CompiledCatalogQuery {
  const q = text.toLowerCase();
  const bits: string[] = [];
  let templateId: string | null = null;
  for (const [id, words, label] of TEMPLATE_HINTS) {
    if (words.some((w) => q.includes(w))) {
      templateId = id;
      bits.push(`${label} template`);
      break;
    }
  }
  if (!templateId) bits.push("all live specializations");
  const slaOnly = ["hire", "retainer", "sla", "on staff"].some((w) => q.includes(w));
  if (slaOnly) bits.push("SLA/Hire only");
  const certifiedOrBetter = q.includes("certified") || q.includes("trusted") || slaOnly;
  if (certifiedOrBetter && !slaOnly) bits.push("Certified or SLA");
  let maxCreditsPerRow: number | null = null;
  if (["cheap", "budget", "inexpensive", "under"].some((w) => q.includes(w))) {
    maxCreditsPerRow = 15;
    bits.push("max 15 credits/row");
  }
  const minEval = ["reliable", "accurate", "high eval"].some((w) => q.includes(w)) ? 0.85 : null;
  if (minEval) bits.push(`min eval ${Math.round(minEval * 100)}%`);
  return { templateId, slaOnly, certifiedOrBetter, maxCreditsPerRow, minEval, explanation: bits.join("; ") };
}

export function searchCatalogAgents(
  text: string,
  agents: CatalogAgent[] = CATALOG_AGENTS,
  specialty: string | null = null,
): CatalogAgent[] {
  const compiled = compileCatalogQuery(text);
  const templateId = specialty ?? compiled.templateId;
  return agents
    .filter((agent) => {
      if (templateId && agent.templateId !== templateId) return false;
      if (compiled.slaOnly && agent.badge !== "sla") return false;
      if (compiled.certifiedOrBetter && agent.badge !== "certified" && agent.badge !== "sla") return false;
      if (compiled.maxCreditsPerRow != null && agent.creditsPerRun > compiled.maxCreditsPerRow) return false;
      if (compiled.minEval != null && agent.evalPassRate < compiled.minEval) return false;
      return true;
    })
    .sort((a, b) => {
      if (b.evalPassRate !== a.evalPassRate) return b.evalPassRate - a.evalPassRate;
      if (b.rating !== a.rating) return b.rating - a.rating;
      if (a.creditsPerRun !== b.creditsPerRun) return a.creditsPerRun - b.creditsPerRun;
      return 0;
    });
}
