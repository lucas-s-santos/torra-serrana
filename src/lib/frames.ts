/**
 * Frames de uma sequência guardados comprimidos (Blob, ~25 KB) e decodificados em ImageBitmap só numa janela
 * em volta do frame atual. Decodificar tudo de uma vez custaria ~4 MB por frame de 960 px: 286 frames
 * passariam de 1 GB e o Safari do iPhone derruba a aba bem antes disso.
 */
export type FrameStore = {
  /** frame decodificado mais próximo de i (pode ser outro enquanto o certo ainda decodifica) */
  nearest(i: number): ImageBitmap | undefined;
  has(i: number): boolean;
  /** move a janela de decodificação pra perto de i (a direção do movimento ganha mais frames à frente) */
  focus(i: number): void;
  /** baixa os frames na ordem dada, `parallel` por vez */
  load(order: number[], parallel?: number): Promise<void>;
  dispose(): void;
};

type Options = {
  /** frames decodificados à frente e atrás da direção do movimento */
  ahead: number;
  behind: number;
  /** giro 360: o frame depois do último é o primeiro */
  circular?: boolean;
  onDecoded?: () => void;
};

export function frameStore(count: number, url: (i: number) => string, { ahead, behind, circular = false, onDecoded }: Options): FrameStore {
  const blobs: (Blob | undefined)[] = new Array(count);
  const bitmaps = new Map<number, ImageBitmap>();
  const pending = new Set<number>();
  let center = 0;
  let dir = 1;
  let alive = true;

  const wrap = (i: number) => ((i % count) + count) % count;
  const delta = (i: number) => {
    if (!circular) return i - center;
    const d = wrap(i - center);
    return d > count / 2 ? d - count : d;
  };
  const inWindow = (i: number) => {
    const d = delta(i) * dir;
    return d >= -behind && d <= ahead;
  };

  const decode = (i: number) => {
    const blob = blobs[i];
    if (!blob || bitmaps.has(i) || pending.has(i)) return;
    pending.add(i);
    createImageBitmap(blob).then(
      (bm) => {
        pending.delete(i);
        if (!alive || !inWindow(i)) return bm.close();
        bitmaps.set(i, bm);
        onDecoded?.();
      },
      () => pending.delete(i),
    );
  };

  const sweep = () => {
    for (const [i, bm] of bitmaps) {
      if (!inWindow(i)) {
        bm.close();
        bitmaps.delete(i);
      }
    }
    // de perto pra longe, à frente primeiro
    for (let d = 0; d <= Math.max(ahead, behind); d++) {
      for (const s of d ? [d * dir, -d * dir] : [0]) {
        if ((s * dir > 0 && d > ahead) || (s * dir < 0 && d > behind)) continue;
        const i = circular ? wrap(center + s) : center + s;
        if (i >= 0 && i < count) decode(i);
      }
    }
  };

  return {
    has: (i) => bitmaps.has(i),
    nearest(i) {
      const exact = bitmaps.get(i);
      if (exact) return exact;
      let best: ImageBitmap | undefined;
      let bestD = Infinity;
      for (const [j, bm] of bitmaps) {
        const d = Math.abs(circular ? delta(j) - delta(i) : j - i);
        if (d < bestD) [best, bestD] = [bm, d];
      }
      return best;
    },
    focus(i) {
      if (i !== center) dir = delta(i) > 0 ? 1 : -1;
      center = i;
      sweep();
    },
    async load(order, parallel = 4) {
      let next = 0;
      const worker = async () => {
        while (alive && next < order.length) {
          const i = order[next++];
          if (blobs[i]) continue;
          try {
            const res = await fetch(url(i), { priority: "low" } as RequestInit);
            if (res.ok) blobs[i] = await res.blob();
          } catch {}
          if (alive && inWindow(i)) decode(i);
        }
      };
      await Promise.all(Array.from({ length: parallel }, worker));
    },
    dispose() {
      alive = false;
      for (const bm of bitmaps.values()) bm.close();
      bitmaps.clear();
    },
  };
}

/** maior largura da lista que ainda cobre o canvas (com DPR até 2); mobile não decodifica 1600² */
export function pickSize(sizes: number[], canvas: HTMLCanvasElement, fit: "contain" | "cover" = "contain") {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const need = (fit === "cover" ? Math.max : Math.min)(canvas.clientWidth, canvas.clientHeight) * dpr;
  return sizes.find((s) => s >= need * 0.9) ?? sizes[sizes.length - 1];
}

/** janela de decodificação pelo tamanho do frame: ~150–250 MB de bitmaps no máximo */
export const janela = (size: number) => (size >= 1600 ? { ahead: 14, behind: 6 } : { ahead: 28, behind: 10 });

export const frameUrl = (src: string, size: number, i: number, ext = "webp") =>
  `${src}/${size}/${String(i + 1).padStart(4, "0")}.${ext}`;

/** desenha o bitmap centralizado (contain/cover) no canvas inteiro */
export function draw(ctx: CanvasRenderingContext2D, img: ImageBitmap | undefined, fit: "contain" | "cover" = "contain") {
  const { canvas } = ctx;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!img) return;
  const s = (fit === "cover" ? Math.max : Math.min)(canvas.width / img.width, canvas.height / img.height);
  const w = img.width * s;
  const h = img.height * s;
  ctx.drawImage(img, (canvas.width - w) / 2, (canvas.height - h) / 2, w, h);
}

/** canvas no tamanho do elemento × DPR (até 2) */
export function fitCanvas(canvas: HTMLCanvasElement) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(canvas.clientWidth * dpr);
  canvas.height = Math.round(canvas.clientHeight * dpr);
  const ctx = canvas.getContext("2d")!;
  ctx.imageSmoothingQuality = "high";
  return ctx;
}
