"use client";

import Link from "next/link";
import { Reveal } from "./Reveal";

export function Contact() {
  return (
    <section id="contact" className="relative mx-auto max-w-7xl px-6 py-24 sm:px-10 sm:py-28">
      <div className="glass relative overflow-hidden rounded-[32px] px-6 py-12 sm:px-12 sm:py-16">
        <div className="pointer-events-none absolute -left-20 top-0 h-56 w-56 rounded-full bg-lavender/25 blur-3xl" />
        <div className="pointer-events-none absolute -right-16 bottom-0 h-48 w-48 rounded-full bg-midnight blur-3xl" />

        <div className="relative mx-auto max-w-2xl text-center">
          <Reveal>
            <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">
              Get started
            </p>
            <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
              Have a bounty <span className="text-gradient">in mind?</span>
            </h2>
            <p className="mx-auto mt-5 max-w-md text-muted">
              Sign up, describe the outcome, and Merit&apos;s AI will clarify requirements into an
              approvable task report — before any escrow moves.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/post"
                className="rounded-full bg-gradient-brand px-7 py-3 text-sm font-semibold text-white shadow-[0_12px_40px_rgba(1,121,243,0.4)] transition-transform hover:scale-[1.03]"
              >
                Post a bounty →
              </Link>
              <a
                href="#how-it-works"
                className="rounded-full border border-white/15 px-7 py-3 text-sm font-semibold text-white/85 hover:border-lavender/40"
              >
                See how it works
              </a>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
