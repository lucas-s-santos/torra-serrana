"use client";

import { useEffect, useRef } from "react";
import { prefersReducedMotion } from "@/lib/useReducedMotion";
import { escolheSrc } from "@/lib/video";

/** Vídeo em loop que só baixa perto da tela e só toca enquanto visível. Reduced-motion: parado.
 *  `srcPequeno`: versão de 720 px, usada quando o vídeo aparece pequeno (ver escolheSrc). */
export function LoopVideo({ src, srcPequeno, className = "" }: { src: string; srcPequeno?: string; className?: string }) {
  const ref = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = ref.current!;
    const reduced = prefersReducedMotion();
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting && !video.src) {
          video.src = escolheSrc(video, src, srcPequeno);
          video.load();
        }
        if (reduced) return;
        if (e.isIntersecting) video.play().catch(() => {});
        else video.pause();
      },
      { rootMargin: "50% 0px" },
    );
    io.observe(video);
    return () => io.disconnect();
  }, [src, srcPequeno]);

  return <video ref={ref} muted loop playsInline preload="none" disablePictureInPicture aria-hidden className={className} />;
}
