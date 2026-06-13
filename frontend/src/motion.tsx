import { useEffect, useRef, useState } from "react";
import { motion, useInView, type Variants } from "framer-motion";
import type { ReactNode } from "react";

// Premium easing — same curve Linear/Vercel-style UIs use for confident motion.
export const EASE = [0.22, 1, 0.36, 1] as const;

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: EASE } },
};

export const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.04 } },
};

/** Page-level entrance: stagger any direct <motion> children that use `fadeUp`. */
export function PageMotion({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className={className}>
      {children}
    </motion.div>
  );
}

/** A single item that fades+rises into place; composes inside PageMotion. */
export function Item({
  children,
  className,
  as = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "li" | "tr";
}) {
  const Comp = motion[as] as typeof motion.div;
  return (
    <Comp variants={fadeUp} className={className}>
      {children}
    </Comp>
  );
}

/** Reveal on scroll into view — used for dashboard sections. */
export function Reveal({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 18 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.55, ease: EASE, delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * Animated number counter. Eases toward `value`, formatting each frame.
 * Looks hand-built (not a default chart label) and adds life to the dashboard.
 */
export function CountUp({
  value,
  duration = 1.1,
  decimals = 0,
  prefix = "",
  suffix = "",
}: {
  value: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
}) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    let raf = 0;
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / (duration * 1000));
      // easeOutExpo
      const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      setDisplay(from + (value - from) * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration]);

  return (
    <span ref={ref} className="tnum">
      {prefix}
      {display.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
}
