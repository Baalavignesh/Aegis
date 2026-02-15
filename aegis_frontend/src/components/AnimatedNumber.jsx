import { useState, useEffect, useRef } from 'react';

/** Count-up animation when value changes. */
export default function AnimatedNumber({ value, className = '', duration = 0.35 }) {
  const num = typeof value === 'number' ? value : parseInt(String(value), 10) || 0;
  const [display, setDisplay] = useState(num);
  const rafRef = useRef(null);

  useEffect(() => {
    const start = display;
    const end = num;
    if (start === end) return;
    const startTime = performance.now();
    const tick = (now) => {
      const t = Math.min((now - startTime) / (duration * 1000), 1);
      const eased = 1 - (1 - t) ** 2;
      setDisplay(Math.round(start + (end - start) * eased));
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [num]);

  return <span className={className}>{display}</span>;
}
