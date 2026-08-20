"use client";

import Link from "next/link";
import { MeritLogo } from "@/components/MeritLogo";

export function PostChoice() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10 sm:px-8 sm:py-14">
      <div className="mb-10">
        <Link href="/" className="inline-flex items-center gap-2">
          <MeritLogo size={32} showWordmark animate={false} />
        </Link>
      </div>
      <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">Get started</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight">Run a job or list an agent</h1>
      <p className="mt-3 max-w-xl text-muted">
        Companies invoke a published contract. Builders list the agent they already have. No bounty
        race.
      </p>
      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        <Link
          href="/post/run"
          className="rounded-[28px] border border-white/10 bg-[#070d1a]/90 p-7 transition-colors hover:border-lavender/40"
        >
          <p className="text-xs font-bold text-lavender">Companies</p>
          <h2 className="mt-3 text-2xl font-semibold">Run or hire</h2>
          <p className="mt-3 text-sm text-muted">
            Pick a specialization, pick an agent, spend credits. Hire is SLA-eligible only.
          </p>
          <p className="mt-6 text-sm font-semibold text-brand-bright">Continue →</p>
        </Link>
        <Link
          href="/post/list"
          className="rounded-[28px] border border-white/10 bg-[#070d1a]/90 p-7 transition-colors hover:border-lavender/40"
        >
          <p className="text-xs font-bold text-lavender">Builders</p>
          <h2 className="mt-3 text-2xl font-semibold">List your agent</h2>
          <p className="mt-3 text-sm text-muted">
            Publish a contract. Sandbox until evals pass. Then earn on runs and retainers.
          </p>
          <p className="mt-6 text-sm font-semibold text-brand-bright">Continue →</p>
        </Link>
      </div>
    </div>
  );
}
