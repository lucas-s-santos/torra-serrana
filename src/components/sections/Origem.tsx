"use client";

import { useRef } from "react";
import { ORIGEM } from "@/lib/site";
import { reveal, useScrollVar } from "@/lib/useScrollProgress";
import { Revela } from "@/components/Revela";

const f = (n: number) => n.toFixed(2);

/** Círculo irregular (marca de xícara) como Bézier fechada: Catmull-Rom sobre pontos com ondulação. */
function anel(r: number, ondula: number, semente: number, n = 56) {
  const pts = Array.from({ length: n }, (_, i) => {
    const a = (i / n) * Math.PI * 2;
    const rr =
      r + ondula * (0.6 * Math.sin(a * 3 + semente) + 0.3 * Math.sin(a * 7 + semente * 2.1) + 0.1 * Math.sin(a * 13 + semente * 0.7));
    return [200 + rr * Math.cos(a - Math.PI / 2), 200 + rr * Math.sin(a - Math.PI / 2)];
  });
  let d = `M${f(pts[0][0])},${f(pts[0][1])}`;
  for (let i = 0; i < n; i++) {
    const [p0, p1, p2, p3] = [-1, 0, 1, 2].map((k) => pts[(i + k + n) % n]);
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    d += `C${f(c1[0])},${f(c1[1])} ${f(c2[0])},${f(c2[1])} ${f(p2[0])},${f(p2[1])}`;
  }
  return `${d}Z`;
}

const PRINCIPAL = anel(150, 4, 1.3);
const HALO = anel(152, 6, 2.2);
const INTERNO = anel(139, 3, 0.4);

// stroke-dashoffset dirigido pela --p da seção (pathLength=1 normaliza o comprimento)
const desenha = (atraso = 0, ate = 1) => ({
  strokeDasharray: 1,
  strokeDashoffset: `calc(1 - clamp(0, calc((var(--p) - ${atraso}) / ${ate - atraso}), 1))`,
});

function Anel() {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[560px]">
      <svg viewBox="0 0 400 400" className="absolute inset-0 size-full -rotate-12 text-creme" aria-hidden>
        <defs>
          <filter id="mancha" x="-10%" y="-10%" width="120%" height="120%">
            <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7" />
            <feDisplacementMap in="SourceGraphic" scale="5" />
          </filter>
        </defs>
        <g fill="none" stroke="currentColor" strokeLinecap="round" filter="url(#mancha)">
          <path d={HALO} pathLength={1} strokeWidth={22} opacity={0.06} style={desenha(0, 0.85)} />
          <path d={PRINCIPAL} pathLength={1} strokeWidth={4.5} opacity={0.6} style={desenha(0, 0.8)} />
          {/* onde o café empoçou: trecho mais grosso que nasce junto com o traço */}
          <path
            d={PRINCIPAL}
            pathLength={1}
            strokeWidth={11}
            opacity={0.16}
            style={{ strokeDasharray: "calc(clamp(0, calc((var(--p) - 0.5) / 0.3), 1) * 0.26) 1", strokeDashoffset: -0.52 }}
          />
          <path d={INTERNO} pathLength={1} strokeWidth={1.3} opacity={0.35} style={desenha(0.15, 0.95)} />
        </g>
        <g fill="currentColor" style={{ opacity: "calc(clamp(0, calc((var(--p) - 0.85) / 0.15), 1) * 0.2)" }}>
          <circle cx="352" cy="118" r="5" />
          <circle cx="366" cy="96" r="2.5" />
          <circle cx="58" cy="300" r="3" />
        </g>
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center" style={reveal(0.55, 0.85, 16)}>
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/80">22°07′ S · 45°08′ O</p>
          <p className="mt-3 font-serif text-[clamp(1.75rem,3vw,2.75rem)] leading-none">
            Carmo de <em className="italic">Minas</em>
          </p>
        </div>
      </div>
    </div>
  );
}

export function Origem() {
  const ref = useRef<HTMLElement>(null);
  useScrollVar(ref, { start: "top 75%", end: "center 40%" });

  return (
    <section ref={ref} id="origem" className="relative bg-[linear-gradient(to_bottom,var(--color-cafe),var(--color-torra-funda)_14vh,var(--color-torra)_48vh)] text-creme [--p:0]">
      <div className="shell grid items-center gap-16 py-28 md:grid-cols-12 md:gap-10 md:py-44">
        <div className="md:col-span-6">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/80">01 — Origem</p>
          <Revela className="mt-8 max-w-[12ch] font-serif text-title">
            Toda xícara começa no <em className="italic">pé.</em>
          </Revela>
          <Revela as="p" delay={0.15} className="mt-8 max-w-[36ch] text-lead text-creme/90">
            Colhemos à mão, só a cereja madura, na encosta da serra. Devagar, pé por pé: é o único jeito de o grão chegar inteiro na xícara.
          </Revela>
          <dl className="mt-14 border-t border-creme/25">
            {ORIGEM.map((d, i) => (
              <div
                key={d.label}
                className="flex items-baseline justify-between gap-6 border-b border-creme/25 py-4"
                style={reveal(0.35 + i * 0.12, 0.6 + i * 0.12, 12)}
              >
                <dt className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/80">{d.label}</dt>
                <dd className="text-right font-mono text-base tabular-nums md:text-lg">{d.valor}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="md:col-span-6">
          <Anel />
        </div>
      </div>
    </section>
  );
}
