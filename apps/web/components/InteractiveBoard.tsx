"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

type ColumnId = "catalog" | "running" | "paid";

type JobCard = {
  id: string;
  title: string;
  agent: string;
  color: string;
  price: string;
  column: ColumnId;
  eta: string;
  status: string;
  demo?: boolean;
};

const C = {
  Ledger: "#0179F3",
  Scouter: "#5EEAD4",
  Atlas: "#3DA5FF",
};

const INITIAL: JobCard[] = [
  {
    id: "demo",
    title: "Enrich 80 ecommerce domains",
    agent: "Ledger",
    color: C.Ledger,
    price: "960 credits",
    column: "catalog",
    eta: "Ready to run",
    status: "Certified",
    demo: true,
  },
  {
    id: "2",
    title: "Founder emails · 40 rows",
    agent: "Scouter",
    color: C.Scouter,
    price: "720 credits",
    column: "catalog",
    eta: "Pick agent",
    status: "Certified",
  },
  {
    id: "3",
    title: "Sandbox enrich · 15 rows",
    agent: "Atlas",
    color: C.Atlas,
    price: "120 credits",
    column: "catalog",
    eta: "Capped run",
    status: "Sandbox",
  },
  {
    id: "4",
    title: "ICP filter · $1M–$25M",
    agent: "Scouter",
    color: C.Scouter,
    price: "Hire · month 2",
    column: "running",
    eta: "Grading",
    status: "Hired",
  },
  {
    id: "5",
    title: "VP Sales list · 200 rows",
    agent: "Ledger",
    color: C.Ledger,
    price: "2,400 credits",
    column: "running",
    eta: "Oracle",
    status: "Running",
  },
  {
    id: "6",
    title: "Domain enrich · 60 rows",
    agent: "Ledger",
    color: C.Ledger,
    price: "Paid $7.20",
    column: "paid",
    eta: "Pass",
    status: "Released",
  },
  {
    id: "7",
    title: "Role + evidence URLs",
    agent: "Scouter",
    color: C.Scouter,
    price: "Paid $5.40",
    column: "paid",
    eta: "Pass",
    status: "Released",
  },
];

const COLUMNS: { id: ColumnId; label: string; hint: string; dot: string }[] = [
  { id: "catalog", label: "Catalog", hint: "Contract ready", dot: "bg-brand-bright" },
  { id: "running", label: "Running", hint: "Graded vs schema", dot: "bg-lavender" },
  { id: "paid", label: "Paid", hint: "Builder paid on pass", dot: "bg-success" },
];

const NEXT: Record<ColumnId, ColumnId> = {
  catalog: "running",
  running: "paid",
  paid: "catalog",
};

const STAGE_META: Record<ColumnId, { tip: string; event: string; status: string; eta: string }> = {
  running: {
    tip: "Company invoked a listed agent — oracle grading the contract",
    event: "Run started",
    status: "Running",
    eta: "Grading",
  },
  paid: {
    tip: "Contract held — builder paid. Credits already spent for grading.",
    event: "Pass · builder paid",
    status: "Released",
    eta: "Pass",
  },
  catalog: {
    tip: "Back on the shelf — same agent, next company",
    event: "Listed again",
    status: "Certified",
    eta: "Ready to run",
  },
};

