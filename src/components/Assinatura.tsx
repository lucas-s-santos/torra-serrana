"use client";

import { useRef } from "react";
import { Grao } from "@/components/Logo";
import { useScrollVar } from "@/lib/useScrollProgress";

/**
 * A marca de ponta a ponta no pé da página. Sobe de trás da borda conforme a página acaba,
 * e a crista da serra se desenha no grão junto. Largura medida no Fraunces: grão 0.92em +
 * vão 0.16em + "Torra Serrana" = 5.93em, com o opsz preso no 144 (solto, no celular o opsz menor
 * alargava as letras e a marca vazava). Dividir a largura livre por 6.2 deixa ~4% de folga.
 */
export function Assinatura() {
  const ref = useRef<HTMLDivElement>(null);
  useScrollVar(ref, { start: "top bottom", end: "bottom bottom" });

  return (
    <div ref={ref} aria-hidden className="overflow-hidden px-6 [--p:0] md:px-12">
      <p
        className="flex items-center justify-center gap-[0.16em] pb-[0.1em] font-serif text-[calc((100vw-3rem)/6.2)] [font-variation-settings:'opsz'_144] leading-[0.95] tracking-[-0.045em] whitespace-nowrap text-cereja md:text-[calc((100vw-6rem)/6.2)]"
        style={{ transform: "translate3d(0, calc((1 - var(--p)) * 55%), 0)" }}
      >
        <Grao
          id="grao-rodape"
          className="size-[0.92em] shrink-0"
          crista={{ strokeDasharray: 1, strokeDashoffset: "calc(1 - clamp(0, calc((var(--p) - 0.3) / 0.7), 1))" }}
        />
        Torra Serrana
      </p>
    </div>
  );
}
