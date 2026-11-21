#!/usr/bin/env bash
# PNG (Blender) -> WebP com alpha, em vários tamanhos.
# Uso: bash blender/to_webp.sh blender/out/cena01 public/seq/cena01 44-52
#   3º arg (opcional): faixa de frames com fade de alpha (EEVEE dithered gera ruído no alpha,
#   que o WebP guarda sem perda: ~300 KB/frame). Nessa faixa o alpha leva blur leve + quantização
#   em 16 níveis (equivalente ao -alpha_q do cwebp): ~45 KB/frame.
#   BORDA=0.07 (env, opcional): esmaece o alpha nas bordas (fração do lado). No desktop o quadro quadrado
#   fica no meio da tela: objeto entrando por fora dele apareceria cortado numa linha reta.
#   CORTE=x:y:w:h (env, opcional, em px do PNG de 1600): recorta só a caixa do objeto (giro 360: a xícara ocupa ~1/3
#   do quadro, e o giro decodifica os 72 ângulos de uma vez). Saída: (w × size/1600) px de largura.
set -euo pipefail
IN=${1:?pasta com 0001.png...}
OUT=${2:?pasta destino}
FADE=${3:-}
BORDA=${BORDA:-0}
CORTE=${CORTE:-}
SIZES=(${SIZES:-720 960 1600})   # SIZES="720" (env) gera só esse tamanho
Q=${Q:-75}   # 75: ~25% menor que 85 e indistinguível no frame (testado no 0120, o mais detalhado)

fade_ini=0; fade_fim=-1
if [[ -n $FADE ]]; then fade_ini=${FADE%-*}; fade_fim=${FADE#*-}; fi

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for size in "${SIZES[@]}"; do
  mkdir -p "$OUT/$size"
  if [[ $BORDA != 0 ]]; then   # máscara cinza: 1 no miolo, smoothstep até 0 na borda
    b="($BORDA*$size)"
    ffmpeg -hide_banner -loglevel error -y -f lavfi -i "color=white:s=${size}x${size},format=gray" -frames:v 1 \
      -vf "geq=lum='255*(st(0,min(1,min(X,W-1-X)/$b))*0+ld(0)*ld(0)*(3-2*ld(0)))*(st(1,min(1,min(Y,H-1-Y)/$b))*0+ld(1)*ld(1)*(3-2*ld(1)))'" \
      "$tmp/borda_$size.png"
  fi
done

for png in "$IN"/[0-9][0-9][0-9][0-9].png; do
  name=$(basename "$png" .png); n=$((10#$name))
  for size in "${SIZES[@]}"; do
    [[ "$OUT/$size/$name.webp" -nt "$png" ]] && continue   # já convertido e o PNG não mudou
    # escala ANTES de quantizar: o lanczos depois recriaria os níveis intermediários (e o peso)
    if [[ -n $CORTE ]]; then
      IFS=: read -r cx cy cw ch <<< "$CORTE"
      vf="[0]crop=$cw:$ch:$cx:$cy,scale=$((cw * size / 1600)):-1:flags=lanczos,format=rgba,split[c][a];[a]alphaextract"
    else
      vf="[0]scale=$size:-1:flags=lanczos,format=rgba,split[c][a];[a]alphaextract"
    fi
    (( n >= fade_ini && n <= fade_fim )) && vf+=",gblur=sigma=1.0,lut=y='min(255,floor(val/16+0.5)*16)'"
    if [[ $BORDA != 0 ]]; then
      vf+="[al];[al][1]blend=all_mode=multiply[am];[c][am]alphamerge"
      extra=(-i "$tmp/borda_$size.png")
    else
      vf+="[am];[c][am]alphamerge"
      extra=()
    fi
    ffmpeg -hide_banner -loglevel error -y -i "$png" "${extra[@]}" -filter_complex "$vf" \
      -c:v libwebp -quality $Q -compression_level 6 -pix_fmt yuva420p "$OUT/$size/$name.webp"
  done
done
for size in "${SIZES[@]}"; do
  echo "$size px: $(ls "$OUT/$size" | wc -l) frames, $(du -sh "$OUT/$size" | cut -f1)"
done
