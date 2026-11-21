"use client";

import { useRef } from "react";
import { ScrubVideo } from "@/components/ScrubVideo";
import { reveal, useScrollVar } from "@/lib/useScrollProgress";

export function Crema() {
  const ref = useRef<HTMLElement>(null);
  useScrollVar(ref);

  return (
    <section ref={ref} aria-label="Crema" className="relative h-[280svh] bg-cafe [--p:0] motion-reduce:h-svh">
      <div className="sticky top-0 h-svh overflow-hidden">
        {/* celular: tela cheia. Desktop: metade direita de ponta a ponta (o vídeo é 9:16: esticado na largura toda ficaria mole) */}
        <div className="absolute inset-0 md:left-1/2">
          <ScrubVideo src="/video/crema.mp4" srcPequeno="/video/crema-sm.mp4" trigger={ref} className="absolute inset-0 size-full object-cover md:object-[50%_40%]" />
          {/* legibilidade do texto e emenda com o café das seções vizinhas */}
          <div className="absolute inset-0 bg-[linear-gradient(to_top,var(--color-cafe)_0%,transparent_45%,transparent_75%,color-mix(in_srgb,var(--color-cafe)_55%,transparent)_100%)] md:bg-[linear-gradient(to_right,var(--color-cafe)_0%,transparent_30%),linear-gradient(to_bottom,color-mix(in_srgb,var(--color-cafe)_80%,transparent)_0%,transparent_22%)]" />
        </div>
        <div className="absolute inset-x-0 bottom-0 pb-10 md:inset-y-0 md:flex md:items-center md:pb-0">
          <div className="shell flex w-full flex-col-reverse gap-6 md:flex-col md:gap-8">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60" style={reveal(0.4, 0.6, 12)}>
              02 — Crema · 25 s de descanso
            </p>
            <h2 className="max-w-[14ch] font-serif text-title md:max-w-[9ch]" style={reveal(0.3, 0.55)}>
              Viva, densa, cor de <em className="italic">avelã.</em>
            </h2>
          </div>
        </div>
      </div>
    </section>
  );
}
