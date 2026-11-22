"use client";

import { useEffect, useRef, type CSSProperties } from "react";

/** Borda da mancha: círculo de raio 1 ondulado por uma soma de senos (como o anel da Origem). */
const MANCHA = (() => {
  const n = 120;
  let d = "";
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    const r =
      1 +
      0.026 * Math.sin(a * 3 + 0.7) +
      0.02 * Math.sin(a * 7 + 2.1) +
      0.012 * Math.sin(a * 13 + 4.2) +
      0.008 * Math.sin(a * 23 + 1.3) +
      0.005 * Math.sin(a * 41 + 5.1);
    d += `${i ? "L" : "M"}${(Math.cos(a) * r).toFixed(4)} ${(Math.sin(a) * r).toFixed(4)}`;
  }
  return `${d}Z`;
})();

/** Gota apontando pra cima, bojo em (0, 0.35) e base em y = 1.5: subida 1.5, a base toca o centro da tela no impacto. */
const GOTA = "M0 -1.9 C0.5 -1 1.15 -0.35 1.15 0.35 A1.15 1.15 0 0 1 -1.15 0.35 C-1.15 -0.35 -0.5 -1 0 -1.9 Z";

/** Respingos do impacto: [ângulo em graus (0 = direita, -90 = cima), distância, raio]. */
const RESPINGOS = [
  [-162, 4.2, 0.32],
  [-138, 5.6, 0.24],
  [-112, 4.8, 0.36],
  [-90, 6.2, 0.22],
  [-66, 5.1, 0.3],
  [-40, 5.8, 0.26],
  [-16, 4, 0.34],
  [180, 3.2, 0.2],
  [0, 3.4, 0.22],
] as const;

const v = (vars: Record<string, string>) => vars as CSSProperties;

/**
 * Abertura do site: tela marrom (torra), uma gota de café cai no meio, bate, respinga, e a mancha se espalha até virar
 * o café do hero. CSS puro (começa no primeiro paint, sem esperar JS); aqui só se esconde no fim, ou na hora
 * se a pessoa já rolar. Na 2ª visita da sessão nem aparece (script do layout). Tempos em globals.css.
 */
export function Gota() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current!;
    if (getComputedStyle(el).display === "none") return;
    try {
      sessionStorage.setItem("gota", "1");
    } catch {}
    const fim = (e: AnimationEvent) => {
      if (e.target === el) el.hidden = true;
    };
    const pula = () => {
      el.style.animation = "gota-some 0.25s ease both";
      sinais.forEach((s) => removeEventListener(s, pula));
    };
    const sinais = ["wheel", "touchstart", "keydown"];
    el.addEventListener("animationend", fim);
    sinais.forEach((s) => addEventListener(s, pula, { passive: true, once: true }));
    return () => {
      el.removeEventListener("animationend", fim);
      sinais.forEach((s) => removeEventListener(s, pula));
    };
  }, []);

  return (
    <div ref={ref} aria-hidden className="gota pointer-events-none fixed inset-0 z-90">
      <svg viewBox="-50 -50 100 100" preserveAspectRatio="xMidYMid slice" className="size-full">
        <defs>
          <radialGradient id="gota-cor" cx="0.36" cy="0.62" r="0.75">
            <stop offset="0" stopColor="#7a4424" />
            <stop offset="0.45" stopColor="#2e180c" />
            <stop offset="1" stopColor="#120a05" />
          </radialGradient>
        </defs>

        <path d={MANCHA} fill="var(--color-cafe)" className="gota-mancha" />

        {/* gota, ondas e respingos em escala própria: 1 unidade aqui = 2,6% do lado maior da tela */}
        <g transform="scale(2.6)">
          {[
            { s: "9", d: "0.7s" },
            { s: "6", d: "0.8s" },
          ].map((o) => (
            <circle
              key={o.s}
              r="1"
              fill="none"
              stroke="var(--color-cafe)"
              strokeWidth="2.5"
              vectorEffect="non-scaling-stroke"
              className="gota-onda"
              style={v({ "--s": o.s, "--d": o.d })}
            />
          ))}

          {RESPINGOS.map(([a, dist, r]) => {
            const rad = (a * Math.PI) / 180;
            return (
              <circle
                key={a}
                r={r}
                fill="var(--color-cafe)"
                className="gota-respingo"
                style={v({ "--x": `${(Math.cos(rad) * dist).toFixed(2)}px`, "--y": `${(Math.sin(rad) * dist).toFixed(2)}px` })}
              />
            );
          })}

          <g className="gota-cai">
            <g className="gota-bate">
              <path d={GOTA} transform="translate(0 -1.5)" fill="url(#gota-cor)" />
              <ellipse cx="-0.45" cy="-1.6" rx="0.22" ry="0.42" fill="#fff" opacity="0.45" transform="rotate(24 -0.45 -1.6)" />
            </g>
          </g>
        </g>
      </svg>
    </div>
  );
}
