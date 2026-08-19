"use client";

import { motion, useReducedMotion } from "framer-motion";

type MeritLogoProps = {
  size?: number;
  showWordmark?: boolean;
  className?: string;
  animate?: boolean;
};

/** Hexagonal lattice points that silhouette a capital "M" (Milkinside-style dots mark). */
const NODES: { x: number; y: number; r: number }[] = [
  { x: 18, y: 78, r: 2.2 },
  { x: 18, y: 64, r: 2.4 },
  { x: 18, y: 50, r: 2.6 },
  { x: 18, y: 36, r: 2.8 },
  { x: 18, y: 22, r: 3.0 },
  { x: 30, y: 30, r: 2.6 },
  { x: 40, y: 40, r: 2.8 },
  { x: 50, y: 52, r: 3.0 },
  { x: 60, y: 40, r: 2.8 },
  { x: 70, y: 30, r: 2.6 },
  { x: 82, y: 22, r: 3.0 },
  { x: 82, y: 36, r: 2.8 },
  { x: 82, y: 50, r: 2.6 },
  { x: 82, y: 64, r: 2.4 },
  { x: 82, y: 78, r: 2.2 },
  { x: 6, y: 50, r: 1.4 },
  { x: 94, y: 50, r: 1.4 },
  { x: 34, y: 16, r: 1.5 },
  { x: 66, y: 16, r: 1.5 },
  { x: 50, y: 70, r: 1.6 },
  { x: 28, y: 72, r: 1.4 },
  { x: 72, y: 72, r: 1.4 },
];

const EDGES: [number, number][] = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [4, 5],
  [5, 6],
  [6, 7],
  [7, 8],
  [8, 9],
  [9, 10],
  [10, 11],
  [11, 12],
  [12, 13],
  [13, 14],
  [3, 5],
  [5, 7],
  [7, 9],
  [9, 11],
  [2, 6],
  [6, 8],
  [8, 12],
  [15, 2],
  [16, 12],
  [17, 4],
  [18, 10],
  [19, 7],
  [20, 0],
  [21, 14],
];

export function MeritLogo({
  size = 36,
  showWordmark = false,
  className = "",
  animate = true,
}: MeritLogoProps) {
  const reduce = useReducedMotion();
  const live = animate && !reduce;

  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <motion.svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
        className="shrink-0"
        whileHover={live ? { scale: 1.04 } : undefined}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        <defs>
          <radialGradient id="meritGlow" cx="50%" cy="45%" r="55%">
            <stop offset="0%" stopColor="#0179F3" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#003AD4" stopOpacity="0" />
          </radialGradient>
        </defs>

        <motion.circle
          cx="50"
          cy="50"
          r="42"
          fill="url(#meritGlow)"
          initial={live ? { opacity: 0 } : false}
          animate={live ? { opacity: [0.55, 0.95, 0.55] } : { opacity: 0.8 }}
          transition={live ? { duration: 3.2, repeat: Infinity, ease: "easeInOut" } : undefined}
        />

        {EDGES.map(([a, b], i) => {
          const from = NODES[a];
          const to = NODES[b];
          return (
            <motion.line
              key={`e-${i}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke="rgba(255,255,255,0.55)"
              strokeWidth={0.9}
              strokeLinecap="round"
              initial={live ? { pathLength: 0, opacity: 0 } : false}
              animate={
                live
                  ? { pathLength: 1, opacity: [0.35, 0.8, 0.35] }
                  : { pathLength: 1, opacity: 0.55 }
              }
              transition={
                live
                  ? {
                      pathLength: {
                        delay: 0.15 + i * 0.016,
                        duration: 0.4,
                        ease: [0.22, 1, 0.36, 1],
                      },
                      opacity: {
                        duration: 2.8,
                        delay: 0.9 + (i % 7) * 0.08,
                        repeat: Infinity,
                        ease: "easeInOut",
                      },
                    }
                  : undefined
              }
            />
          );
        })}

        {NODES.map((node, i) => (
          <motion.circle
            key={`n-${i}`}
            r={node.r}
            fill={i < 15 ? "#FFFFFF" : "rgba(61,165,255,0.95)"}
            initial={live ? { scale: 0, opacity: 0, cx: 50, cy: 50 } : false}
            animate={
              live
                ? {
                    cx: node.x,
                    cy: node.y,
                    opacity: 1,
                    scale: [1, i < 15 ? 1.16 : 1.08, 1],
                  }
                : { cx: node.x, cy: node.y, opacity: 1, scale: 1 }
            }
            transition={
              live
                ? {
                    cx: { type: "spring", stiffness: 260, damping: 18, delay: 0.04 + i * 0.022 },
                    cy: { type: "spring", stiffness: 260, damping: 18, delay: 0.04 + i * 0.022 },
                    opacity: { delay: 0.04 + i * 0.022, duration: 0.25 },
                    scale: {
                      duration: 2.2,
                      delay: 1.1 + (i % 5) * 0.1,
                      repeat: Infinity,
                      ease: "easeInOut",
                    },
                  }
                : undefined
            }
          />
        ))}

        {live && (
          <motion.polygon
            points="50,14 64,22 64,38 50,46 36,38 36,22"
            fill="none"
            stroke="rgba(61,165,255,0.8)"
            strokeWidth={1}
            initial={{ opacity: 0, y: 0 }}
            animate={{ opacity: [0, 0.95, 0], y: [0, 28, 52] }}
            transition={{ duration: 3.6, repeat: Infinity, ease: "easeInOut", delay: 1.2 }}
          />
        )}
      </motion.svg>

      {showWordmark && (
        <motion.span
          className="text-[15px] font-semibold tracking-[0.04em] text-white"
          initial={live ? { opacity: 0, x: -6 } : false}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: live ? 0.55 : 0, duration: 0.45 }}
        >
          merit
        </motion.span>
      )}
    </span>
  );
}
