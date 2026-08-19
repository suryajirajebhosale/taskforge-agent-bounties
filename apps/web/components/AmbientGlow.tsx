"use client";

import { useMotionValue, useMotionTemplate, motion } from "framer-motion";
import type { ReactNode, MouseEvent } from "react";

export function AmbientGlow({ children }: { children: ReactNode }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function onMove(e: MouseEvent<HTMLDivElement>) {
    const { left, top } = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - left);
    mouseY.set(e.clientY - top);
  }

  const spotlight = useMotionTemplate`radial-gradient(620px circle at ${mouseX}px ${mouseY}px, rgba(1,121,243,0.18), transparent 45%)`;

  return (
    <div className="relative isolate min-h-screen overflow-hidden" onMouseMove={onMove}>
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-70" />
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[720px] -translate-x-1/2 rounded-full bg-midnight/80 blur-[120px] animate-pulse-soft" />
      <div className="pointer-events-none absolute bottom-0 left-1/2 h-[420px] w-[680px] -translate-x-1/2 rounded-full bg-lavender/20 blur-[140px]" />
      <motion.div className="pointer-events-none absolute inset-0 z-0" style={{ background: spotlight }} />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
