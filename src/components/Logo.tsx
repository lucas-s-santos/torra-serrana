import type { CSSProperties } from "react";

/** Crista da serra no lugar da fenda do grão (coordenadas do grão deitado, antes de girar). */
const CRISTA = "M-24 5.5 L-21 3.2 L-11.5 -5.5 L-6.5 -1.2 L1.8 -9.5 L10.5 -0.5 L14 -3.2 L24 5.5";

type Props = {
  /** id do <mask> (único por página: o grão aparece no header e no rodapé) */
  id: string;
  /** desenha a crista ao carregar (abertura do site) */
  anima?: boolean;
  className?: string;
  style?: CSSProperties;
};

/**
 * Marca da Torra Serrana: grão de café com a crista da serra no lugar da fenda.
 * Uma cor só (currentColor), com a crista vazada: funciona sob o mix-blend-difference do header.
 */
export function Grao({ id, anima = false, className = "", style }: Props) {
  return (
    <svg viewBox="-24 -24 48 48" className={className} style={style} aria-hidden>
      <mask id={id}>
        <g transform="rotate(-14)">
          <ellipse rx="21.5" ry="15.5" fill="#fff" />
          <path
            d={CRISTA}
            pathLength={1}
            fill="none"
            stroke="#000"
            strokeWidth="2.8"
            strokeLinejoin="round"
            strokeLinecap="round"
            className={anima ? "crista" : undefined}
          />
        </g>
      </mask>
      <rect x="-24" y="-24" width="48" height="48" fill="currentColor" mask={`url(#${id})`} />
    </svg>
  );
}
