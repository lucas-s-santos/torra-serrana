"use client";

import { useEffect, useRef, type CSSProperties, type RefObject } from "react";
import { ScrollTrigger } from "@/lib/gsap";
import { prefersReducedMotion } from "@/lib/useReducedMotion";

type Opts = { start?: string; end?: string };

/**
 * Progresso 0→1 do elemento no scroll (sem tween: o Lenis já suaviza).
 * Com reduced-motion entrega 1 uma vez: estado final, estático.
 */
export function useScrollProgress(
  ref: RefObject<HTMLElement | null>,
  onProgress: (p: number) => void,
  { start = "top top", end = "bottom bottom" }: Opts = {},
) {
  const cb = useRef(onProgress);
  useEffect(() => {
    cb.current = onProgress;
  });

  // useEffect (não layout): o ref pode ser de um ancestral (ex.: ScrubVideo), que só é ligado
  // depois dos layout effects dos filhos
  useEffect(() => {
    if (prefersReducedMotion()) return cb.current(1);
    const st = ScrollTrigger.create({
      trigger: ref.current,
      start,
      end,
      onUpdate: (self) => cb.current(self.progress),
      onRefresh: (self) => cb.current(self.progress),
    });
    return () => st.kill();
  }, [ref, start, end]);
}

/** Mesmo progresso, publicado como CSS var no elemento (o CSS faz o resto com calc()). */
export function useScrollVar(ref: RefObject<HTMLElement | null>, opts: Opts & { name?: string } = {}) {
  const { name = "--p", ...range } = opts;
  useScrollProgress(ref, (p) => ref.current?.style.setProperty(name, p.toFixed(4)), range);
}

/** Recorta [a, b] do progresso e normaliza pra 0→1. */
export const segment = (p: number, a: number, b: number) => Math.min(1, Math.max(0, (p - a) / (b - a)));

/** Entrada (fade + sobe) dirigida pela CSS var --p do ancestral, no trecho [a, b]. */
export function reveal(a: number, b: number, dist = 28): CSSProperties {
  const t = `clamp(0, calc((var(--p) - ${a}) / ${b - a}), 1)`;
  return { opacity: t, transform: `translate3d(0, calc((1 - ${t}) * ${dist}px), 0)` };
}
