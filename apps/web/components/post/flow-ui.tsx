"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { MeritLogo } from "@/components/MeritLogo";
import { clearSession, type MeritSession } from "@/lib/session";

export function FlowHeader({
  session,
  onSignOut,
}: {
  session: MeritSession | null;
  onSignOut: () => void;
}) {
  return (
    <div className="mb-10 flex items-center justify-between gap-4">
      <Link href="/" className="inline-flex items-center gap-2">
        <MeritLogo size={32} showWordmark animate={false} />
      </Link>
      {session && (
        <div className="flex items-center gap-3 text-xs text-muted">
          <span className="hidden sm:inline">{session.email}</span>
          <button
            type="button"
            onClick={() => {
              clearSession();
              onSignOut();
            }}
            className="rounded-full border border-white/10 px-3 py-1.5 hover:border-lavender/40 hover:text-white"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export function Panel({ children }: { children: React.ReactNode }) {
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

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold tracking-[0.28em] text-lavender uppercase">{children}</p>
  );
}

export function Field({
  label,
  name,
  type,
  required,
  minLength,
  defaultValue,
  placeholder,
}: {
  label: string;
  name: string;
  type: string;
  required?: boolean;
  minLength?: number;
  defaultValue?: string;
  placeholder?: string;
}) {
  return (
    <label className="block text-xs font-medium text-muted">
      {label}
      <input
        name={name}
        type={type}
        required={required}
        minLength={minLength}
        defaultValue={defaultValue}
        placeholder={placeholder}
        className="mt-2 w-full rounded-xl border border-white/10 bg-panel-soft px-4 py-3 text-sm text-foreground outline-none focus:border-lavender"
      />
    </label>
  );
}

export function Primary({
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

export function SignupForm({
  error,
  onSubmit,
}: {
  error: string | null;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <Panel>
      <Eyebrow>Sign up required</Eyebrow>
      <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Create your Merit account</h1>
      <p className="mt-3 text-sm text-muted">Demo auth for now (saved locally).</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <Field label="Name" name="name" type="text" required />
        <Field label="Work email" name="email" type="email" required />
        <Field label="Password" name="password" type="password" required minLength={6} />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <Primary type="submit">Continue →</Primary>
      </form>
    </Panel>
  );
}

export function handleSignup(
  e: React.FormEvent<HTMLFormElement>,
  save: (session: { name: string; email: string; createdAt: string }) => void,
): string | null {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  const name = String(fd.get("name") ?? "").trim();
  const email = String(fd.get("email") ?? "").trim();
  const password = String(fd.get("password") ?? "");
  if (!name || !email || password.length < 6) {
    return "Use a name, email, and password (6+ characters).";
  }
  save({ name, email, createdAt: new Date().toISOString() });
  return null;
}
