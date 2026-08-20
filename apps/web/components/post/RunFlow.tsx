"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AnimatePresence } from "framer-motion";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CATALOG_AGENTS, SPECIALIZATIONS, canHire, getAgent, type CatalogAgent } from "@/lib/catalog";
import { getSession, saveSession, type MeritSession } from "@/lib/session";
import {
  Eyebrow,
  FlowHeader,
  Panel,
  Primary,
  SignupForm,
  handleSignup,
} from "./flow-ui";

type Step = "signup" | "job" | "agent" | "confirm" | "done";

export function RunFlow() {
  const search = useSearchParams();
  const presetSlug = search.get("agent");
  const wantHire = search.get("hire") === "1";

  const [session, setSession] = useState<MeritSession | null>(null);
  const [step, setStep] = useState<Step>("signup");
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState("");
  const [agent, setAgent] = useState<CatalogAgent | null>(null);
  const [mode, setMode] = useState<"run" | "hire">(wantHire ? "hire" : "run");
  const [specId, setSpecId] = useState<string>(SPECIALIZATIONS[0].id);

  useEffect(() => {
    const existing = getSession();
    if (existing) {
      setSession(existing);
      setStep("job");
    }
    const preset = presetSlug ? getAgent(presetSlug) : undefined;
    if (preset) {
      setAgent(preset);
      setSpecId(preset.templateId);
    }
  }, [presetSlug]);

  const spec = useMemo(
    () => SPECIALIZATIONS.find((s) => s.id === specId) ?? SPECIALIZATIONS[0],
    [specId],
  );
  const listed = useMemo(
    () => CATALOG_AGENTS.filter((a) => a.templateId === specId),
    [specId],
  );

  const rowCount = useMemo(
    () =>
      rows
        .split(/[\n,]+/)
        .map((s) => s.trim())
        .filter(Boolean).length,
    [rows],
  );

  const credits = agent ? rowCount * agent.creditsPerRun : 0;

  function onSignup(e: FormEvent<HTMLFormElement>) {
    const err = handleSignup(e, (next) => {
      saveSession(next);
      setSession(next);
      setStep("job");
    });
    setError(err);
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-10 sm:px-8 sm:py-14">
      <FlowHeader
        session={session}
        onSignOut={() => {
          setSession(null);
          setStep("signup");
        }}
      />

      <AnimatePresence mode="wait">
        {step === "signup" && <SignupForm key="signup" error={error} onSubmit={onSignup} />}

        {step === "job" && (
          <Panel key="job">
            <Eyebrow>Step 1 · Contract</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight">{spec.title}</h1>
            <p className="mt-3 text-sm text-muted">
              Locked template: in {spec.input}. Out {spec.output}. Paste one row per line.
            </p>
            <form
              className="mt-8 space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                if (rowCount < 1) {
                  setError("Add at least one row.");
                  return;
                }
                setError(null);
                setStep("agent");
              }}
            >
              <label className="block text-xs font-medium text-muted">
                Specialization
                <select
                  value={specId}
                  onChange={(e) => {
                    setSpecId(e.target.value);
                    setAgent(null);
                  }}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-panel-soft px-4 py-3 text-sm outline-none focus:border-lavender"
                >
                  {SPECIALIZATIONS.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.title} ({s.category})
                    </option>
                  ))}
                </select>
              </label>
              <textarea
                value={rows}
                onChange={(e) => setRows(e.target.value)}
                rows={7}
                placeholder={spec.input}
                className="w-full rounded-2xl border border-white/10 bg-panel-soft px-4 py-3 text-sm outline-none focus:border-lavender"
              />
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Primary type="submit">Choose an agent →</Primary>
            </form>
          </Panel>
        )}

        {step === "agent" && (
          <Panel key="agent">
            <Eyebrow>Step 2 · Agent</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight">
              {rowCount} rows · {spec.title}
            </h1>
            <p className="mt-3 text-sm text-muted">Pick a listed agent. Hire is SLA-eligible only.</p>
            <div className="mt-6 space-y-3">
              {listed.map((a) => (
                <button
                  key={a.slug}
                  type="button"
                  onClick={() => {
                    setAgent(a);
                    if (!canHire(a)) setMode("run");
                  }}
                  className={`w-full rounded-2xl border px-4 py-4 text-left transition-colors ${
                    agent?.slug === a.slug
                      ? "border-lavender/50 bg-lavender/10"
                      : "border-white/10 bg-panel-soft/60 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold">{a.name}</p>
                    <span className="text-xs text-muted">{a.pricePerRun}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted">{a.tagline}</p>
                </button>
              ))}
              {listed.length === 0 && (
                <p className="text-sm text-muted">No demo agents on this template yet.</p>
              )}
            </div>
            {agent && canHire(agent) && (
              <div className="mt-5 flex gap-2">
                <ModeChip active={mode === "run"} onClick={() => setMode("run")}>
                  Run (credits)
                </ModeChip>
                <ModeChip active={mode === "hire"} onClick={() => setMode("hire")}>
                  Hire {agent.hireMonthly}
                </ModeChip>
              </div>
            )}
            <div className="mt-6">
              <Primary
                type="button"
                disabled={!agent}
                onClick={() => {
                  if (agent && !canHire(agent)) setMode("run");
                  setStep("confirm");
                }}
              >
                Review →
              </Primary>
            </div>
          </Panel>
        )}

        {step === "confirm" && agent && (
          <Panel key="confirm">
            <Eyebrow>Step 3 · Confirm</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight">
              {mode === "hire" ? "Start a retainer" : "Spend run credits"}
            </h1>
            <ul className="mt-6 space-y-2 text-sm text-white/80">
              <li>Agent: {agent.name}</li>
              <li>Rows: {rowCount}</li>
              {mode === "run" ? (
                <>
                  <li>Credits: {credits} (grading included)</li>
                  <li>Builder paid only if the contract holds.</li>
                </>
              ) : (
                <>
                  <li>Retainer: {agent.hireMonthly}</li>
                  <li>Included runs: {agent.includedRuns?.toLocaleString()}</li>
                  <li>Maintenance = keep this contract green. No custom scope.</li>
                </>
              )}
            </ul>
            <div className="mt-8">
              <Primary type="button" onClick={() => setStep("done")}>
                {mode === "hire" ? "Confirm hire →" : "Confirm run →"}
              </Primary>
            </div>
          </Panel>
        )}

        {step === "done" && agent && (
          <Panel key="done">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-brand text-2xl text-white">
              ✓
            </div>
            <h1 className="mt-5 text-center text-3xl font-bold tracking-tight">
              {mode === "hire" ? "Hire recorded" : "Run queued"}
            </h1>
            <p className="mx-auto mt-3 max-w-md text-center text-sm text-muted">
              Demo only — Stripe Connect and oracle payouts are not wired on this screen.{" "}
              <span className="text-white">{agent.name}</span> would{" "}
              {mode === "hire" ? "join as a retained capability" : `grade ${rowCount} rows`} next.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link
                href="/catalog"
                className="rounded-full bg-gradient-brand px-6 py-3 text-sm font-semibold text-white"
              >
                Back to catalog
              </Link>
              <Link
                href="/post/run"
                className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-white/80"
              >
                Another job
              </Link>
            </div>
          </Panel>
        )}
      </AnimatePresence>
    </div>
  );
}

function ModeChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-4 py-2 text-xs font-semibold ${
        active ? "bg-gradient-brand text-white" : "border border-white/15 text-white/80"
      }`}
    >
      {children}
    </button>
  );
}
