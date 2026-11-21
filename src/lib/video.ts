/**
 * Escolhe entre o vídeo cheio (1080) e a versão de 720 px (`<nome>-sm.mp4`, scripts/videos.sh) pelo tamanho em que
 * o vídeo aparece: se o lado menor do elemento, em pixels de tela (DPR até 2), cabe em ~800, o de 720 basta.
 * Celular, e desktop sem retina na maioria dos casos, baixam metade dos bytes.
 */
export function escolheSrc(el: HTMLElement, src: string, srcPequeno?: string) {
  if (!srcPequeno) return src;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  return Math.min(el.clientWidth, el.clientHeight) * dpr <= 800 ? srcPequeno : src;
}
