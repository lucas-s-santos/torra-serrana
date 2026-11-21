"use client";

import { useRef, type CSSProperties, type ReactNode } from "react";
import { ImageSequence } from "@/components/ImageSequence";
import dynamic from "next/dynamic";
import type { Giro360Handle } from "@/components/Giro360";

// só aparece no fim do hero: fora do JS da primeira carga
const Giro360 = dynamic(() => import("@/components/Giro360").then((m) => m.Giro360), { ssr: false });

const FRAMES = 214;
const HOLD = 0.09; // fim do scroll com a xícara parada (e girável)
const CORTE_GIRO = [210, 470, 1180, 760] as const; // caixa da xícara nos 72 ângulos (mesmo CORTE do to_webp.sh)

type Contador = { de: number; ate: number; frames: [number, number]; casas?: number; unidade: string };
type Etapa = {
  nome: string;
  /** último frame da etapa (numeração do Blender, ver PROC em blender/cena01_do_pe_a_xicara.py) */
  ate: number;
  frase?: ReactNode;
  dado?: string | Contador;
  rotulo?: string;
};

const ETAPAS: Etapa[] = [
  { nome: "Cereja", ate: 28 },
  { nome: "Grão verde", ate: 46, frase: "Dentro da fruta, a semente.", dado: "1.100 m", rotulo: "Bourbon Amarelo" },
  { nome: "Torra", ate: 70, frase: "Torramos devagar, até o ponto médio.", dado: { de: 24, ate: 205, frames: [46, 66], unidade: "°C" }, rotulo: "Torra média" },
  { nome: "Moagem", ate: 96, frase: "Moemos na hora de tirar.", dado: "250 µm", rotulo: "Moagem fina" },
  { nome: "Dose", ate: 122, frase: "Pesamos cada dose.", dado: { de: 0, ate: 18, frames: [92, 118], casas: 1, unidade: "g" }, rotulo: "Na balança" },
  { nome: "Compactação", ate: 152, frase: "Nivelamos e compactamos.", dado: "15 kg", rotulo: "De pressão, reta" },
  { nome: "Extração", ate: 192, frase: "Um fio cor de mel.", dado: { de: 0, ate: 28, frames: [170, 190], unidade: "s" }, rotulo: "9 bar · 93 °C" },
  {
    nome: "Xícara",
    ate: FRAMES,
    frase: (
      <>
        Do pé <em className="italic">à xícara.</em>
      </>
    ),
    dado: "36 g",
    rotulo: "Proporção 1:2",
  },
];

const atraso = (ms: number) => ({ "--atraso": `${ms}ms` }) as CSSProperties;
const suave = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/**
 * Título em duas camadas idênticas: a de trás (sob o canvas) mostra "Do pé", a da frente "à xícara.".
 * Cada linha fica inteira de um lado do objeto, então nenhuma letra é cortada ao meio.
 * Posições em frações do quadro quadrado (--s), medidas nos frames: a cereja ocupa ~35–78% da altura.
 */
function Titulo({ frente = false, wrapRef }: { frente?: boolean; wrapRef: (el: HTMLDivElement | null) => void }) {
  const Tag = frente ? "p" : "h1";
  return (
    <div ref={wrapRef} className="absolute inset-0 will-change-transform">
      <Tag
        aria-hidden={frente || undefined}
        className="text-center font-serif text-[clamp(3.5rem,20vw,6rem)] leading-[0.9] tracking-[-0.035em] text-creme md:text-[calc(var(--s)*0.155)]"
      >
        <span
          className={`entrada absolute inset-x-0 bottom-[calc(50%+var(--s)*0.155)] md:-translate-x-[0.42em] ${frente ? "text-transparent" : ""}`}
          style={atraso(150)}
        >
          Do pé
        </span>{" "}
        <span
          className={`entrada absolute inset-x-0 top-[calc(50%+var(--s)*0.175)] md:translate-x-[0.3em] ${frente ? "" : "text-transparent"}`}
          style={atraso(300)}
        >
          à <em className="italic">xícara.</em>
        </span>
      </Tag>
    </div>
  );
}

