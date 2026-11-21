"use client";

import { useRef } from "react";
import { reveal, useScrollVar } from "@/lib/useScrollProgress";

// de 0 a 0.45 do scroll a foto sai de um quadro no creme e toma a tela
const abre = "clamp(0, calc(var(--p) / 0.45), 1)";

/** Respiro entre Origem e Extração: a casa na encosta, com a serra na neblina. */
export function Serra() {
  const ref = useRef<HTMLElement>(null);
  useScrollVar(ref);

  return (
    <section ref={ref} aria-label="A serra" className="relative h-[220svh] bg-creme [--p:0] motion-reduce:h-svh">
      <div
        className="sticky top-0 h-svh overflow-hidden"
        style={{ clipPath: `inset(calc((1 - ${abre}) * 12%) calc((1 - ${abre}) * 8%))` }}
      >
        {/* desktop: faixa larga recortada (céu, neblina e a casa); celular: a foto 3:4 inteira */}
        <picture>
          <source media="(min-width: 768px)" srcSet="/img/serra/serra-larga.webp" />
          <img
            src="/img/serra/serra-1200.webp"
            alt="A casa caiada na encosta, entre pés de café e araucárias, com a serra coberta de neblina ao amanhecer."
            loading="lazy"
            decoding="async"
            width={1200}
            height={1607}
            className="absolute inset-0 size-full object-cover object-[60%_50%]"
            style={{ scale: "calc(1.15 - var(--p) * 0.15)" }}
          />
        </picture>
        {/* sombra no topo: o header (mix-blend-difference) some no céu claro sem ela */}
        <div
          className="absolute inset-x-0 top-0 h-48 bg-[linear-gradient(to_bottom,color-mix(in_srgb,var(--color-cafe)_80%,transparent),transparent)]"
          style={{ opacity: abre }}
        />
        {/* legibilidade e emenda com o café da Extração logo abaixo */}
        <div
          className="absolute inset-0 bg-[linear-gradient(to_top,var(--color-cafe)_0%,color-mix(in_srgb,var(--color-cafe)_55%,transparent)_30%,transparent_60%)]"
          style={{ opacity: "clamp(0, calc((var(--p) - 0.25) / 0.5), 1)" }}
        />
        <div className="absolute inset-x-0 bottom-0 pb-10 md:pb-16">
          <div className="shell flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <h2 className="max-w-[13ch] font-serif text-title text-creme" style={reveal(0.45, 0.7)}>
              A serra acorda antes da <em className="italic">gente.</em>
            </h2>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/70" style={reveal(0.55, 0.75, 12)}>
              Carmo de Minas · 1.100 m · 6h
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
