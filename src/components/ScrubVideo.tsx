"use client";

import { useEffect, useRef, type RefObject } from "react";
import { gsap } from "@/lib/gsap";
import { useScrollProgress } from "@/lib/useScrollProgress";
import { prefersReducedMotion } from "@/lib/useReducedMotion";
import { escolheSrc } from "@/lib/video";

type Props = {
  /** precisa ter keyframe em todo frame (ffmpeg -g 1), senão o seek trava */
  src: string;
  /** versão de 720 px (<nome>-sm.mp4), usada quando o vídeo aparece pequeno: ver escolheSrc */
  srcPequeno?: string;
  /** seção que dirige o vídeo (normalmente a seção sticky que o contém) */
  trigger: RefObject<HTMLElement | null>;
  start?: string;
  end?: string;
  /** ponto (0–1) mostrado parado com reduced-motion */
  still?: number;
  className?: string;
};

/** Vídeo cujo tempo segue o scroll. Só baixa quando a seção chega perto. */
export function ScrubVideo({ src, srcPequeno, trigger, start, end, still = 0.6, className = "" }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const target = useRef(0);

  useScrollProgress(trigger, (p) => (target.current = p), { start, end });

  useEffect(() => {
    const video = videoRef.current!;
    const section = trigger.current!;
    const reduced = prefersReducedMotion();
    let ready = false;

    const io = new IntersectionObserver(
      ([e]) => {
        if (!e.isIntersecting || video.src) return;
        video.src = escolheSrc(video, src, srcPequeno);
        video.load();
        io.disconnect();
      },
      { rootMargin: "150% 0px" },
    );
    io.observe(section);

    const onMeta = () => {
      ready = true;
      // iOS só pinta frames de seek depois de um play() (mudo é permitido)
      video.play().then(() => video.pause(), () => {});
      if (reduced) video.currentTime = still * video.duration;
    };
    video.addEventListener("loadedmetadata", onMeta);

    const tick = () => {
      if (!ready || reduced || video.seeking) return;
      const t = target.current * (video.duration - 0.05);
      if (Math.abs(video.currentTime - t) > 1 / 60) video.currentTime = t;
    };
    gsap.ticker.add(tick);

    return () => {
      io.disconnect();
      video.removeEventListener("loadedmetadata", onMeta);
      gsap.ticker.remove(tick);
    };
  }, [src, srcPequeno, trigger, still]);

  return <video ref={videoRef} muted playsInline preload="auto" disablePictureInPicture aria-hidden className={className} />;
}
