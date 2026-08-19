"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { MeritLogo } from "@/components/MeritLogo";
import { clearSession, getSession, saveSession, type MeritSession } from "@/lib/session";
import type { ChatMessage, TaskReport } from "@/lib/bounty-types";

type Step = "signup" | "describe" | "clarify" | "report" | "done";

const STEPS: { id: Step; label: string }[] = [
  { id: "signup", label: "Account" },
  { id: "describe", label: "Brief" },
  { id: "clarify", label: "Clarify" },
  { id: "report", label: "Report" },
  { id: "done", label: "Approve" },
];

export function PostFlow() {
  const [session, setSession] = useState<MeritSession | null>(null);
  const [step, setStep] = useState<Step>("signup");
  const [brief, setBrief] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [report, setReport] = useState<TaskReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const existing = getSession();
    if (existing) {
      setSession(existing);
      setStep("describe");
    }
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function onSignup(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const name = String(fd.get("name") ?? "").trim();
    const email = String(fd.get("email") ?? "").trim();
    const password = String(fd.get("password") ?? "");
    if (!name || !email || password.length < 6) {
      setError("Use a name, email, and password (6+ characters).");
      return;
    }
    const next = { name, email, createdAt: new Date().toISOString() };
    saveSession(next);
    setSession(next);
    setError(null);
    setStep("describe");
  }

  async function startClarify(e: FormEvent) {
    e.preventDefault();
    if (brief.trim().length < 12) {
      setError("Give a bit more detail — at least a sentence.");
      return;
    }
    setError(null);
    setLoading(true);
    setStep("clarify");
    setMessages([]);
    try {
      const res = await fetch("/api/bounty/clarify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief, history: [] }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setMessages([{ role: "assistant", content: data.reply }]);
      if (data.readyForReport) await buildReport([{ role: "assistant", content: data.reply }]);
    } catch {
      setError("Couldn’t start clarification. Try again.");
      setStep("describe");
    } finally {
      setLoading(false);
    }
  }

  async function sendClarify(e: FormEvent) {
    e.preventDefault();
    if (!draft.trim() || loading) return;
    const userMsg: ChatMessage = { role: "user", content: draft.trim() };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setDraft("");
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/bounty/clarify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief, history: nextHistory }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      const withAssistant = [...nextHistory, { role: "assistant" as const, content: data.reply }];
      setMessages(withAssistant);
      if (data.readyForReport) await buildReport(withAssistant);
    } catch {
      setError("Reply failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function buildReport(history: ChatMessage[]) {
    setLoading(true);
    try {
      const res = await fetch("/api/bounty/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief, history }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setReport(data.report);
      setStep("report");
    } catch {
      setError("Couldn’t draft the task report.");
    } finally {
      setLoading(false);
    }
  }

  function approve() {
    setStep("done");
  }

  function signOut() {
    clearSession();
    setSession(null);
    setStep("signup");
    setBrief("");
    setMessages([]);
    setReport(null);
  }

  const stepIndex = STEPS.findIndex((s) => s.id === step);

  return (
    <div className="mx-auto max-w-3xl px-6 py-10 sm:px-8 sm:py-14">
      <div className="mb-10 flex items-center justify-between gap-4">
        <Link href="/" className="inline-flex items-center gap-2">
          <MeritLogo size={32} showWordmark animate={false} />
        </Link>
        {session && (
          <div className="flex items-center gap-3 text-xs text-muted">
            <span className="hidden sm:inline">{session.email}</span>
            <button
              type="button"
              onClick={signOut}
              className="rounded-full border border-white/10 px-3 py-1.5 hover:border-lavender/40 hover:text-white"
            >
              Sign out
            </button>
          </div>
        )}
      </div>

      <div className="mb-8 flex flex-wrap gap-2">
        {STEPS.map((s, i) => (
          <div
            key={s.id}
            className={`rounded-full px-3 py-1 text-[11px] font-medium ${
              i < stepIndex
                ? "bg-success/15 text-success"
                : i === stepIndex
                  ? "bg-lavender/20 text-brand-bright"
                  : "bg-white/5 text-muted"
            }`}
          >
            {i + 1}. {s.label}
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {step === "signup" && (
          <Panel key="signup">
            <Eyebrow>Sign up required</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Create your Merit account
            </h1>
            <p className="mt-3 text-sm text-muted">
              Bounty posting is gated — so every task report is tied to a real requester
              before escrow funding.
            </p>
            <form onSubmit={onSignup} className="mt-8 space-y-4">
              <Field label="Name" name="name" type="text" required />
              <Field label="Work email" name="email" type="email" required />
              <Field label="Password" name="password" type="password" required minLength={6} />
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Primary type="submit">Continue →</Primary>
            </form>
            <p className="mt-4 text-[11px] text-muted">
              Demo auth for now (saved locally). Wire Clerk / Auth.js when you go live.
            </p>
          </Panel>
        )}

        {step === "describe" && (
          <Panel key="describe">
            <Eyebrow>Step 1 · Brief</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight">What do you need done?</h1>
            <p className="mt-3 text-sm text-muted">
              Describe the outcome in plain English. Merit will clarify, then draft a
              machine-checkable task report for you to approve.
            </p>
            <form onSubmit={startClarify} className="mt-8 space-y-4">
              <textarea
                value={brief}
                onChange={(e) => setBrief(e.target.value)}
                rows={6}
                placeholder="e.g. Find 100 ecommerce brands doing $1M–$25M in revenue, with founder emails…"
                className="w-full rounded-2xl border border-white/10 bg-panel-soft px-4 py-3 text-sm outline-none focus:border-lavender"
              />
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Primary type="submit" disabled={loading}>
                {loading ? "Starting…" : "Clarify with AI →"}
              </Primary>
            </form>
          </Panel>
        )}

        {step === "clarify" && (
          <Panel key="clarify">
            <Eyebrow>Step 2 · Clarify</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight">Merit is scoping your bounty</h1>
            <p className="mt-2 text-sm text-muted">Answer a few questions so the oracle can grade fairly.</p>

            <div className="mt-6 max-h-[420px] space-y-3 overflow-y-auto rounded-2xl border border-white/8 bg-background/40 p-4">
              <div className="rounded-xl border border-lavender/20 bg-lavender/10 px-3 py-2 text-xs text-brand-bright">
                Brief: {brief}
              </div>
              {messages.map((m, i) => (
                <div
                  key={`${m.role}-${i}`}
                  className={`whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm ${
                    m.role === "assistant"
                      ? "border border-white/8 bg-panel-soft text-white/90"
                      : "ml-8 bg-lavender/20 text-white"
                  }`}
                >
                  {m.content}
                </div>
              ))}
              {loading && (
                <div className="rounded-2xl border border-white/8 bg-panel-soft px-4 py-3 text-sm text-muted">
                  Thinking…
                </div>
              )}
              <div ref={chatEnd} />
            </div>

            <form onSubmit={sendClarify} className="mt-4 flex gap-2">
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Your answer…"
                className="flex-1 rounded-full border border-white/10 bg-panel-soft px-4 py-3 text-sm outline-none focus:border-lavender"
              />
              <button
                type="submit"
                disabled={loading || !draft.trim()}
                className="rounded-full bg-gradient-brand px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"
              >
                Send
              </button>
            </form>
            {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
            <button
              type="button"
              onClick={() => buildReport(messages)}
              disabled={loading || messages.length < 2}
              className="mt-3 text-xs text-muted underline-offset-2 hover:text-brand-bright hover:underline disabled:opacity-40"
            >
              Skip ahead — draft report now
            </button>
          </Panel>
        )}

        {step === "report" && report && (
          <Panel key="report">
            <Eyebrow>Step 3 · Task report</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight">Review & approve</h1>
            <p className="mt-2 text-sm text-muted">
              This becomes the locked definition of done once you fund escrow.
            </p>

            <div className="mt-6 space-y-4 rounded-3xl border border-white/10 bg-panel-soft/80 p-5 sm:p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs text-muted">{report.category}</p>
                  <h2 className="mt-1 text-xl font-semibold">{report.title}</h2>
                </div>
                <div className="text-right text-sm">
                  <p className="font-bold text-brand-bright">{report.suggestedReward}</p>
                  <p className="text-xs text-muted">{report.deadline}</p>
                </div>
              </div>
              <p className="text-sm text-white/80">{report.summary}</p>

              <Section title="Deliverables">
                <ul className="space-y-1.5 text-sm text-white/80">
                  {report.deliverables.map((d) => (
                    <li key={d}>• {d}</li>
                  ))}
                </ul>
              </Section>

              <Section title="Objective criteria">
                <ul className="space-y-1.5 text-sm text-white/80">
                  {report.objectiveCriteria.map((c) => (
                    <li key={c.field}>
                      <span className="text-brand-bright">{c.field}</span> {c.rule}
                    </li>
                  ))}
                </ul>
              </Section>

              <Section title="Subjective criteria">
                <ul className="space-y-1.5 text-sm text-white/80">
                  {report.subjectiveCriteria.map((c) => (
                    <li key={c.description}>
                      {c.description}{" "}
                      <span className="text-muted">({Math.round(c.weight * 100)}%)</span>
                    </li>
                  ))}
                </ul>
              </Section>

              <Section title="Acceptance">
                <p className="text-sm text-white/80">{report.acceptanceNotes}</p>
              </Section>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <Primary type="button" onClick={approve}>
                Approve task report →
              </Primary>
              <button
                type="button"
                onClick={() => {
                  setStep("clarify");
                  setReport(null);
                }}
                className="rounded-full border border-white/15 px-5 py-3 text-sm font-semibold text-white/80 hover:border-lavender/40"
              >
                Back to clarify
              </button>
            </div>
          </Panel>
        )}

        {step === "done" && report && (
          <Panel key="done">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-brand text-2xl text-white">
              ✓
            </div>
            <h1 className="mt-5 text-center text-3xl font-bold tracking-tight">Report approved</h1>
            <p className="mx-auto mt-3 max-w-md text-center text-sm text-muted">
              <span className="text-white">{report.title}</span> is ready. Next: fund escrow and let
              agents compete. Payout wiring lands with Stripe Connect.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link
                href="/"
                className="rounded-full bg-gradient-brand px-6 py-3 text-sm font-semibold text-white"
              >
                Back to Merit
              </Link>
              <button
                type="button"
                onClick={() => {
                  setBrief("");
                  setMessages([]);
                  setReport(null);
                  setStep("describe");
                }}
                className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-white/80"
              >
                Post another
              </button>
            </div>
          </Panel>
        )}
      </AnimatePresence>
    </div>
  );
}

function Panel({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.35 }}
      className="rounded-[28px] border border-white/10 bg-[#070d1a]/90 p-6 shadow-[0_30px_80px_-40px_rgba(0,58,212,0.7)] sm:p-8"
    >
      {children}
    </motion.div>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">{children}</p>
  );
}

function Field({
  label,
  name,
  type,
  required,
  minLength,
}: {
  label: string;
  name: string;
  type: string;
  required?: boolean;
  minLength?: number;
}) {
  return (
    <label className="block text-xs font-medium text-muted">
      {label}
      <input
        name={name}
        type={type}
        required={required}
        minLength={minLength}
        className="mt-2 w-full rounded-xl border border-white/10 bg-panel-soft px-4 py-3 text-sm text-foreground outline-none focus:border-lavender"
      />
    </label>
  );
}

function Primary({
  children,
  type = "button",
  onClick,
  disabled,
}: {
  children: React.ReactNode;
  type?: "button" | "submit";
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className="w-full rounded-full bg-gradient-brand py-3 text-sm font-semibold text-white shadow-[0_12px_40px_rgba(1,121,243,0.35)] disabled:opacity-50 sm:w-auto sm:px-8"
    >
      {children}
    </button>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-white/8 pt-4">
      <p className="mb-2 text-xs font-semibold tracking-wide text-lavender uppercase">{title}</p>
      {children}
    </div>
  );
}
