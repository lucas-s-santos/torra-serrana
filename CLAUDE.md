# Torra Serrana — Landing 3D de café especial (portfólio)

Cafeteria/torrefação **fictícia** do Sul de Minas. Nenhuma marca real. Objetivo: vídeo vertical pro Instagram (@dev.lucassilva.ss) + portfólio.
Referência de linha visual: premium escuro alternando com creme, macros de café em tela cheia, dados de barista na tela, serifa elegante.

## Stack
- Next.js (App Router) + TypeScript + Tailwind
- GSAP + ScrollTrigger · Lenis
- Deploy: Vercel (repo: https://github.com/lucas-s-santos/torra-serrana, branch `main`; o Lucas conecta na Vercel)
- Sem lib 3D no runtime: 3D vem **renderizado do Blender** (sequência WebP com alpha num `<canvas>`) e os líquidos vêm **do Google Flow** (vídeo)

## Divisão de assets
| Fonte | Usado para | Pasta |
|---|---|---|
| Blender (`/blender/*.py`, headless) | Objetos com fundo transparente: do pé à xícara (cereja → grão → torra → pó → porta-filtro → extração → xícara com espiral), giro 360° da xícara, grãos soltos | `/public/seq/cena01/{720,960,1600}/0001–0214.webp`, `/public/seq/xicara360/{720,960,1600}/0001–0072.webp`, `/public/img/graos/` |
| Google Flow (Lucas gera, via extensão do Claude: `docs/flow-prompts.md`) | Líquidos fotorrealistas (crema, extração, leite, xícara final) e a casa/serra (torrador, fachada, balcão, encosta) | `/public/video/*.mp4`, `/public/img/casa/`, `/public/img/serra/` |

## Seções (ordem)
| # | Fundo | Conteúdo | Técnica |
|---|---|---|---|
| 1 Hero | Café `#1A110B` | Sequência Blender em 8 etapas: cereja, grão verde, torra, moagem, dose, compactação, extração, xícara. Título "Do pé à xícara." **sanduíche** (linha de cima atrás da cereja, de baixo na frente) que sobe e some; depois, legenda por etapa com dado de barista. No fim a xícara vira **giro 360°** (arrastar) | Sticky + scroll-linked (frames 1–214, ~900svh) + `<Giro360>` |
| 2 Origem | Creme `#F2EBE0` | "Toda xícara começa no pé." + anel de mancha de café em SVG que se desenha no scroll. Dados: 1.100 m · Bourbon Amarelo · colheita manual | Scroll-linked (stroke-dashoffset) |
| — Serra | Creme → foto | Foto do Flow (fachada saída 2: casa na encosta, neblina) sai de um quadro no creme e toma a tela; "A serra acorda antes da *gente.*" Degradê embaixo emenda no café da Extração | Sticky + clip-path inset + zoom lento (220svh) |
| 3 Crema | Café | `crema.mp4` (rodada 2 do Flow: gotas caindo na crema). Celular: tela cheia; desktop: metade direita de ponta a ponta, texto à esquerda (9:16 esticado na largura ficava mole). "Viva, densa, cor de *avelã.*" | Sticky + scroll-scrub |
| 4 Extração | Café | `extracao.mp4` + dados animados: **18 g · 36 g · 28 s · 9 bar · 93 °C** (contadores ligados ao scroll) | Sticky + scroll-linked |
| 5 Grãos | Creme | 3 cards com grão renderizado flutuando sobre o still life das notas (Flow, rodada 4: jasmim + pêssego, cacau + caramelo, framboesa + mel). Notas: "Jasmim · Fruta amarela", "Cacau · Caramelo", "Frutas vermelhas · Mel" | Horizontal scroll |
| 6 Leite | Café | `leite.mp4` (vídeo da "espiral" do Flow: não saiu espiral nem vista de cima, saiu o leite desenhando um coração; recortado 3:4). "Leite a 62 °C." / "Desenhado à *mão.*" | Sticky + scroll-scrub |
| 7 Citação | Café | "O primeiro gole conta a história toda." sobre a foto do pé de café com orvalho (Flow, rodada 3: 16:9 no desktop com o galho no terço esquerdo e a frase à direita; 9:16 no celular com o galho em cima) + grãos (PNG do Blender) em 3 camadas, só fora do galho | Parallax |
| 8 A casa | Creme | "Uma casa pequena na serra." Fotos do Flow (fachada, torrador, balcão), em escada | Parallax leve |
| 9 CTA | Café | `xicara-final.mp4` em loop (quadrado, vista de cima, máscara radial some no fundo). "Prove na *serra.*" + botão WhatsApp, endereço, horário | Scroll-triggered |

Os rótulos na tela ("0X —") contam só as seções numeradas: Origem 01 … CTA 08 (Serra não tem número).

Mudanças de 20/11 (rodada 1 do Flow; o site fecha com o que tem):
- **Espiral** ("28 segundos. Uma espiral perfeita."): cortada, o hero já termina na espiral 3D. O vídeo dela virou a seção **Leite**.
- **Crema**: a 1ª veio com "grãos" boiando; a rodada 2 (gotas caindo) entrou no mesmo dia, entre Serra e Extração.

## Direção visual
- Cores: café `#1A110B` · creme `#F2EBE0` · caramelo `#C8925A` (detalhes, números) · cereja `#B5462F` (só na seção 1 e numa palavra de destaque)
- Tipo: **Fraunces** (títulos grandes, itálico pontual numa palavra) + **Geist** (corpo) + **Geist Mono** (dados técnicos)
- Grão de filme sutil (overlay SVG noise, opacity ~0.06)
- **Logo (grão-serra, escolhida pelo Lucas em 20/11):** grão de café com a crista da serra no lugar da fenda, ao lado de "Torra Serrana" em Fraunces. `<Grao>` em `src/components/Logo.tsx`: uma cor só (`currentColor`) com a crista vazada por `<mask>`, porque o header usa `mix-blend-difference`; na abertura a crista se desenha (`.crista` no globals.css). Colorida (caramelo + café) no `icon.svg` e no `opengraph-image.jpg` (prévia do link, 1200×630, gerada de um HTML com o frame 214)
- Copy curta, em português, primeira pessoa do plural
- **Proibido:** gradiente roxo, glassmorphism, ícones genéricos em cards, emojis, "Bem-vindo", lorem ipsum

## Técnicas (detalhes)
- **Sequência de imagens** `<ImageSequence src count />`: canvas sticky, ScrollTrigger `scrub: true` → índice do frame (`hold` = trecho final parado). Frames baixados como Blob e decodificados em `ImageBitmap` só numa janela em volta do frame atual (`src/lib/frames.ts`): tudo decodificado passaria de 1 GB no celular. 1º frame logo, 20 depois do load, o resto em background. Respeitar DPR e redesenhar no resize.
- **Giro 360°** `<Giro360>`: 72 ângulos renderizados no mesmo enquadramento do último frame da sequência (ângulo 0 == frame 214). Arraste com inércia, gira sozinho devagar, setas no teclado; ao rolar de volta, volta pro 0 antes de devolver pra sequência.
  - Frames **recortados na caixa da xícara** (`CORTE=210:470:1180:760` no `to_webp.sh`, mesma caixa em `CORTE_GIRO` no Hero) e **todos decodificados** de uma vez (~90 MB no celular). A janela deslizante fazia a xícara sumir num arraste rápido (32% dos quadros em branco no teste) e travar.
  - Crossfade entre ângulos vizinhos (composição `lighter`): sem ele os passos de 5° davam tranco no giro lento. Parado, assenta no ângulo inteiro (senão a alça aparece dobrada). Nunca apaga o canvas se o frame não chegou.
- **Sanduíche de tipografia:** título em duas camadas idênticas; a de trás fica sob o canvas e mostra só a 1ª linha, a da frente só a 2ª. Cada linha fica inteira de um lado do objeto. **Não** cortar letra ao meio com `clip-path` (parece bug: foi o que o Lucas reclamou).
- **Scroll-scrub de vídeo:** o vídeo PRECISA ser reencodado com keyframe em todo frame, senão trava:
  `ffmpeg -i in.mp4 -an -c:v libx264 -g 1 -crf 22 -pix_fmt yuv420p -movflags +faststart out.mp4`
  Controlar `video.currentTime` via ScrollTrigger com rAF. No mobile, se travar, usar sequência WebP.
- **Contadores:** valores interpolados pelo progress do ScrollTrigger, números em Geist Mono com `tabular-nums`.
- `prefers-reduced-motion`: frames finais estáticos, vídeos pausados.
- Lighthouse mobile ≥ 90; vídeos ≤ 4 MB cada (e `-sm` ≤ 2 MB); `loading="lazy"` / preload só do hero.
- **Peso:** o celular comum (390 px, DPR 2) usa os frames de 720; desktop DPR 1, 960; retina, 1600. Vídeos: `srcPequeno` no `<ScrubVideo>`/`<LoopVideo>` troca pelo `-sm` de 720 px quando o lado menor do vídeo na tela × DPR ≤ 800 (`src/lib/video.ts`): celular e quase todo desktop sem retina. Rolando a página inteira: ~12 MB no celular, ~14 MB no desktop DPR 1, ~25 MB no retina.

## Blender (pipeline)
- Scripts em `/blender/`. Requer Blender ≥ 4.2 no PATH.
- Teste rápido: `blender -b -P blender/cena01_do_pe_a_xicara.py -- --engine EEVEE --res 480 --samples 16 --frames 1,70,100,180,214 --out blender/test/` (`--frames` aceita faixas: `71-214`)
- Final: `blender -b -P blender/cena01_do_pe_a_xicara.py -- --engine EEVEE --res 1600 --out blender/out/cena01/` (~20 s/frame; 71–214 levou 48 min)
- Giro 360°: `... -- --engine EEVEE --res 1600 --giro 72 --out blender/out/xicara360/` (23 min); converter com `CORTE=210:470:1180:760 bash blender/to_webp.sh blender/out/xicara360 public/seq/xicara360` (se mudar câmera/xícara, recalcular a caixa pelo alpha dos 72 PNGs)
- Converter pra WebP com alpha: `for f in blender/out/cena01/*.png; do cwebp -q 82 -alpha_q 90 "$f" -o "public/seq/cena01/$(basename "${f%.png}").webp"; done`
  - Sem `cwebp` nesta máquina → `BORDA=0.07 bash blender/to_webp.sh blender/out/cena01 public/seq/cena01 44-52` (ffmpeg; gera 720, 960 e 1600 px com qualidade 75, ~25% menor que 85 sem diferença visível; `SIZES=720` gera um tamanho só; o 3º arg é a faixa do fade, onde o alpha é suavizado/quantizado pra não pesar ~300 KB/frame; `BORDA` esmaece as bordas do quadro, porque no desktop o quadrado fica no meio da tela e objeto entrando por fora apareceria cortado em linha reta)
- Nesta máquina o Blender não está no PATH: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"`. Rodar sempre da raiz do projeto.
- Ajustes de cor, timing e câmera ficam no topo do script. Sempre renderizar teste antes do final.

## Scripts
- Vídeos do Flow: prompt pronto pra extensão do Claude em `docs/flow-prompts.md`. Originais em `flow/originais/` (fora do `public/`, no `.gitignore`); o corte/recorte vai pra `flow/raw/<nome>.mp4` e `bash scripts/videos.sh` gera `public/video/` (sem áudio, `-g 1`, ≤ 4 MB; cai pra 720 se precisar) e o `<nome>-sm.mp4` de 720 px (≤ 2 MB) pro celular.
  - Rodada 1 (20/11): entraram `extracao` (corte a partir de 2,0 s + recorte 3:4, `crop=1080:1440:0:240`), `xicara-final` (de 2,0 s, `crop=1080:1080:0:500`, loop com crossfade de 1 s) e as fotos da casa (torrador = recorte 1200×1600 em x 330, y 600 da saída alternativa do balcão). Depois, reaproveitados: `leite` (o vídeo da espiral inteiro, `crop=1080:1440:0:280`, CRF 30 pra caber em 4 MB) e a saída 2 da fachada como `serra-1200.webp` (3:4, celular) + `serra-larga.webp` (`crop=1792:1100:0:380`, desktop). Crema reprovada ("grãos" no meio de tudo, não tem recorte que salve); torrador em vídeo não gerado.
  - Rodada 2 (20/11): `crema` (gotas na crema) a partir do frame 18, sem recorte, CRF 30. Original em `flow/originais/A1-crema-r2.mp4`.
  - Rodada 3 (20/11): pé de café (Nano Banana Pro, 2K, 0 crédito) → `public/img/cerejas/` (`cerejas-{1280,1920}.webp` 16:9 e `cerejas-alta-1080.webp` 9:16, WebP q88: em q78 o fundo escuro fazia faixas).
  - Rodada 4 (21/11): notas de sabor dos lotes (3:4, fundo creme) → `python scripts/fundo_branco.py flow/originais/C4-loteN-*.jpg public/img/graos/notas-N.webp`: o fundo vira branco puro (superfície polinomial ajustada fora do arranjo) e o card aplica `mix-blend-multiply`, então o fundo some na cor do card. O card precisa de fundo **opaco**: o trilho tem `will-change` e isola a mistura.
  - `blender/cena02_crema.py`: tentativa de crema no Blender (20/11), não chegou no nível do Flow e não é usada. Cada render no EEVEE recompila o shader (~40 s fixos): se for usar, renderizar numa chamada só de animação.
- Fraunces enxuto (peso 400 + SOFT 50 fixos, só `opsz` variável, 70 KB): `python scripts/fraunces.py <Regular-var.woff2> <Italic-var.woff2>` → `src/app/fonts/` (precisa de fonttools + brotli).

## Regras
- Componentes pequenos, sem dependência desnecessária
- Enquanto faltar asset: placeholders (frames numerados, vídeo de cor sólida)
- Antes de decisões grandes de design ou arquitetura, perguntar ao Lucas

## Ordem de trabalho
1. Setup + tokens + fontes + Lenis
2. `<ImageSequence />` com a cena 01 renderizada (rodar o Blender)
3. Seções 1–8 com placeholders de vídeo
4. Trocar pelos vídeos do Flow (reencodados)
5. Polimento das animações de texto, mobile, deploy
