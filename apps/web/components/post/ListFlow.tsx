"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AnimatePresence } from "framer-motion";
import Link from "next/link";
import { SPECIALIZATIONS } from "@/lib/catalog";
import { getSession, saveSession, type MeritSession } from "@/lib/session";
import { Eyebrow, Field, FlowHeader, Panel, Primary, SignupForm, handleSignup } from "./flow-ui";

type Step = "signup" | "form" | "done";

export function ListFlow() {
  const [session, setSession] = useState<MeritSession | null>(null);
  const [step, setStep] = useState<Step>("signup");
  const [error, setError] = useState<string | null>(null);
  const [agentName, setAgentName] = useState("");
  const [specId, setSpecId] = useState<string>(SPECIALIZATIONS[0].id);
  const spec = useMemo(
    () => SPECIALIZATIONS.find((s) => s.id === specId) ?? SPECIALIZATIONS[0],
    [specId],
  );

  useEffect(() => {
    const existing = getSession();
    if (existing) {
      setSession(existing);
      setStep("form");
    }
  }, []);

  function onSignup(e: FormEvent<HTMLFormElement>) {
    const err = handleSignup(e, (next) => {
      saveSession(next);
      setSession(next);
      setStep("form");
    });
    setError(err);
  }

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const name = String(fd.get("agentName") ?? "").trim();
    const webhook = String(fd.get("webhook") ?? "").trim();
    if (!name || !webhook) {
      setError("Name and webhook URL are required.");
      return;
    }
    setAgentName(name);
    setError(null);
    setStep("done");
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

        {step === "form" && (
          <Panel key="form">
            <Eyebrow>Publish contract</Eyebrow>
            <h1 className="mt-3 text-3xl font-bold tracking-tight">List your agent</h1>
            <p className="mt-3 text-sm text-muted">
              Pick one Merit specialization. You cannot strip required fields. Extra fields are
              ungraded. Sandbox until that template&apos;s golden set passes. Hire needs Certified,
              an attested runtime, and the SLA checklist.
            </p>
            <form onSubmit={onSubmit} className="mt-8 space-y-4">
              <Field label="Agent name" name="agentName" type="text" required placeholder="Ledger" />
              <label className="block text-xs font-medium text-muted">
                Specialization
                <select
                  name="templateId"
                  value={specId}
                  onChange={(e) => setSpecId(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-panel-soft px-4 py-3 text-sm outline-none focus:border-lavender"
                >
                  {SPECIALIZATIONS.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.title} ({s.category})
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-xs font-medium text-muted">
                Official contract (locked)
                <textarea
                  name="schema"
                  readOnly
                  rows={4}
                  value={`In: ${spec.input}\nOut: ${spec.output}`}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-muted"
                />
              </label>
              <Field
                label="Optional extras (ungraded)"
                name="extras"
                type="text"
                placeholder="linkedin_url"
              />
              <Field label="Price per run (credits / row)" name="price" type="text" required defaultValue="12" />
              <Field label="Webhook or repo URL" name="webhook" type="url" required placeholder="https://" />
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Primary type="submit">Submit to Sandbox →</Primary>
            </form>
          </Panel>
        )}

        {step === "done" && (
          <Panel key="done">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-brand text-2xl text-white">
              ✓
            </div>
            <h1 className="mt-5 text-center text-3xl font-bold tracking-tight">In Sandbox</h1>
            <p className="mx-auto mt-3 max-w-md text-center text-sm text-muted">
              <span className="text-white">{agentName}</span> is queued for the {spec.title} eval
              set. Demo only — no live listing yet.
            </p>
            <div className="mt-8 flex justify-center">
              <Link
                href="/builders"
                className="rounded-full bg-gradient-brand px-6 py-3 text-sm font-semibold text-white"
              >
                Back to builders
              </Link>
            </div>
          </Panel>
        )}
      </AnimatePresence>
    </div>
  );
}
