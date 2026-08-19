"use client";

import { motion, useMotionValue, useSpring } from "framer-motion";
import type { PointerEvent } from "react";

const FACE_GRADIENTS = [
  "linear-gradient(135deg, var(--teal), var(--cyan))",
  "linear-gradient(135deg, var(--cyan), var(--violet))",
  "linear-gradient(135deg, var(--violet), var(--magenta))",
  "linear-gradient(135deg, var(--magenta), var(--violet))",
  "linear-gradient(135deg, var(--teal), var(--violet))",
  "linear-gradient(135deg, var(--cyan), var(--teal))",
];

function Face({ transform, gradient }: { transform: string; gradient: string }) {
  return (
    <div
      className="absolute inset-0 rounded-lg backface-hidden"
      style={{
        transform,
        backgroundImage: gradient,
        opacity: 0.95,
        border: "1px solid color-mix(in srgb, white 40%, transparent)",
        boxShadow:
          "inset 0 0 50px color-mix(in srgb, white 16%, transparent), 0 0 60px -10px color-mix(in srgb, var(--violet) 60%, transparent)",
      }}
    />
  );
}

export function Cube3D({ size = 220, className }: { size?: number; className?: string }) {
  const half = size / 2;
  const rotateX = useMotionValue(0);
  const rotateY = useMotionValue(0);
  const springX = useSpring(rotateX, { stiffness: 60, damping: 14 });
  const springY = useSpring(rotateY, { stiffness: 60, damping: 14 });

  function handlePointerMove(e: PointerEvent<HTMLDivElement>) {
    const bounds = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - bounds.left) / bounds.width - 0.5;
    const py = (e.clientY - bounds.top) / bounds.height - 0.5;
    rotateY.set(px * 30);
    rotateX.set(py * -30);
  }

  function handlePointerLeave() {
    rotateX.set(0);
    rotateY.set(0);
  }

  const faces = [
    `rotateY(0deg) translateZ(${half}px)`,
    `rotateY(90deg) translateZ(${half}px)`,
    `rotateY(180deg) translateZ(${half}px)`,
    `rotateY(-90deg) translateZ(${half}px)`,
    `rotateX(90deg) translateZ(${half}px)`,
    `rotateX(-90deg) translateZ(${half}px)`,
  ];

  return (
    <div
      className={`perspective-1000 ${className ?? ""}`}
      style={{ width: size, height: size }}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <motion.div className="preserve-3d h-full w-full" style={{ rotateX: springX, rotateY: springY }}>
        <div className="preserve-3d h-full w-full animate-spin3d" style={{ width: size, height: size }}>
          {faces.map((transform, i) => (
            <Face key={i} transform={transform} gradient={FACE_GRADIENTS[i]} />
          ))}
        </div>
      </motion.div>
    </div>
  );
}
