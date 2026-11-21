"use client";

import { useEffect, useRef } from "react";
import { ScrollTrigger } from "@/lib/gsap";
import { LOTES } from "@/lib/site";
import { useScrollProgress } from "@/lib/useScrollProgress";
import { Revela } from "@/components/Revela";

/** Scroll horizontal com sticky: a seção ganha altura = distância horizontal do trilho. */
export function Graos() {
  const ref = useRef<HTMLElement>(null);
  const trilho = useRef<HTMLDivElement>(null);
  const distancia = useRef(0);

  useEffect(() => {
    const section = ref.current!;
    const track = trilho.current!;
    const medir = () => {
      const d = Math.max(0, track.scrollWidth - window.innerWidth);
      if (d === distancia.current) return;
      distancia.current = d;
      section.style.setProperty("--dist", `${d}px`);
      // antes do load o ScrollTrigger ainda vai fazer o refresh dele: não force layout à toa
      if (document.readyState === "complete") ScrollTrigger.refresh();
    };
    const ro = new ResizeObserver(medir);
    ro.observe(track);
    return () => ro.disconnect();
  }, []);

  useScrollProgress(ref, (p) => {
    ref.current?.style.setProperty("--p", p.toFixed(4));
    if (trilho.current) trilho.current.style.transform = `translate3d(${-p * distancia.current}px, 0, 0)`;
  });

  return (
    <section
      ref={ref}
      aria-label="Lotes"
      className="relative h-[calc(100svh+var(--dist,0px))] bg-creme text-cafe [--p:0] motion-reduce:h-auto"
    >
      <div className="sticky top-0 flex h-svh items-center overflow-hidden motion-reduce:static motion-reduce:h-auto motion-reduce:overflow-x-auto motion-reduce:py-28">
        {/* mesma margem esquerda do .shell, mesmo em telas > 1400px */}
        <div
          ref={trilho}
          className="flex w-max items-center gap-5 px-[max(1.5rem,calc((100vw-1400px)/2+1.5rem))] will-change-transform md:gap-8 md:px-[max(3rem,calc((100vw-1400px)/2+3rem))] motion-reduce:transform-none!"
        >
          <div className="flex w-[82vw] shrink-0 flex-col justify-center pr-6 md:w-[34vw] md:pr-16">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-cafe/65">04 — Lotes</p>
            <Revela className="mt-8 font-serif text-title">
              Três lotes. Três <em className="italic">histórias.</em>
            </Revela>
            <Revela as="p" delay={0.15} className="mt-8 max-w-[32ch] text-lead text-cafe/70">
              Torramos em lotes de 12 kg, toda terça. Cada café com a sua curva, até a nota aparecer.
            </Revela>
          </div>

          {LOTES.map((l, i) => (
            <article
              key={l.nome}
              className="relative flex h-[74svh] w-[80vw] shrink-0 flex-col justify-between border border-cafe/12 bg-[color-mix(in_srgb,var(--color-cafe)_3.5%,var(--color-creme))] p-6 md:h-[78svh] md:w-[30vw] md:min-w-[380px] md:p-8"
            >
              <header className="flex justify-between font-mono text-[11px] uppercase tracking-[0.18em] text-cafe/65">
                <span>Lote 0{i + 1}</span>
                <span className="tabular-nums">{l.pontos} pts</span>
              </header>

              {/* notas de sabor (Flow, fundo achatado pra branco: scripts/fundo_branco.py) no "chão" do card, por multiply:
                  o fundo some no card e o arranjo fica alinhado embaixo. O card precisa de fundo opaco: o trilho
                  (will-change) isola a mistura, e com o fundo translúcido o multiply não teria com o que multiplicar.
                  O grão gira e flutua por cima conforme o trilho passa */}
              <div className="relative -mx-6 my-2 min-h-0 flex-1 md:-mx-8">
                <img
                  src={l.notasImg}
                  alt={`Notas de sabor do lote ${l.nome}: ${l.notas.replace(" · ", " e ").toLowerCase()}`}
                  width={900}
                  height={1205}
                  loading="lazy"
                  decoding="async"
                  className="borda-suave absolute inset-0 size-full object-cover object-bottom mix-blend-multiply"
                />
                <img
                  src={l.img}
                  alt={`Grão do lote ${l.nome}, torra ${l.torra.toLowerCase()}`}
                  width={800}
                  height={800}
                  loading="lazy"
                  decoding="async"
                  className="absolute top-[33%] left-1/2 w-[74%] max-w-[400px] drop-shadow-[0_28px_32px_rgba(26,17,11,0.32)]"
                  style={{
                    translate: `-50% calc(-50% + (var(--p) - ${0.25 + i * 0.25}) * -60px)`,
                    rotate: `calc((var(--p) - ${0.25 + i * 0.25}) * 50deg)`,
                  }}
                />
              </div>

              <div>
                <h3 className="font-serif text-[clamp(2rem,3.2vw,3rem)] leading-none tracking-[-0.02em]">{l.nome}</h3>
                <p className="mt-3 font-serif text-lg italic text-cafe/75 md:text-xl">{l.notas}</p>
                <dl className="mt-6 grid grid-cols-3 gap-3 border-t border-cafe/15 pt-4">
                  {[
                    ["Variedade", l.variedade],
                    ["Processo", l.processo],
                    ["Altitude", l.altitude],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-cafe/65">{k}</dt>
                      <dd className="mt-1 font-mono text-[13px] leading-snug">{v}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </article>
          ))}
          <div className="w-[6vw] shrink-0" aria-hidden />
        </div>
      </div>
    </section>
  );
}
