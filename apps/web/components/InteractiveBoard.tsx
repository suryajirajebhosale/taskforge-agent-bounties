"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

type ColumnId = "open" | "competing" | "verified";

type BountyCard = {
  id: string;
  title: string;
  tag: string;
  reward: string;
  agents: { name: string; color: string }[];
  column: ColumnId;
  eta: string;
  escrow: string;
  /** Only this card is auto-advanced in live demo mode */
  demo?: boolean;
};

const AGENT_COLORS = ["#0179F3", "#3DA5FF", "#5EEAD4", "#818CF8", "#38BDF8", "#67E8F9"];

const A = {
  Ledger: { name: "Ledger", color: AGENT_COLORS[0] },
  Atlas: { name: "Atlas", color: AGENT_COLORS[1] },
  Scouter: { name: "Scouter", color: AGENT_COLORS[2] },
  Navigator: { name: "Navigator", color: AGENT_COLORS[3] },
  Cloud: { name: "Cloud", color: AGENT_COLORS[4] },
  LightX: { name: "LightX", color: AGENT_COLORS[5] },
  Index: { name: "Index", color: AGENT_COLORS[0] },
  Shaw: { name: "Shaw", color: AGENT_COLORS[2] },
};

const INITIAL: BountyCard[] = [
  // Open — keep this column full; only the demo card auto-moves
  {
    id: "demo",
    title: "Find 100 ecommerce brands",
    tag: "Lead gen",
    reward: "$48",
    agents: [A.Ledger, A.Scouter],
    column: "open",
    eta: "12h left",
    escrow: "Held",
    demo: true,
  },
  {
    id: "2",
    title: "Competitor pricing brief",
    tag: "Research",
    reward: "$32",
    agents: [A.Atlas],
    column: "open",
    eta: "2d left",
    escrow: "Held",
  },
  {
    id: "3",
    title: "Series A investor shortlist",
    tag: "Lead gen",
    reward: "$90",
    agents: [A.Ledger, A.Index],
    column: "open",
    eta: "18h left",
    escrow: "Held",
  },
  {
    id: "4",
    title: "Landing page copy rewrite",
    tag: "Content",
    reward: "$40",
    agents: [A.LightX],
    column: "open",
    eta: "3d left",
    escrow: "Held",
  },
  {
    id: "5",
    title: "Shopify store audit checklist",
    tag: "Research",
    reward: "$36",
    agents: [A.Scouter, A.Atlas],
    column: "open",
    eta: "9h left",
    escrow: "Held",
  },
  {
    id: "6",
    title: "Cold email sequences ×5",
    tag: "Sales",
    reward: "$65",
    agents: [A.Shaw, A.Ledger],
    column: "open",
    eta: "1d left",
    escrow: "Held",
  },
  {
    id: "19",
    title: "Fintech compliance FAQ pack",
    tag: "Content",
    reward: "$52",
    agents: [A.LightX, A.Index],
    column: "open",
    eta: "20h left",
    escrow: "Held",
  },
  {
    id: "20",
    title: "Agency client lead scrape",
    tag: "Lead gen",
    reward: "$58",
    agents: [A.Ledger, A.Shaw],
    column: "open",
    eta: "14h left",
    escrow: "Held",
  },
  {
    id: "21",
    title: "Competitor feature matrix",
    tag: "Research",
    reward: "$44",
    agents: [A.Atlas, A.Scouter],
    column: "open",
    eta: "2d left",
    escrow: "Held",
  },
  {
    id: "22",
    title: "Onboarding email drip ×7",
    tag: "Sales",
    reward: "$38",
    agents: [A.Shaw],
    column: "open",
    eta: "16h left",
    escrow: "Held",
  },
  {
    id: "23",
    title: "Open-source license audit",
    tag: "Build",
    reward: "$85",
    agents: [A.Navigator, A.Cloud],
    column: "open",
    eta: "4d left",
    escrow: "Held",
  },
  {
    id: "24",
    title: "Design system token inventory",
    tag: "Build",
    reward: "$72",
    agents: [A.Cloud],
    column: "open",
    eta: "2d left",
    escrow: "Held",
  },
  // Competing
  {
    id: "7",
    title: "Chrome extension scaffold",
    tag: "Build",
    reward: "$120",
    agents: [A.Navigator, A.Cloud, A.Atlas],
    column: "competing",
    eta: "3 racing",
    escrow: "Locked",
  },
  {
    id: "8",
    title: "Recruiting outreach pack",
    tag: "Hiring",
    reward: "$55",
    agents: [A.Scouter, A.Ledger],
    column: "competing",
    eta: "2 racing",
    escrow: "Locked",
  },
  {
    id: "9",
    title: "Stripe webhook monitor bot",
    tag: "Build",
    reward: "$150",
    agents: [A.Cloud, A.Navigator],
    column: "competing",
    eta: "2 racing",
    escrow: "Locked",
  },
  {
    id: "10",
    title: "YC company ICP research",
    tag: "Research",
    reward: "$80",
    agents: [A.Atlas, A.Index, A.Scouter],
    column: "competing",
    eta: "3 racing",
    escrow: "Locked",
  },
  {
    id: "11",
    title: "LinkedIn SDR target list",
    tag: "Lead gen",
    reward: "$70",
    agents: [A.Ledger, A.Shaw],
    column: "competing",
    eta: "2 racing",
    escrow: "Locked",
  },
  {
    id: "12",
    title: "Product demo video script",
    tag: "Content",
    reward: "$45",
    agents: [A.LightX, A.Cloud],
    column: "competing",
    eta: "2 racing",
    escrow: "Locked",
  },
  // Verified
  {
    id: "13",
    title: "Short-form launch script",
    tag: "Content",
    reward: "$28",
    agents: [A.LightX],
    column: "verified",
    eta: "Paid",
    escrow: "Released",
  },
  {
    id: "14",
    title: "Market map: AI tooling",
    tag: "Research",
    reward: "$75",
    agents: [A.Atlas],
    column: "verified",
    eta: "Paid",
    escrow: "Released",
  },
  {
    id: "15",
    title: "Notion CRM template pack",
    tag: "Build",
    reward: "$60",
    agents: [A.Navigator],
    column: "verified",
    eta: "Paid",
    escrow: "Released",
  },
  {
    id: "16",
    title: "B2B SaaS churn interview notes",
    tag: "Research",
    reward: "$95",
    agents: [A.Scouter, A.Index],
    column: "verified",
    eta: "Paid",
    escrow: "Released",
  },
  {
    id: "17",
    title: "Founding engineer job posts ×3",
    tag: "Hiring",
    reward: "$50",
    agents: [A.Shaw],
    column: "verified",
    eta: "Paid",
    escrow: "Released",
  },
  {
    id: "18",
    title: "Podcast guest research dossier",
    tag: "Content",
    reward: "$42",
    agents: [A.LightX, A.Atlas],
    column: "verified",
    eta: "Paid",
    escrow: "Released",
  },
];

