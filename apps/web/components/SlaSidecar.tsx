"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const STEPS = [
  "Process contract is versioned (listing template + harness hash).",
  "Builder must submit a trace digest (for example, trace.tools_used).",
  "Merit validates the trace against the allowlist/denylist in the harness.",
  "Undeclared or denied tools fail closed — the row pass alone isn’t enough.",
];

export function SlaSidecarDrawer({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-50 bg-black/60"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          <motion.aside
            className="fixed right-0 top-0 z-50 h-full w-full max-w-md overflow-y-auto border-l border-white/10 bg-background/95 backdrop-blur"
            initial={{ x: 24, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 24, opacity: 0 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
          >
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">
                  SLA sidecar
                </p>
                <h3 className="mt-1 text-lg font-semibold">How SLA-eligible verification works</h3>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-white/10 px-3 py-1.5 text-sm text-white/80 hover:border-lavender/40 hover:text-white"
              >
                Close
              </button>
            </div>

            <div className="px-5 py-5">
              <p className="text-sm text-muted">
                SLA-eligible is Certified + an attested runtime. Builders must run with a declared
                harness, and Merit checks that runtime behavior matches what was declared.
              </p>

              <div className="mt-5 space-y-3">
                {STEPS.map((t) => (
                  <div key={t} className="rounded-2xl border border-white/8 bg-panel-soft/60 p-4">
                    <p className="text-sm text-white/85">{t}</p>
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-2xl border border-lavender/20 bg-lavender/10 p-4">
                <p className="text-sm font-semibold">Two verdicts on Hire</p>
                <p className="mt-2 text-sm text-white/85">
                  1) Oracle pass checks the output against the frozen I/O contract.
                  <br />
                  2) Harness check confirms the process matched the declared rules.
                </p>
              </div>

              <p className="mt-5 text-xs text-muted">
                Sandbox and Certified Runs may stay builder-hosted and black-box. Sidecar
                attestation is scoped to SLA/Hire so companies get transparency only where it
                matters.
              </p>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

/** Self-contained trigger + drawer for catalog / hire surfaces. */
export function SlaLearnLink({
  label = "Learn why SLA is verified →",
  className = "text-xs font-semibold text-lavender hover:text-brand-bright",
}: {
  label?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className={className}>
        {label}
      </button>
      <SlaSidecarDrawer open={open} onClose={() => setOpen(false)} />
    </>
  );
}
