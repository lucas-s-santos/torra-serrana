"use client";

import { useRef, type CSSProperties, type ReactNode } from "react";
import { useScrollVar } from "@/lib/useScrollProgress";
import { Revela } from "@/components/Revela";

/** Foto 3:4 em WebP (800/1200 px): `<img>` puro como no resto do site, sem o runtime do next/image no bundle inicial */
function Foto({ nome, alt, sizes = "(min-width: 768px) 30vw, 50vw" }: { nome: string; alt: string; sizes?: string }) {
  return (
    <img
      src={`/img/casa/${nome}-800.webp`}
      srcSet={`/img/casa/${nome}-800.webp 800w, /img/casa/${nome}-1200.webp 1200w`}
      sizes={sizes}
      alt={alt}
      loading="lazy"
      decoding="async"
      width={800}
      height={1067}
      className="absolute inset-0 size-full object-cover"
    />
  );
}

/** Foto 3:4 com legenda em mono; `vel` = deslocamento de parallax (svh) no desktop. */
function Quadro({ legenda, vel, className = "", children }: { legenda: string; vel: number; className?: string; children: ReactNode }) {
  return (
    <figure className={className}>
      <div
        className="relative aspect-[3/4] overflow-hidden bg-cafe/10 md:[translate:0_calc((0.5-var(--p))*var(--vel))]"
        style={{ "--vel": `${vel}svh` } as CSSProperties}
      >
        {children}
      </div>
      <figcaption className="mt-4 font-mono text-[11px] uppercase tracking-[0.18em] text-cafe/65">{legenda}</figcaption>
    </figure>
  );
}

export function Casa() {
  const ref = useRef<HTMLElement>(null);
  useScrollVar(ref, { start: "top bottom", end: "bottom top" });

  return (
    <section ref={ref} aria-label="A casa" className="relative overflow-hidden bg-creme text-cafe [--p:0.5]">
      <div className="shell py-28 md:py-40">
        <div className="grid gap-8 md:grid-cols-12 md:items-end md:gap-10">
          <div className="md:col-span-7">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-cafe/65">07 — A casa</p>
            <Revela className="mt-8 font-serif text-title">
              Uma casa pequena <em className="italic">na serra.</em>
            </Revela>
          </div>
          <Revela as="p" delay={0.15} className="max-w-[34ch] text-lead text-cafe/75 md:col-span-4 md:col-start-9">
            Torramos às terças, num torrador de cinco quilos. Nos outros dias a porta fica aberta e o café vai direto pra mesa.
          </Revela>
        </div>

        {/* mobile: torrador inteiro em cima, fotos lado a lado; desktop: três em escada */}
        <div className="mt-16 grid grid-cols-2 gap-4 md:mt-28 md:grid-cols-12 md:items-start md:gap-6">
          <Quadro legenda="Fachada · Estrada da Serra, km 4" vel={6} className="md:col-span-4 md:mt-28">
            <Foto nome="casa-fachada" alt="A fachada caiada da torrefação, entre pés de café na encosta." />
          </Quadro>
          <Quadro legenda="Torrador · 5 kg · às terças" vel={-4} className="order-first col-span-2 md:order-none md:col-span-4">
            <Foto
              nome="casa-torrador"
              alt="O torrador pequeno no canto da casa, ao lado do balcão e da janela para a serra."
              sizes="(min-width: 768px) 30vw, 100vw"
            />
          </Quadro>
          <Quadro legenda="Balcão · 7 lugares" vel={10} className="md:col-span-4 md:mt-56">
            <Foto nome="casa-balcao" alt="O balcão de nogueira com a máquina de espresso e xícaras creme empilhadas." />
          </Quadro>
        </div>
      </div>
    </section>
  );
}
