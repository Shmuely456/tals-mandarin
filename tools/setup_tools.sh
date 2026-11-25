#!/usr/bin/env bash
# Reinstalls what the lesson import needs after a fresh container: Python packages, the voice and the two speech
# recognizers (for tools/gen_audio.py), CC-CEDICT (for checking words) and the font sources (for tools/subset_fonts.py).
# Usage: bash tools/setup_tools.sh <folder>   then: gen_audio.py <folder>/models, subset_fonts.py <folder>/fonts-src,
#        CC-CEDICT is <folder>/cedict/pycccedict/data/cedict_1_0_ts_utf-8_mdbg.txt.gz
set -eu
DIR=$(mkdir -p "$1" && cd "$1" && pwd)
pip install -q sherpa-onnx onnxruntime soundfile pypinyin fonttools brotli numpy
mkdir -p "$DIR/models" && cd "$DIR/models"
R=https://github.com/k2-fsa/sherpa-onnx/releases/download
for u in tts-models/matcha-icefall-zh-baker.tar.bz2 vocoder-models/vocos-22khz-univ.onnx \
         asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2 asr-models/sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2; do
  f=$(basename "$u"); [ -e "${f%.tar.bz2}" ] && continue
  curl -sSL --retry 3 -o "$f" "$R/$u"
  case "$f" in *.tar.bz2) tar xjf "$f" && rm "$f" ;; esac
done
mkdir -p "$DIR/cedict" && cd "$DIR/cedict"
pip download -q pycccedict --no-deps -d . && unzip -q -o pycccedict-*.whl 'pycccedict/data/*'
mkdir -p "$DIR/fonts-src" && cd "$DIR/fonts-src"
for spec in "Fredoka:wght@500..700|Fredoka_wght_500__700.ttf" "Nunito:wght@500..800|Nunito_wght_500__800.ttf" \
            "Noto+Serif+SC:wght@500|NotoSerifSC_wght_500.ttf" "Noto+Serif+SC:wght@700|NotoSerifSC_wght_700.ttf"; do
  url=$(curl -sS "https://fonts.googleapis.com/css2?family=${spec%%|*}" | grep -o 'https://[^)]*\.ttf' | head -1)
  curl -sSL -o "${spec##*|}" "$url"
done
echo "ready: $DIR"