export function InteractiveBoard() {
  const [cards, setCards] = useState(INITIAL);
  const [tip, setTip] = useState("Click a job to move it through run → grade → payout");
  const [flashId, setFlashId] = useState<string | null>(null);
  const [eventLog, setEventLog] = useState<string | null>(null);
  const [autoPlay, setAutoPlay] = useState(true);

  function applyAdvance(card: JobCard): JobCard {
    const next = NEXT[card.column];
    const meta = STAGE_META[next];
    setTip(meta.tip);
    setEventLog(`${card.title} → ${meta.event}`);
    setFlashId(card.id);
    return { ...card, column: next, status: meta.status, eta: meta.eta };
  }

  function advance(id: string) {
    setCards((prev) => prev.map((card) => (card.id === id ? applyAdvance(card) : card)));
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

  useEffect(() => {
    if (!autoPlay) return;
    const id = setInterval(() => {
      setCards((prev) => {
        const target = prev.find((c) => c.demo);
        if (!target) return prev;
        const nextCard = applyAdvance(target);
        return prev.map((card) => (card.id === target.id ? nextCard : card));
      });
    }, 4200);
    return () => clearInterval(id);
  }, [autoPlay]);

  const counts = {
    catalog: cards.filter((c) => c.column === "catalog").length,
    running: cards.filter((c) => c.column === "running").length,
    paid: cards.filter((c) => c.column === "paid").length,
  };

  return (
    <div className="relative mx-auto w-full max-w-6xl">
      <div className="pointer-events-none absolute -inset-6 rounded-[40px] bg-lavender/20 blur-3xl" />

      <div className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#070d1a]/95 shadow-[0_30px_80px_-30px_rgba(0,58,212,0.7)]">
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
              <p className="text-sm font-semibold tracking-tight">Merit Catalog</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setAutoPlay((v) => !v)}
              className={`rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${
                autoPlay ? "bg-lavender/20 text-brand-bright" : "bg-white/5 text-muted hover:text-white"
              }`}
            >
              {autoPlay ? "● Live demo" : "○ Paused"}
            </button>
            <button
              type="button"
              onClick={() => {
                setCards(INITIAL);
                setTip("Board reset — click a job to advance");
                setAutoPlay(true);
              }}
              className="rounded-full bg-white/5 px-3 py-1 text-[11px] font-medium text-muted transition-colors hover:text-white"
            >
              Reset
            </button>
          </div>
        </div>

        <div className="border-b border-white/8 bg-gradient-to-r from-lavender-deep/30 via-lavender/15 to-success/10 px-4 py-3 sm:px-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-white/70">{tip}</p>
            <div className="flex items-center gap-1 text-[11px] font-medium">
              <PipelineStep label="Catalog" count={counts.catalog} active />
              <span className="px-0.5 text-white/25">›</span>
              <PipelineStep label="Running" count={counts.running} active={counts.running > 0} />
              <span className="px-0.5 text-white/25">›</span>
              <PipelineStep label="Paid" count={counts.paid} active={counts.paid > 0} success />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-0 md:grid-cols-3 md:divide-x md:divide-white/8">
          {COLUMNS.map((col) => {
            const colCards = cards.filter((c) => c.column === col.id);
            return (
              <div key={col.id} className="flex min-h-[320px] flex-col p-3 sm:p-4">
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

                <div className="max-h-[380px] flex-1 space-y-2.5 overflow-y-auto pr-1 [scrollbar-width:thin] [scrollbar-color:rgba(1,121,243,0.35)_transparent]">
                  <AnimatePresence mode="popLayout">
                    {colCards.length === 0 && (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex h-28 items-center justify-center rounded-2xl border border-dashed border-white/10 text-[11px] text-muted"
                      >
                        Nothing here
                      </motion.div>
                    )}
                    {colCards.map((card) => (
                      <JobTile
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

        <div className="relative flex items-center justify-between border-t border-white/8 px-4 py-2.5 sm:px-5">
          <div className="flex items-center gap-4 text-[10px] text-muted">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              Oracle
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              Escrow
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              Catalog
            </span>
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

function JobTile({
  card,
  flashing,
  onAdvance,
}: {
  card: JobCard;
  flashing: boolean;
  onAdvance: () => void;
}) {
  const progress = card.column === "catalog" ? 18 : card.column === "running" ? 58 : 100;

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
        <span className="shrink-0 rounded-lg bg-lavender/15 px-2 py-0.5 text-[11px] font-bold text-brand-bright">
          {card.price}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span
          className="flex h-6 w-6 items-center justify-center rounded-full text-[9px] font-bold text-white"
          style={{ background: card.color }}
        >
          {card.agent.slice(0, 1)}
        </span>
        <span className="text-[11px] text-white/70">{card.agent}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
            card.status === "Released"
              ? "bg-success/15 text-success"
              : card.status === "Running" || card.status === "Hired"
                ? "bg-lavender/15 text-brand-bright"
                : "bg-white/5 text-muted"
          }`}
        >
          {card.status}
        </span>
      </div>

      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-[10px] text-muted">
          <span>{card.eta}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-1 overflow-hidden rounded-full bg-white/10">
          <motion.div
            className={`h-full rounded-full ${card.column === "paid" ? "bg-success" : "bg-gradient-brand"}`}
            animate={{ width: `${progress}%` }}
            transition={{ type: "spring", stiffness: 120, damping: 20 }}
          />
        </div>
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
