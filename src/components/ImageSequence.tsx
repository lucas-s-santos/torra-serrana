"use client";

import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { preload } from "react-dom";
import { gsap, useGSAP } from "@/lib/gsap";
import { prefersReducedMotion, useReducedMotion } from "@/lib/useReducedMotion";
import { draw, fitCanvas, frameStore, frameUrl, janela, pickSize, type FrameStore } from "@/lib/frames";

type Props = {
  /** pasta em /public com uma subpasta por largura: `${src}/960/0001.webp`, `${src}/1600/0001.webp`… */
  src: string;
  count: number;
  /** larguras renderizadas; usa a menor que cobre o canvas (mobile não decodifica 1600²) */
  sizes?: number[];
  ext?: string;
  /** altura da seção em svh: quanto scroll a sequência consome (a parte sticky ocupa 100) */
  length?: number;
  /** fração final do scroll em que o último frame fica parado */
  hold?: number;
  fit?: "contain" | "cover";
  alt: string;
  /** camada atrás do canvas (ex.: título de trás do sanduíche) */
  under?: ReactNode;
  /** camada na frente do canvas */
  children?: ReactNode;
  className?: string;
  canvasClassName?: string;
  /** progresso 0→1 do scroll e frame atual (pra UI sincronizada; não dispara re-render) */
  onProgress?: (p: number, frame: number) => void;
};

const PRELOAD = 20;
const SIZES = [720, 960, 1600]; // 720: celular comum (390 px × DPR 2); 960: celular grande e desktop DPR 1; 1600: retina

/**
 * Sequência de frames num canvas sticky, ligada ao scroll.
 * Mostra o 1º frame logo; os 20 seguintes depois do load; o resto na primeira rolagem/toque.
 */
export function ImageSequence({
  src,
  count,
  sizes = SIZES,
  ext = "webp",
  length = 400,
  hold = 0,
  fit = "contain",
  alt,
  under,
  children,
  className = "",
  canvasClassName = "",
  onProgress,
}: Props) {
  const sectionRef = useRef<HTMLElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const showFrame = useRef<(i: number) => void>(() => {});
  const progressCb = useRef(onProgress);
  useEffect(() => {
    progressCb.current = onProgress;
  });
  const [shown, setShown] = useState(false);
  const reduced = useReducedMotion();
  const sorted = [...sizes].sort((a, b) => a - b);
  const sizesKey = sorted.join(","); // dependência estável mesmo se `sizes` vier inline

  // o menor tamanho é o que o mobile usa (alvo do Lighthouse). "fetch": é assim que o store baixa os frames
  preload(frameUrl(src, sorted[0], 0, ext), { as: "fetch", crossOrigin: "anonymous", fetchPriority: "low" });

  useEffect(() => {
    const canvas = canvasRef.current!;
    let ctx = canvas.getContext("2d")!;
    const size = pickSize(sizesKey.split(",").map(Number), canvas, fit);
    const still = prefersReducedMotion(); // o hook ainda vale false na hidratação: não baixar 20 frames à toa
    let current = still ? count - 1 : 0;
    let raf = 0;
    let alive = true;

    const paint = () => {
      raf = 0;
      draw(ctx, store.nearest(current), fit);
      // o gravador do reel (reel/fonte/gravar.mjs) só tira a foto quando o frame desenhado é o certo
      canvas.dataset.exato = String(store.has(current));
    };
    const store: FrameStore = frameStore(count, (i) => frameUrl(src, size, i, ext), {
      ...janela(size),
      onDecoded: () => {
        if (!raf) raf = requestAnimationFrame(paint);
      },
    });

    showFrame.current = (i) => {
      if (i === current) return;
      current = i;
      store.focus(i);
      if (!raf) raf = requestAnimationFrame(paint);
    };

    const ro = new ResizeObserver(() => {
      ctx = fitCanvas(canvas);
      paint();
    });
    ro.observe(canvas);

    (async () => {
      store.focus(current);
      await store.load([current], 1);
      if (!alive) return;
      setShown(true);
      if (still) return;
      // o resto só depois do load + ocioso: frames disputando banda com a fonte atrasam a 1ª pintura no 4G
      await new Promise<void>((r) => (document.readyState === "complete" ? r() : addEventListener("load", () => r(), { once: true })));
      await new Promise<void>((r) => ("requestIdleCallback" in window ? requestIdleCallback(() => r(), { timeout: 1500 }) : setTimeout(r, 300)));
      if (!alive) return;
      const order = Array.from({ length: count }, (_, i) => i);
      await store.load(order.slice(1, PRELOAD), 4);
      // o resto (vários MB) só quando a pessoa der sinal de que vai rolar: quem só abre a página não paga por ele
      await new Promise<void>((r) => {
        if (scrollY > 0) return r();
        const sinais = ["scroll", "wheel", "touchstart", "pointerdown", "keydown"];
        const vai = () => {
          for (const s of sinais) removeEventListener(s, vai);
          r();
        };
        for (const s of sinais) addEventListener(s, vai, { passive: true });
      });
      if (!alive) return;
      await store.load(order.slice(PRELOAD), 4);
    })();

    return () => {
      alive = false;
      ro.disconnect();
      cancelAnimationFrame(raf);
      store.dispose();
    };
  }, [src, count, sizesKey, ext, fit, reduced]);

  useGSAP(
    () => {
      if (reduced || prefersReducedMotion()) return progressCb.current?.(1, count - 1);
      const state = { p: 0 };
      gsap.to(state, {
        p: 1,
        ease: "none",
        scrollTrigger: { trigger: sectionRef.current, start: "top top", end: "bottom bottom", scrub: true },
        onUpdate: () => {
          const frame = Math.round(Math.min(1, state.p / (1 - hold)) * (count - 1));
          showFrame.current(frame);
          progressCb.current?.(state.p, frame);
        },
      });
    },
    { dependencies: [count, hold, reduced], scope: sectionRef },
  );

  return (
    <section
      ref={sectionRef}
      className={`relative h-(--seq-length) motion-reduce:h-svh ${className}`}
      style={{ "--seq-length": `${length}svh` } as CSSProperties}
    >
      <div className="sticky top-0 h-svh overflow-hidden">
        {under && <div className="absolute inset-0">{under}</div>}
        <canvas
          ref={canvasRef}
          role="img"
          aria-label={alt}
          className={`absolute inset-0 size-full transition-opacity duration-1000 ease-out-expo ${shown ? "opacity-100" : "opacity-0"} ${canvasClassName}`}
        />
        {children && <div className="absolute inset-0">{children}</div>}
      </div>
    </section>
  );
}
