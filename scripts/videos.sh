#!/usr/bin/env bash
# Vídeos do Google Flow -> versão de site: sem áudio, keyframe em TODO frame (scroll-scrub não trava),
# no máximo 1080 px no lado menor e <= 4 MB (sobe o CRF até caber).
# Gera também <nome>-sm.mp4 (720 px no lado menor, <= 2 MB) pro layout de celular: os componentes trocam pelo -sm
# abaixo de 768 px, onde o vídeo aparece pequeno (ou é macro desfocado) e 1080 seria peso à toa.
# Uso: bash scripts/videos.sh            (processa flow/raw/*.mp4: originais já cortados/recortados)
#      bash scripts/videos.sh crema      (só um)
set -euo pipefail
RAW=${RAW:-flow/raw}
OUT=${OUT:-public/video}
MAX_BYTES=$((4 * 1024 * 1024))
MAX_SM=$((2 * 1024 * 1024))

shopt -s nullglob
files=("$RAW"/${1:-*}.mp4)
(( ${#files[@]} )) || { echo "nada em $RAW/${1:-*}.mp4"; exit 1; }

for src in "${files[@]}"; do
  name=$(basename "$src" .mp4)
  out="$OUT/$name.mp4"
  # xicara-final e casa-* tocam em loop (não é scrub): GOP normal fica bem menor
  [[ $name == xicara-final* || $name == casa-* ]] && gop=30 || gop=1
  # tenta 1080 no lado menor; se nem CRF 30 couber em 4 MB, cai pra 720
  done_=0
  for lado in 1080 720; do
    for crf in 22 24 26 28 30; do
      ffmpeg -hide_banner -loglevel error -y -i "$src" -an         -vf "scale='if(lt(iw,ih),min($lado,iw),-2)':'if(lt(iw,ih),-2,min($lado,ih))':flags=lanczos"         -c:v libx264 -preset slow -g $gop -crf $crf -pix_fmt yuv420p -movflags +faststart "$out"
      size=$(stat -c %s "$out")
      if (( size <= MAX_BYTES )); then done_=1; break 2; fi
    done
  done
  dims=$(ffprobe -v error -select_streams v -show_entries stream=width,height,duration -of csv=p=0 "$out")
  printf "%-22s crf %-2s gop %-2s %5s KB  %s
" "$name.mp4" $crf $gop $(( size / 1024 )) "$dims"
  if (( ! done_ )); then echo "  ! ainda acima de 4 MB mesmo em 720: cortar a duração"; fi

  sm="$OUT/$name-sm.mp4"
  for crf in 24 26 28 30; do
    ffmpeg -hide_banner -loglevel error -y -i "$src" -an       -vf "scale='if(lt(iw,ih),min(720,iw),-2)':'if(lt(iw,ih),-2,min(720,ih))':flags=lanczos"       -c:v libx264 -preset slow -g $gop -crf $crf -pix_fmt yuv420p -movflags +faststart "$sm"
    size=$(stat -c %s "$sm")
    (( size <= MAX_SM )) && break
  done
  dims=$(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0 "$sm")
  printf "%-22s crf %-2s gop %-2s %5s KB  %s
" "$name-sm.mp4" $crf $gop $(( size / 1024 )) "$dims"
done
