# Torra Serrana

Landing page de uma torrefação de cafés especiais do Sul de Minas. A marca é **fictícia**: projeto de portfólio de [@dev.lucassilva.ss](https://instagram.com/dev.lucassilva.ss).

O site conta o caminho do café, do pé à xícara, no ritmo do scroll: uma sequência 3D renderizada no Blender (cereja → grão → torra → moagem → extração → xícara), que termina numa xícara que gira com o dedo, e vídeos de líquido fotorrealistas gerados no Google Flow.

## Stack

- Next.js (App Router) + TypeScript + Tailwind CSS
- GSAP + ScrollTrigger, Lenis
- Nenhuma biblioteca 3D no navegador: o 3D chega como sequência de WebP com transparência, desenhada num `<canvas>`

## Rodar

```bash
pnpm install
pnpm dev      # http://localhost:3000
pnpm build
```

## Como foi feito

| Parte | Técnica |
|---|---|
| Hero "Do pé à xícara" | 214 frames do Blender (`public/seq/cena01/{720,960,1600}`) num canvas sticky. Os frames ficam guardados comprimidos e só uma janela em volta do frame atual é decodificada, porque tudo aberto passaria de 1 GB no celular |
| Xícara 360° | 72 ângulos recortados na caixa da xícara, todos decodificados, com crossfade entre ângulos vizinhos. Arraste com inércia, teclado e giro automático |
| Crema, extração e leite | Vídeos com keyframe em todo frame (`-g 1`), com o tempo controlado pelo scroll. Versão de 720 px no celular |
| Fotos | Geradas no Google Flow. As notas de sabor dos lotes têm o fundo achatado pra branco e entram no card com `mix-blend-multiply` |
| Logo | SVG de uma cor só, com a crista da serra vazada no grão. Ela se desenha quando a página abre |

Scripts do pipeline:

- `blender/*.py`: cenas renderizadas sem interface (`blender -b -P ...`)
- `blender/to_webp.sh`: PNG para WebP com transparência, em 3 larguras
- `scripts/videos.sh`: vídeos para scroll, sem áudio, com no máximo 4 MB (2 MB na versão de celular)
- `scripts/fundo_branco.py`: deixa branco o fundo das fotos de still life
- `docs/flow-prompts.md`: os prompts usados no Google Flow

`prefers-reduced-motion` é respeitado: a sequência e os vídeos ficam parados no quadro final.
