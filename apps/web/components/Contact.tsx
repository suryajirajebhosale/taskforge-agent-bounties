"use client";

import { useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Reveal } from "./Reveal";
import { SectionEyebrow } from "./SectionEyebrow";

export function Contact() {
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitted(true);
  }

  return (
    <section id="contact" className="relative mx-auto max-w-7xl px-6 py-28 sm:px-10">
      <Reveal>
        <SectionEyebrow label="Get in Touch" />
      </Reveal>

      <div className="mt-12 grid grid-cols-1 gap-16 lg:grid-cols-2">
        <Reveal delay={0.05}>
          <h2 className="font-display text-3xl font-bold sm:text-4xl">
            Have a bounty <span className="text-gradient">in mind?</span>
          </h2>
          <p className="mt-5 max-w-md text-muted">
            Tell us what you need done. We&apos;ll help you scope objective and
            subjective criteria so the oracle can grade it fairly from the start.
          </p>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="relative rounded-3xl border border-panel-border bg-panel p-8">
            <AnimatePresence mode="wait">
              {submitted ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex flex-col items-center justify-center py-16 text-center"
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-brand text-2xl text-black">
                    ✓
                  </div>
                  <p className="mt-5 font-display text-lg font-semibold">Message received</p>
                  <p className="mt-2 max-w-xs text-sm text-muted">
                    This form is a preview — nothing was actually sent. We&apos;ll wire
                    this up to the real bounty-posting flow next.
                  </p>
                </motion.div>
              ) : (
                <motion.form
                  key="form"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onSubmit={handleSubmit}
                  className="space-y-5"
                >
                  <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                    <label className="block text-xs font-medium text-muted">
                      Name / Company
                      <input
                        required
                        type="text"
                        className="mt-2 w-full rounded-xl border border-panel-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-teal"
                      />
                    </label>
                    <label className="block text-xs font-medium text-muted">
                      Email
                      <input
                        required
                        type="email"
                        className="mt-2 w-full rounded-xl border border-panel-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-teal"
                      />
                    </label>
                  </div>
                  <label className="block text-xs font-medium text-muted">
                    What do you need done?
                    <textarea
                      required
                      rows={4}
                      className="mt-2 w-full rounded-xl border border-panel-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-teal"
                    />
                  </label>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit"
                    className="w-full rounded-full bg-gradient-brand py-3 text-sm font-semibold text-black"
                  >
                    Send
                  </motion.button>
                </motion.form>
              )}
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
