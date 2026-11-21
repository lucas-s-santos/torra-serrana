"use client";

import { useRef } from "react";
import { ScrubVideo } from "@/components/ScrubVideo";
import { reveal, useScrollVar } from "@/lib/useScrollProgress";

const titulo = "font-serif text-[clamp(2.5rem,4.2vw,4.5rem)] leading-[0.95] tracking-[-0.025em]";

export function Leite() {
  const ref = useRef<HTMLElement>(null);
  useScrollVar(ref);

  return (
    <section ref={ref} aria-label="Leite" className="relative h-[300svh] bg-cafe [--p:0] motion-reduce:h-svh">
      <div className="sticky top-0 h-svh overflow-hidden">
        {/* celular: título, vídeo, legenda empilhados; desktop: o vídeo no meio, uma frase de cada lado */}
        <div className="shell grid h-full grid-rows-[auto_minmax(0,1fr)_auto] items-center gap-6 pt-24 pb-10 lg:grid-cols-12 lg:grid-rows-1 lg:gap-10 lg:py-16">
          <h2 className={`${titulo} lg:col-span-3 lg:self-start lg:pt-8`} style={reveal(0.05, 0.3)}>
            Leite a <span className="whitespace-nowrap text-caramelo">62 °C.</span>
          </h2>

          {/* o quadro abre de dentro pra fora enquanto o leite começa a cair */}
          <div
            className="relative mx-auto aspect-[3/4] h-full max-h-[78svh] max-w-full lg:col-span-6"
            style={{ clipPath: "inset(calc((1 - clamp(0, calc(var(--p) / 0.35), 1)) * 18%))" }}
          >
            <ScrubVideo src="/video/leite.mp4" srcPequeno="/video/leite-sm.mp4" trigger={ref} still={1} className="absolute inset-0 size-full object-cover" />
          </div>

          <div className="flex flex-col gap-4 lg:col-span-3 lg:self-end lg:pb-8 lg:text-right">
            <p className={titulo} style={reveal(0.45, 0.75)}>
              Desenhado à <em className="italic">mão.</em>
            </p>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60" style={reveal(0.5, 0.7, 12)}>
              05 — Leite · vaporizado na hora
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