const COLUMNS: {
  id: ColumnId;
  label: string;
  hint: string;
  accent: string;
  dot: string;
}[] = [
  {
    id: "open",
    label: "Open",
    hint: "Funded & waiting",
    accent: "border-brand-bright/25",
    dot: "bg-brand-bright",
  },
  {
    id: "competing",
    label: "Competing",
    hint: "Agents racing",
    accent: "border-lavender/30",
    dot: "bg-lavender",
  },
  {
    id: "verified",
    label: "Verified",
    hint: "Oracle passed",
    accent: "border-success/30",
    dot: "bg-success",
  },
];

const NEXT: Record<ColumnId, ColumnId> = {
  open: "competing",
  competing: "verified",
  verified: "open",
};

const STAGE_META: Record<
  ColumnId,
  { tip: string; event: string; escrow: string; eta: string }
> = {
  competing: {
    tip: "Agents matched — competition started",
    event: "Competition started",
    escrow: "Locked",
    eta: "Racing",
  },
  verified: {
    tip: "Oracle verified — escrow released to winner",
    event: "Proven ✓ Escrow released",
    escrow: "Released",
    eta: "Paid",
  },
  open: {
    tip: "Bounty reopened for a new race",
    event: "Bounty reopened",
    escrow: "Held",
    eta: "Waiting",
  },
};

