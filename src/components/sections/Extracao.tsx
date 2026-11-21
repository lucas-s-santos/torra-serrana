"use client";

import { useRef } from "react";
import { ScrubVideo } from "@/components/ScrubVideo";
import { EXTRACAO } from "@/lib/site";
import { segment, useScrollProgress } from "@/lib/useScrollProgress";
import { Revela } from "@/components/Revela";

// inteiro e decimal em spans separados: no mono a vírgula ocupa uma célula inteira e abriria um buraco
const partes = (v: number, casas: number) => {
  const [int, dec = ""] = v.toFixed(casas).split(".");
  return [int, dec] as const;
};

export function Extracao() {
  const ref = useRef<HTMLElement>(null);
  const inteiros = useRef<(HTMLSpanElement | null)[]>([]);
  const decimais = useRef<(HTMLSpanElement | null)[]>([]);
  const linha = useRef<HTMLDivElement>(null);

  // contadores escrevem direto no DOM: nada de re-render a cada frame de scroll
  useScrollProgress(ref, (p) => {
    EXTRACAO.forEach((d, i) => {
      const [int, dec] = partes(d.de + (d.ate - d.de) * segment(p, d.janela[0], d.janela[1]), d.casas);
      if (inteiros.current[i]) inteiros.current[i].textContent = int;
      if (decimais.current[i]) decimais.current[i].textContent = dec;
    });
    if (linha.current) linha.current.style.transform = `scaleX(${p})`;
  });

  return (
    <section ref={ref} aria-label="Extração" className="relative h-[320svh] bg-cafe motion-reduce:h-auto">
      <div className="sticky top-0 flex h-svh items-center overflow-hidden motion-reduce:static motion-reduce:h-auto motion-reduce:py-28">
        <div className="shell grid items-center gap-6 pt-16 md:grid-cols-12 md:gap-10 md:pt-0">
          <div className="relative h-[34svh] overflow-hidden md:col-span-5 md:h-[78svh]">
            <ScrubVideo src="/video/extracao.mp4" srcPequeno="/video/extracao-sm.mp4" trigger={ref} className="absolute inset-0 size-full object-cover" />
          </div>

          <div className="md:col-span-6 md:col-start-7">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">03 — Extração</p>
            <Revela className="mt-4 max-w-[16ch] font-serif text-[clamp(2rem,4.5vw,4.25rem)] leading-[0.98] tracking-[-0.025em] md:mt-6">
              Medimos tudo. Depois, <em className="italic">provamos.</em>
            </Revela>

            <dl className="mt-6 grid grid-cols-2 gap-x-6 border-t border-creme/12 md:mt-12 md:block">
              {EXTRACAO.map((d, i) => (
                <div
                  key={d.label}
                  className="flex flex-col gap-1 border-b border-creme/12 py-3 md:flex-row md:items-baseline md:justify-between md:py-4"
                >
                  <dt className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">{d.label}</dt>
                  <dd className="font-mono text-[clamp(1.75rem,4vw,3.25rem)] leading-none tabular-nums text-caramelo">
                    <span
                      ref={(el) => {
                        inteiros.current[i] = el;
                      }}
                    >
                      {partes(d.de, d.casas)[0]}
                    </span>
                    <span className="-mx-[0.22em]">,</span>
                    <span
                      ref={(el) => {
                        decimais.current[i] = el;
                      }}
                    >
                      {partes(d.de, d.casas)[1]}
                    </span>
                    <span className="ml-2 text-[0.42em] text-creme/60">{d.unidade}</span>
                  </dd>
                </div>
              ))}
              <div className="flex flex-col gap-1 py-3 md:flex-row md:items-baseline md:justify-between md:py-4">
                <dt className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">Proporção</dt>
                <dd className="font-mono text-[clamp(1.75rem,4vw,3.25rem)] leading-none tabular-nums text-creme">1:2</dd>
              </div>
            </dl>

            <div className="mt-4 hidden h-px bg-creme/12 md:block">
              <div ref={linha} className="h-full origin-left scale-x-0 bg-caramelo" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
