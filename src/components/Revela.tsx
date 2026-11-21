"use client";

import { createElement, useEffect, useRef, type ReactNode } from "react";
import { gsap, loadSplitText } from "@/lib/gsap";
import type { SplitText } from "gsap/SplitText";
import { prefersReducedMotion } from "@/lib/useReducedMotion";

type Props = {
  as?: "h2" | "h3" | "p" | "blockquote";
  className?: string;
  children: ReactNode;
  /** atraso em segundos (ex.: parágrafo depois do título) */
  delay?: number;
};

/**
 * Texto que entra linha a linha, subindo de dentro de uma máscara, quando chega na tela (uma vez).
 * Só divide as linhas quando o texto se aproxima da tela: dividir tudo no load forçava layout
 * em série e pesava no TBT do mobile.
 */
export function Revela({ as = "h2", className, children, delay = 0 }: Props) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current!;
    if (prefersReducedMotion()) return;
    let split: SplitText | undefined;
    let tween: gsap.core.Tween | undefined;

    // 1) perto da tela: divide e esconde as linhas (ainda fora de vista)
    let vivo = true;
    const perto = new IntersectionObserver(
      async ([e]) => {
        if (!e.isIntersecting) return;
        perto.disconnect();
        const SplitText = await loadSplitText();
        if (!vivo) return;
        split = SplitText.create(el, {
          type: "lines",
          mask: "lines",
          linesClass: "linha",
          aria: "none", // só linhas: o texto continua contínuo pro leitor de tela
          autoSplit: true,
          onSplit: (self) =>
            (tween = gsap.from(self.lines, { yPercent: 110, duration: 1.3, ease: "expo.out", stagger: 0.09, delay, paused: true })),
        });
        visivel.observe(el);
      },
      { rootMargin: "0px 0px 40% 0px" },
    );
    // 2) entrou de fato (12% acima da borda de baixo): toca
    const visivel = new IntersectionObserver(
      ([e]) => {
        if (!e.isIntersecting) return;
        visivel.disconnect();
        tween?.play();
      },
      { rootMargin: "0px 0px -12% 0px" },
    );
    perto.observe(el);

    return () => {
      vivo = false;
      perto.disconnect();
      visivel.disconnect();
      split?.revert();
    };
  }, [delay]);

  return createElement(as, { ref, className }, children);
}
