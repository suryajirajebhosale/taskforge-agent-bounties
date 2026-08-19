"use client";

import { useInView, useMotionValue, useSpring } from "framer-motion";
import { useEffect, useRef, useState } from "react";

export function StatCounter({
  target,
  prefix = "",
  suffix = "",
  decimals = 0,
  label,
}: {
  target: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  label: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const motionValue = useMotionValue(0);
  const spring = useSpring(motionValue, { stiffness: 60, damping: 20 });
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    if (isInView) motionValue.set(target);
  }, [isInView, motionValue, target]);

  useEffect(() => {
    return spring.on("change", (v) => {
      setDisplay(v.toFixed(decimals));
    });
  }, [spring, decimals]);

  return (
    <div ref={ref} className="text-center">
      <div className="font-display text-2xl sm:text-3xl font-bold text-gradient tabular-nums">
        {prefix}
        {display}
        {suffix}
      </div>
      <div className="mt-1 text-xs sm:text-sm text-muted">{label}</div>
    </div>
  );
}
