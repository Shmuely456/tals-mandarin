"""Generate Mandarin audio clips for words and sentence tiles that don't have one yet.

Usage (from the repo root):  python3 tools/gen_audio.py <models folder>
Needs:  pip install sherpa-onnx soundfile numpy, and ffmpeg.
Model:  https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_1.tar.bz2
        (unpack into <models folder>/kokoro-multi-lang-v1_1)
Writes audio/zhNNN.m4a and updates content/audio.json (text -> file).
Voice 55 scored best on a speech-recognizer check of tones and sounds; keep it so all clips match.
"""
import json, os, subprocess, sys
import numpy as np
import sherpa_onnx
import soundfile as sf

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(sys.argv[1], 'kokoro-multi-lang-v1_1')
VOICE = 55
items = json.load(open(os.path.join(root, 'content', 'items.json'), encoding='utf-8'))
amap_path = os.path.join(root, 'content', 'audio.json')
amap = json.load(open(amap_path, encoding='utf-8')) if os.path.exists(amap_path) else {}
texts = []
for it in items:
    for t in [it.get('hanzi')] + [tok.get('h') for tok in it.get('tokens') or []]:
        if t and t not in amap and t not in texts:
            texts.append(t)
if not texts:
    sys.exit('every text already has a clip')

tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
    model=sherpa_onnx.OfflineTtsModelConfig(
        kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
            model=f'{K}/model.onnx', voices=f'{K}/voices.bin', tokens=f'{K}/tokens.txt',
            data_dir=f'{K}/espeak-ng-data', dict_dir=f'{K}/dict', lexicon=f'{K}/lexicon-us-en.txt,{K}/lexicon-zh.txt'),
        num_threads=4),
    rule_fsts=f'{K}/date-zh.fst,{K}/phone-zh.fst,{K}/number-zh.fst',
    max_num_sentences=1))

def clean(samples, rate):
    """Trim silence at both ends, leave a little air, and even out the volume."""
    x = np.nan_to_num(np.asarray(samples, dtype=np.float32))
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > 0:
        env = np.convolve(np.abs(x), np.ones(int(0.02 * rate)) / int(0.02 * rate), mode='same')
        loud = np.flatnonzero(env > peak * 0.06)
        x = x[max(0, loud[0] - int(0.02 * rate)):loud[-1] + int(0.04 * rate)] / peak * 0.89
    return np.concatenate([np.zeros(int(0.06 * rate), np.float32), x, np.zeros(int(0.15 * rate), np.float32)])

used = {int(f[2:5]) for f in os.listdir(os.path.join(root, 'audio')) if f.startswith('zh') and f.endswith('.m4a')}
n = max(used or {0})
for text in texts:
    short = sum(1 for c in text if '一' <= c <= '鿿') <= 2
    spoken = text if text[-1] in '。？！?!.' else text + '。'
    audio = tts.generate(spoken, sid=VOICE, speed=0.85 if short else 0.9)
    wav = os.path.join(root, 'audio', 'tmp.wav')
    sf.write(wav, clean(audio.samples, audio.sample_rate), audio.sample_rate)
    n += 1
    name = 'audio/zh%03d.m4a' % n
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-ac', '1', '-ar', '24000', '-c:a', 'aac', '-b:a', '80k', '-movflags', '+faststart', os.path.join(root, name)], check=True)
    os.remove(wav)
    amap[text] = name
    print(name, text)
json.dump(amap, open(amap_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
