"use client";

import { useRef } from "react";
import { useScrollVar } from "@/lib/useScrollProgress";
import { Revela } from "@/components/Revela";

// [grão, x%, y%, largura (vw), camada, rotação°, onde]. Camada 0 = fundo (pequeno, desfocado, lento) … 2 = frente (grande, rápido).
// "onde": os grãos ficam fora do galho da foto, que no desktop ocupa o terço esquerdo e no celular a faixa de cima
const GRAOS: [number, number, number, number, 0 | 1 | 2, number, "md" | "sm" | "ambos"][] = [
  [5, 74, 14, 4.5, 0, -35, "md"],
  [4, 66, 84, 5.5, 0, 60, "ambos"],
  [1, 44, 90, 4.5, 0, -10, "ambos"],
  [3, 86, 30, 9, 1, 15, "md"],
  [2, 58, 7, 7, 1, 110, "md"],
  [6, 22, 80, 9, 1, -25, "sm"],
  [1, 93, 62, 20, 2, -30, "ambos"], // camada da frente: na lateral, na altura da frase, sangrando pela borda
  [5, 7, 72, 16, 2, 40, "sm"],
];
const ONDE = { md: "max-md:hidden", sm: "md:hidden", ambos: "" };
const CAMADA = [
  { vel: 12, cls: "opacity-35 blur-[3px]" },
  { vel: 32, cls: "opacity-85" },
  { vel: 70, cls: "drop-shadow-[0_30px_30px_rgba(0,0,0,0.45)]" },
];

export function Citacao() {
  const ref = useRef<HTMLElement>(null);
  useScrollVar(ref, { start: "top bottom", end: "bottom top" });

  return (
    <section ref={ref} aria-label="Citação" className="relative overflow-hidden bg-cafe py-[32svh] [--p:0.5]">
      {/* pé de café (Flow) saindo do escuro; parallax leve, e as bordas somem no café das seções vizinhas */}
      <picture>
        <source
          media="(min-width: 768px)"
          srcSet="/img/cerejas/cerejas-1280.webp 1280w, /img/cerejas/cerejas-1920.webp 1920w"
          sizes="100vw"
          width={1920}
          height={1072}
        />
        <img
          src="/img/cerejas/cerejas-alta-1080.webp"
          alt=""
          aria-hidden
          loading="lazy"
          decoding="async"
          width={1080}
          height={1936}
          className="pointer-events-none absolute inset-x-0 -top-[6svh] h-auto w-full"
          style={{ translate: "0 calc((0.5 - var(--p)) * 12svh)" }}
        />
      </picture>
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,var(--color-cafe),transparent_16%,transparent_70%,var(--color-cafe))]" />

      {GRAOS.map(([g, x, y, w, c, rot, onde], i) => (
        <img
          key={i}
          src={`/img/graos/solto-${g}.webp`}
          alt=""
          aria-hidden
          loading="lazy"
          decoding="async"
          width={600}
          height={600}
          className={`pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 ${CAMADA[c].cls} ${ONDE[onde]} ${c === 2 ? "z-20" : ""}`}
          style={{
            left: `${x}%`,
            top: `${y}%`,
            width: `${w}vw`,
            minWidth: `${w * 10}px`, // no mobile o vw fica minúsculo (e o grão ocupa ~45% do PNG)
            translate: `0 calc((0.5 - var(--p)) * ${CAMADA[c].vel}svh)`,
            rotate: `calc(${rot}deg + (var(--p) - 0.5) * ${c * 25}deg)`,
          }}
        />
      ))}

      {/* desktop: a frase vai pra direita, longe do galho */}
      <figure className="shell relative z-10 text-center md:pl-[42%] md:text-left">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">06 — Prova</p>
        <Revela as="blockquote" className="mx-auto mt-10 max-w-[17ch] font-serif text-[clamp(2.5rem,5.4vw,5.75rem)] leading-[0.98] tracking-[-0.03em] text-balance md:mx-0 md:max-w-[13ch]">
          O primeiro gole conta a história <em className="italic text-caramelo">toda.</em>
        </Revela>
      </figure>
    </section>
  );
}
