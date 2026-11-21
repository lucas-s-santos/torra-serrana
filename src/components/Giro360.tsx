"use client";

import { useEffect, useImperativeHandle, useRef, type Ref } from "react";
import { gsap } from "@/lib/gsap";
import { prefersReducedMotion } from "@/lib/useReducedMotion";
import { fitCanvas, frameStore, frameUrl, pickSize, type FrameStore } from "@/lib/frames";

export type Giro360Handle = {
  /** começa a baixar os frames (chamar um pouco antes de precisar) */
  carregar(): void;
  /** liga/desliga o giro; ao desligar, volta pro ângulo 0 antes de sumir (emenda com o frame da sequência) */
  ativar(sim: boolean): void;
};

type Props = {
  ref?: Ref<Giro360Handle>;
  src: string;
  count: number;
  sizes?: number[];
  /** caixa do objeto [x, y, w, h] em px do quadro quadrado de 1600 (os frames vêm recortados nela: blender/to_webp.sh CORTE) */
  corte: readonly [number, number, number, number];
  label: string;
  /** chamado quando o canvas do giro aparece/some por cima da sequência */
  onVisivel?: (v: boolean) => void;
  className?: string;
};

const SIZES = [720, 960, 1600]; // 720: celular comum (390 px × DPR 2); 960: celular grande e desktop DPR 1; 1600: retina
const QUADRO = 1600;
const AUTO = 12; // °/s girando sozinho enquanto ninguém mexe
const ESPERA = 2500; // ms parado até voltar a girar sozinho

/**
 * Objeto renderizado em N ângulos (Blender) que gira com o arraste, com inércia.
 * Mesmo enquadramento do último frame da sequência: no ângulo 0 os dois são idênticos.
 * Os N ângulos ficam todos decodificados (recortados na caixa do objeto cabem em ~90 MB no celular): com janela
 * deslizante, um arraste rápido saía dela e a xícara sumia até decodificar. Entre dois ângulos faz crossfade,
 * senão os passos de 5° aparecem como trancos no giro lento.
 */
