import { motion } from "framer-motion";

export default function Logo({ size = 30, animated = false }: { size?: number; animated?: boolean }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="shieldGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#1B4068" />
          <stop offset="100%" stopColor="#0B1F33" />
        </linearGradient>
      </defs>
      <motion.path
        d="M16 2 L28 7 V16 C28 23 22 28 16 30 C10 28 4 23 4 16 V7 Z"
        fill="url(#shieldGrad)"
        initial={animated ? { pathLength: 0, opacity: 0 } : false}
        animate={animated ? { pathLength: 1, opacity: 1 } : {}}
        transition={{ duration: 1, ease: "easeInOut" }}
      />
      {/* signal tick */}
      <path
        d="M11 16 l3.5 3.5 L21 12.5"
        fill="none"
        stroke="#22D3EE"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