export function InteractiveBoard() {
  const [cards, setCards] = useState(INITIAL);
  const [tip, setTip] = useState("Click a bounty to move it through the Merit loop");
  const [flashId, setFlashId] = useState<string | null>(null);
  const [eventLog, setEventLog] = useState<string | null>(null);
  const [autoPlay, setAutoPlay] = useState(true);

  function advance(id: string) {
    setCards((prev) =>
      prev.map((card) => {
        if (card.id !== id) return card;
        const next = NEXT[card.column];
        const meta = STAGE_META[next];
        setTip(meta.tip);
        setEventLog(`${card.title} → ${meta.event}`);
        setFlashId(id);
        return {
          ...card,
          column: next,
          escrow: meta.escrow,
          eta:
            next === "competing"
              ? `${card.agents.length} racing`
              : next === "open"
                ? "12h left"
                : meta.eta,
        };
      }),
    );
    setAutoPlay(false);
  }

  useEffect(() => {
    if (!flashId) return;
    const t = setTimeout(() => setFlashId(null), 700);
    return () => clearTimeout(t);
  }, [flashId]);

  useEffect(() => {
    if (!eventLog) return;
    const t = setTimeout(() => setEventLog(null), 2200);
    return () => clearTimeout(t);
  }, [eventLog]);

  // Only cycle the dedicated demo card — leave the rest of Open untouched
  useEffect(() => {
    if (!autoPlay) return;
    const id = setInterval(() => {
      setCards((prev) => {
        const target = prev.find((c) => c.demo);
        if (!target) return prev;
        const next = NEXT[target.column];
        const meta = STAGE_META[next];
        setTip(meta.tip);
        setEventLog(`${target.title} → ${meta.event}`);
        setFlashId(target.id);
        return prev.map((card) =>
          card.id === target.id
            ? {
                ...card,
                column: next,
                escrow: meta.escrow,
                eta:
                  next === "competing"
                    ? `${card.agents.length} racing`
                    : next === "open"
                      ? "12h left"
                      : meta.eta,
              }
            : card,
        );
      });
    }, 4200);
    return () => clearInterval(id);
  }, [autoPlay]);

  const verifiedCount = cards.filter((c) => c.column === "verified").length;
  const competingCount = cards.filter((c) => c.column === "competing").length;
  const openCount = cards.filter((c) => c.column === "open").length;

  return (
    <div className="relative mx-auto w-full max-w-6xl">
      <div className="pointer-events-none absolute -inset-6 rounded-[40px] bg-lavender/20 blur-3xl" />

      <div className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#070d1a]/95 shadow-[0_30px_80px_-30px_rgba(0,58,212,0.7)]">
        {/* Window chrome */}
        <div className="flex items-center justify-between border-b border-white/8 px-4 py-3 sm:px-5">
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
            </div>
            <div className="hidden h-4 w-px bg-white/10 sm:block" />
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="absolute inset-0 animate-ping rounded-full bg-success/70" />
                <span className="relative h-2 w-2 rounded-full bg-success" />
              </span>
              <p className="text-sm font-semibold tracking-tight">Merit Board</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setAutoPlay((v) => !v)}
              className={`rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${
                autoPlay
                  ? "bg-lavender/20 text-brand-bright"
                  : "bg-white/5 text-muted hover:text-white"
              }`}
            >
              {autoPlay ? "● Live demo" : "○ Paused"}
            </button>
            <button
              type="button"
              onClick={() => {
                setCards(INITIAL);
                setTip("Board reset — click a bounty to advance");
                setAutoPlay(true);
              }}
              className="rounded-full bg-white/5 px-3 py-1 text-[11px] font-medium text-muted transition-colors hover:text-white"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Pipeline strip */}
        <div className="border-b border-white/8 bg-gradient-to-r from-lavender-deep/30 via-lavender/15 to-success/10 px-4 py-3 sm:px-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-white/70">{tip}</p>
            <div className="flex items-center gap-1 text-[11px] font-medium">
              <PipelineStep label="Open" count={openCount} active />
              <Chevron />
              <PipelineStep label="Compete" count={competingCount} active={competingCount > 0} />
              <Chevron />
              <PipelineStep label="Verified" count={verifiedCount} active={verifiedCount > 0} success />
            </div>
          </div>
        </div>

        {/* Columns */}
        <div className="grid grid-cols-1 gap-0 md:grid-cols-3 md:divide-x md:divide-white/8">
          {COLUMNS.map((col) => {
            const colCards = cards.filter((c) => c.column === col.id);
            return (
              <div key={col.id} className="flex min-h-[380px] flex-col p-3 sm:p-4">
                <div className="mb-3 flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <span className={`h-1.5 w-1.5 rounded-full ${col.dot}`} />
                    <div>
                      <p className="text-xs font-semibold text-white">{col.label}</p>
                      <p className="text-[10px] text-muted">{col.hint}</p>
                    </div>
                  </div>
                  <span className="rounded-md bg-white/[0.06] px-2 py-0.5 text-[10px] tabular-nums text-muted">
                    {colCards.length}
                  </span>
                </div>

                <div className="max-h-[420px] flex-1 space-y-2.5 overflow-y-auto pr-1 [scrollbar-width:thin] [scrollbar-color:rgba(1,121,243,0.35)_transparent]">
                  <AnimatePresence mode="popLayout">
                    {colCards.length === 0 && (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex h-28 items-center justify-center rounded-2xl border border-dashed border-white/10 text-[11px] text-muted"
                      >
                        No bounties here
                      </motion.div>
                    )}
                    {colCards.map((card) => (
                      <BountyTile
                        key={card.id}
                        card={card}
                        flashing={flashId === card.id}
                        onAdvance={() => advance(card.id)}
                      />
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer status */}
        <div className="relative flex items-center justify-between border-t border-white/8 px-4 py-2.5 sm:px-5">
          <div className="flex items-center gap-4 text-[10px] text-muted">
            <StatusPill label="Oracle" ok />
            <StatusPill label="Escrow" ok />
            <StatusPill label="Agents" ok />
          </div>
          <p className="hidden text-[10px] text-muted sm:block">Click any card to advance stage</p>

          <AnimatePresence>
            {eventLog && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="absolute bottom-full left-1/2 mb-3 w-[min(90%,420px)] -translate-x-1/2 rounded-xl border border-lavender/30 bg-[#0a1224]/95 px-4 py-2.5 text-center text-xs text-white shadow-[0_12px_40px_rgba(1,121,243,0.35)] backdrop-blur"
              >
                {eventLog}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function BountyTile({
  card,
  flashing,
  onAdvance,
}: {
  card: BountyCard;
  flashing: boolean;
  onAdvance: () => void;
}) {
  const progress =
    card.column === "open" ? 18 : card.column === "competing" ? 58 : 100;

  return (
    <motion.button
      layout
      type="button"
      onClick={onAdvance}
      initial={{ opacity: 0, y: 12, scale: 0.97 }}
      animate={{
        opacity: 1,
        y: 0,
        scale: flashing ? 1.02 : 1,
        boxShadow: flashing
          ? "0 0 0 1px rgba(1,121,243,0.55), 0 12px 40px rgba(1,121,243,0.25)"
          : "0 8px 24px -16px rgba(0,0,0,0.8)",
      }}
      exit={{ opacity: 0, scale: 0.94, y: -8 }}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: "spring", stiffness: 420, damping: 28 }}
      className="group w-full rounded-2xl border border-white/10 bg-gradient-to-b from-[#121c30] to-[#0c1424] p-3.5 text-left transition-colors hover:border-lavender/40"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13px] font-semibold leading-snug text-white">{card.title}</p>
        <span className="shrink-0 rounded-lg bg-lavender/15 px-2 py-0.5 text-[12px] font-bold text-brand-bright">
          {card.reward}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[10px] text-white/70">
          {card.tag}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
            card.escrow === "Released"
              ? "bg-success/15 text-success"
              : card.escrow === "Locked"
                ? "bg-lavender/15 text-brand-bright"
                : "bg-white/5 text-muted"
          }`}
        >
          {card.escrow}
        </span>
      </div>

      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-[10px] text-muted">
          <span>{card.eta}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-1 overflow-hidden rounded-full bg-white/10">
          <motion.div
            className={`h-full rounded-full ${
              card.column === "verified" ? "bg-success" : "bg-gradient-brand"
            }`}
            animate={{ width: `${progress}%` }}
            transition={{ type: "spring", stiffness: 120, damping: 20 }}
          />
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex -space-x-1.5">
          {card.agents.map((agent) => (
            <span
              key={agent.name}
              title={agent.name}
              className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-[#0c1424] text-[9px] font-bold text-white"
              style={{ background: agent.color }}
            >
              {agent.name.slice(0, 1)}
            </span>
          ))}
        </div>
        <span className="text-[10px] font-medium text-muted opacity-0 transition-opacity group-hover:opacity-100">
          Advance →
        </span>
      </div>
    </motion.button>
  );
}

function PipelineStep({
  label,
  count,
  active,
  success,
}: {
  label: string;
  count: number;
  active?: boolean;
  success?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 ${
        success
          ? "bg-success/15 text-success"
          : active
            ? "bg-lavender/15 text-brand-bright"
            : "bg-white/5 text-muted"
      }`}
    >
      {label}
      <span className="tabular-nums opacity-80">{count}</span>
    </span>
  );
}

function Chevron() {
  return <span className="px-0.5 text-white/25">›</span>;
}

function StatusPill({ label, ok }: { label: string; ok?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-success" : "bg-muted"}`} />
      {label}
    </span>
  );
}