export function Giro360({ ref, src, count, sizes = SIZES, corte, label, onVisivel, className = "" }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // o pai pode chamar antes do efeito montar (reduced motion chama no layout effect): guarda o pedido
  const pedido = useRef({ carregar: false, ativo: false });
  const api = useRef<Giro360Handle>({ carregar: () => void (pedido.current.carregar = true), ativar: (s) => void (pedido.current.ativo = s) });
  const visivelCb = useRef(onVisivel);
  useEffect(() => {
    visivelCb.current = onVisivel;
  });
  useImperativeHandle(ref, () => ({ carregar: () => api.current.carregar(), ativar: (s) => api.current.ativar(s) }), []);

  useEffect(() => {
    const canvas = canvasRef.current!;
    let ctx = canvas.getContext("2d")!;
    const passo = 360 / count;
    const size = pickSize(sizes, canvas);
    const still = prefersReducedMotion();
    const s = { angulo: 0 };
    let ativo = false;
    let visivel = false;
    let pronto = false; // frame 0 decodificado: só então pode cobrir a sequência
    let carregando = false;
    let ultimoToque = 0;
    let vel = 0; // °/ms
    let arraste: { x: number; t: number } | null = null;
    let volta: gsap.core.Tween | undefined;

    const wrap = (i: number) => ((i % count) + count) % count;
    const frame = () => wrap(Math.round(s.angulo / passo));
    const paint = () => {
      const a = s.angulo / passo;
      const i = Math.floor(a);
      const t = a - i;
      const exatos = store.has(wrap(i)) && store.has(wrap(i + 1));
      const b0 = exatos ? store.nearest(wrap(i)) : store.nearest(frame());
      if (!b0) return; // nada decodificado ainda: deixa o que já está na tela em vez de apagar
      const b1 = exatos && t > 0.01 ? store.nearest(wrap(i + 1)) : undefined;
      // onde o quadro de 1600 cairia (contain, centrado) e a caixa recortada dentro dele
      const { width: cw, height: ch } = ctx.canvas;
      const k = Math.min(cw, ch) / QUADRO;
      const [x, y, w, h] = corte;
      const dx = (cw - QUADRO * k) / 2 + x * k;
      const dy = (ch - QUADRO * k) / 2 + y * k;
      ctx.clearRect(0, 0, cw, ch);
      ctx.globalAlpha = b1 ? 1 - t : 1;
      ctx.drawImage(b0, dx, dy, w * k, h * k);
      if (b1) {
        // "lighter" soma (pré-multiplicado): (1-t)·A + t·B, crossfade exato até no alpha
        ctx.globalCompositeOperation = "lighter";
        ctx.globalAlpha = t;
        ctx.drawImage(b1, dx, dy, w * k, h * k);
        ctx.globalCompositeOperation = "source-over";
      }
      ctx.globalAlpha = 1;
    };
    const store: FrameStore = frameStore(count, (i) => frameUrl(src, size, i), {
      ahead: count,
      behind: count,
      circular: true,
      onDecoded: () => {
        if (!pronto && store.has(0)) pronto = true;
        mostrar();
        paint();
      },
    });

    const mostrar = () => {
      const v = ativo && pronto;
      if (v === visivel) return;
      visivel = v;
      canvas.toggleAttribute("data-on", v);
      canvas.tabIndex = v ? 0 : -1;
      visivelCb.current?.(v);
    };

    const tick = (_: number, dt: number) => {
      if (!visivel || arraste || volta?.isActive()) return;
      if (Math.abs(vel) > 0.002) {
        s.angulo += vel * dt;
        vel *= Math.pow(0.94, dt / 16.7); // inércia
      } else if (!still && performance.now() - ultimoToque > ESPERA) {
        s.angulo += (AUTO * dt) / 1000;
      } else {
        // parado entre dois ângulos o crossfade mostraria a alça dobrada: assenta no ângulo mais perto
        const alvo = Math.round(s.angulo / passo) * passo;
        if (Math.abs(alvo - s.angulo) < 0.01) return;
        s.angulo += (alvo - s.angulo) * Math.min(1, dt / 90);
        if (Math.abs(alvo - s.angulo) < 0.05) s.angulo = alvo;
      }
      girou();
    };
    const girou = () => {
      store.focus(frame());
      paint();
    };

    const down = (e: PointerEvent) => {
      if (!visivel) return;
      volta?.kill();
      arraste = { x: e.clientX, t: e.timeStamp };
      vel = 0;
      canvas.setPointerCapture(e.pointerId);
    };
    const move = (e: PointerEvent) => {
      if (!arraste) return;
      const dx = e.clientX - arraste.x;
      const dt = Math.max(1, e.timeStamp - arraste.t);
      const graus = (dx / canvas.clientWidth) * 400; // ~uma volta por largura de tela arrastada
      s.angulo += graus;
      vel = vel * 0.6 + (graus / dt) * 0.4;
      arraste = { x: e.clientX, t: e.timeStamp };
      ultimoToque = performance.now();
      girou();
    };
    const up = () => {
      if (!arraste) return;
      arraste = null;
      ultimoToque = performance.now();
      if (still) vel = 0;
    };
    const key = (e: KeyboardEvent) => {
      const d = e.key === "ArrowRight" ? 30 : e.key === "ArrowLeft" ? -30 : 0;
      if (!d) return;
      e.preventDefault();
      vel = 0;
      ultimoToque = performance.now();
      volta = gsap.to(s, { angulo: Math.round((s.angulo + d) / passo) * passo, duration: still ? 0 : 0.6, ease: "power3.out", onUpdate: girou });
    };

    const ro = new ResizeObserver(() => {
      ctx = fitCanvas(canvas);
      paint();
    });
    ro.observe(canvas);
    canvas.addEventListener("pointerdown", down);
    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("pointercancel", up);
    canvas.addEventListener("keydown", key);
    gsap.ticker.add(tick);

    api.current = {
      carregar() {
        if (carregando) return;
        carregando = true;
        store.focus(0);
        // 0 primeiro, depois alternando pros dois lados
        const order = [0, ...Array.from({ length: count - 1 }, (_, k) => (k % 2 ? count - 1 - (k >> 1) : 1 + (k >> 1)))];
        store.load(order, 4);
      },
      ativar(sim) {
        if (sim === ativo) return;
        ativo = sim;
        if (sim) {
          api.current.carregar();
          ultimoToque = performance.now() - ESPERA + 900; // começa a girar sozinho logo: mostra que é 3D
          return mostrar();
        }
        // devolve pro ângulo 0 pelo caminho mais curto e só então entrega pra sequência
        vel = 0;
        arraste = null;
        const alvo = Math.round(s.angulo / 360) * 360;
        volta?.kill();
        volta = gsap.to(s, {
          angulo: alvo,
          duration: still || !visivel ? 0 : Math.min(0.7, Math.abs(alvo - s.angulo) / 300),
          ease: "power2.inOut",
          onUpdate: girou,
          onComplete: () => {
            s.angulo = 0;
            mostrar();
          },
        });
      },
    };

    if (pedido.current.carregar) api.current.carregar();
    if (pedido.current.ativo) api.current.ativar(true);

    return () => {
      ro.disconnect();
      gsap.ticker.remove(tick);
      volta?.kill();
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointermove", move);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("pointercancel", up);
      canvas.removeEventListener("keydown", key);
      store.dispose();
    };
  }, [src, count, sizes, corte]);

  return (
    <canvas
      ref={canvasRef}
      role="img"
      aria-label={label}
      aria-roledescription="objeto 3D, gire com as setas"
      tabIndex={-1}
      // pan-y: o arraste horizontal gira, o vertical continua rolando a página
      className={`pointer-events-none invisible absolute inset-0 size-full cursor-grab touch-pan-y select-none outline-none active:cursor-grabbing data-on:pointer-events-auto data-on:visible focus-visible:outline-2 focus-visible:-outline-offset-8 focus-visible:outline-caramelo/60 ${className}`}
    />
  );
}