function Numero({ dado, refs }: { dado: string | Contador; refs: (int: Element | null, dec: Element | null) => void }) {
  if (typeof dado === "string") return <span>{dado}</span>;
  return (
    <span ref={(el) => void (el && refs(el.querySelector("[data-int]"), el.querySelector("[data-dec]")))}>
      <span data-int>{dado.de}</span>
      {dado.casas ? (
        <>
          {/* vírgula do Geist Mono ocupa uma célula inteira: aperta pra não parecer "18 , 0" */}
          <span className="-mx-[0.22em]">,</span>
          <span data-dec>0</span>
        </>
      ) : null}{" "}
      {dado.unidade}
    </span>
  );
}

export function Hero() {
  const raiz = useRef<HTMLDivElement>(null);
  const titulos = useRef<(HTMLDivElement | null)[]>([]);
  const etapas = useRef<(HTMLLIElement | null)[]>([]);
  const legendas = useRef<(HTMLDivElement | null)[]>([]);
  const contadores = useRef<Map<number, [Element | null, Element | null]>>(new Map());
  const barra = useRef<HTMLDivElement>(null);
  const dica = useRef<HTMLParagraphElement>(null);
  const giro = useRef<Giro360Handle>(null);
  const atual = useRef(-1);

  const onProgress = (p: number, frame: number) => {
    const f = frame + 1; // numeração do Blender
    const e = ETAPAS.findIndex((x) => f <= x.ate);
    if (e !== atual.current) {
      atual.current = e;
      etapas.current.forEach((el, i) => el?.toggleAttribute("data-on", i === e));
      legendas.current.forEach((el, i) => el?.toggleAttribute("data-on", i === e));
    }

    // título sobe e some enquanto a cereja cresce; dali em diante falam as legendas
    const t = suave(6, 26, f);
    raiz.current?.style.setProperty("--k", t.toFixed(3));
    for (const el of titulos.current) {
      if (!el) continue;
      el.style.transform = `translate3d(0, ${-t * 10}svh, 0)`;
      el.style.opacity = String(1 - t);
      el.style.visibility = t >= 1 ? "hidden" : "";
    }

    for (const [i, [int, dec]] of contadores.current) {
      const c = ETAPAS[i].dado as Contador;
      const v = c.de + (c.ate - c.de) * suave(c.frames[0], c.frames[1], f);
      if (int) int.textContent = String(Math.floor(v));
      if (dec) dec.textContent = String(Math.floor((v % 1) * 10 ** (c.casas ?? 0))).padStart(c.casas ?? 0, "0");
    }

    if (barra.current) barra.current.style.transform = `scaleX(${Math.min(1, p / (1 - HOLD))})`;
    if (dica.current) dica.current.style.opacity = String(1 - Math.min(1, p * 14));
    if (f > 150) giro.current?.carregar();
    giro.current?.ativar(p >= 1 - HOLD * 0.8);
  };

  return (
    <div
      id="topo"
      ref={raiz}
      // --s: lado do quadro quadrado dos frames. No desktop o objeto desliza --dx pra direita enquanto o título sai
      // (--k 0→1), abrindo a coluna das legendas; --legenda é a largura que cabe ali sem encostar no objeto.
      className="group [--dx:calc(var(--k,0)*var(--dxmax))] [--dxmax:0px] [--esq:max(3rem,calc((100vw-1400px)/2+3rem))] [--legenda:calc(var(--livre)+var(--dxmax)+var(--s)*0.08-var(--esq))] [--livre:calc((100vw-var(--s))/2)] [--s:min(100vw,100svh)] lg:[--dxmax:clamp(0px,calc(var(--livre)/2),220px)]"
    >
      <ImageSequence
        src="/seq/cena01"
        count={FRAMES}
        length={900}
        hold={HOLD}
        alt="Uma cereja de café se abre, o grão verde torra, vira pó, é compactado no porta-filtro e extraído numa xícara, onde o leite desenha uma espiral."
        under={<Titulo wrapRef={(el) => void (titulos.current[0] = el)} />}
        canvasClassName="quadro-borda translate-x-(--dx) group-data-giro:invisible"
        onProgress={onProgress}
      >
        <Giro360
          ref={giro}
          src="/seq/xicara360"
          count={72}
          corte={CORTE_GIRO}
          label="Xícara de cappuccino com uma espiral de leite. Arraste para girar."
          onVisivel={(v) => raiz.current?.toggleAttribute("data-giro", v)}
          className="translate-x-(--dx)"
        />
        <Titulo frente wrapRef={(el) => void (titulos.current[1] = el)} />

        {/* legenda da etapa: no mobile acima do objeto, no desktop embaixo à esquerda */}
        <div className="pointer-events-none absolute inset-x-0 top-[5.5rem] lg:top-auto lg:bottom-32">
          <div className="shell grid">
            {ETAPAS.map((e, i) =>
              e.frase ? (
                <div
                  key={e.nome}
                  ref={(el) => void (legendas.current[i] = el)}
                  className="col-start-1 row-start-1 translate-y-4 opacity-0 lg:max-w-(--legenda) transition-[opacity,transform] duration-500 ease-out-expo data-on:translate-y-0 data-on:opacity-100 data-on:delay-150 data-on:duration-1000"
                >
                  <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">
                    <span className="tabular-nums">0{i + 1}</span> — {e.nome}
                  </p>
                  <p className="mt-3 max-w-[13ch] font-serif text-[clamp(2rem,3vw,3rem)] leading-[1.02] tracking-[-0.02em] text-creme">
                    {e.frase}
                  </p>
                  {e.dado && (
                    <p className="mt-4 flex items-baseline gap-3 font-mono tabular-nums text-caramelo">
                      <span className="text-[clamp(1.5rem,2.4vw,2.25rem)] leading-none">
                        <Numero dado={e.dado} refs={(int, dec) => contadores.current.set(i, [int, dec])} />
                      </span>
                      <span className="text-[11px] uppercase tracking-[0.18em] text-creme/60">{e.rotulo}</span>
                    </p>
                  )}
                </div>
              ) : null,
            )}
          </div>
        </div>

        <p className="pointer-events-none absolute inset-x-0 bottom-24 text-center font-mono text-[11px] uppercase tracking-[0.18em] text-creme/70 opacity-0 transition-opacity duration-700 group-data-giro:opacity-100 md:hidden">
          ← Arraste para girar →
        </p>

        <div className="pointer-events-none absolute inset-x-0 bottom-0 pb-6 md:pb-9">
          <div style={atraso(900)} className="entrada shell flex items-end justify-between gap-10 font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">
            <p className="hidden w-72 leading-relaxed md:block">
              Torrefação de cafés especiais
              <br />
              Sul de Minas · 1.100 m
            </p>
            <div className="w-full max-w-xl">
              <ol className="flex justify-between gap-3">
                {ETAPAS.map((e, i) => (
                  <li
                    key={e.nome}
                    ref={(el) => void (etapas.current[i] = el)}
                    data-on={i === 0 ? "" : undefined}
                    className="group/etapa transition-colors duration-500 data-on:text-creme"
                  >
                    <span className="tabular-nums text-creme/45 group-data-on/etapa:text-caramelo">0{i + 1}</span>
                    <span className="hidden group-data-on/etapa:inline"> {e.nome}</span>
                  </li>
                ))}
              </ol>
              <div className="relative mt-3 h-px bg-creme/15">
                <div ref={barra} className="h-full origin-left scale-x-0 bg-caramelo" />
                {/* marcas das etapas na régua */}
                {ETAPAS.slice(0, -1).map((e) => (
                  <span key={e.nome} className="absolute -top-[3px] h-[7px] w-px bg-creme/25" style={{ left: `${(e.ate / FRAMES) * 100}%` }} />
                ))}
              </div>
            </div>
            <div className="relative hidden w-72 text-right md:block">
              <p ref={dica}>Role pra torrar</p>
              <p className="absolute inset-0 text-creme/80 opacity-0 transition-opacity duration-700 group-data-giro:opacity-100">
                ← Arraste a xícara →
              </p>
            </div>
          </div>
        </div>
      </ImageSequence>
    </div>
  );
}
