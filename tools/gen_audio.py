"""Generate Mandarin audio clips for words and sentence tiles, and check each one with two speech recognizers.

Usage (from the repo root):
    python3 tools/gen_audio.py <models folder>          clips for new words and sentences only
    python3 tools/gen_audio.py <models folder> --all    every clip again (new file names; old files are removed)
    python3 tools/gen_audio.py <models folder> --redo 的 李月是汉语老师。    just these clips again
Needs:  pip install onnxruntime sherpa-onnx pypinyin numpy soundfile, and ffmpeg.
Models (into <models folder>; unpack the .tar.bz2 files):
    https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/matcha-icefall-zh-baker.tar.bz2
    https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/vocos-22khz-univ.onnx
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2
Writes audio/zhNNN.m4a and updates content/audio.json (text -> file).

Why this voice and method:
- The voice is Matcha-TTS trained on the Baker corpus (标贝): 12 hours of a professional female speaker reading standard
  Putonghua. Its tones follow the textbook shapes (1st high and level, 2nd rising, 3rd low, 4th falling). The Kokoro
  voice used before blurred the 1st tone with the 4th and the 2nd with the 3rd, and hummed an "ooh" before short words.
  The Baker data is licensed for non-commercial use only, which fits this personal app.
- The voice was trained on its own dictionary's readings (lexicon.txt, e.g. 学生 xue2 sheng1 for the natural xuésheng),
  so it gets those, matched longest word first. Where the app's pinyin names a different syllable for a character
  (one with two readings), the app's pinyin wins. Then the tone changes of spoken Mandarin: 3rd + 3rd tone (很好 hén hǎo)
  and 不 before a 4th tone (不是 bú shì), as the dictionary itself does (你好 ni2 hao3).
- The voice varies a little from take to take. Each take is transcribed by two recognizers and kept once both hear
  the right syllables and tones; after 12 takes the best one is kept and flagged to check by ear.
"""
import json, os, subprocess, sys
import numpy as np
import onnxruntime as ort
import sherpa_onnx
import soundfile as sf
from pypinyin import lazy_pinyin, Style

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = sys.argv[1]
EVERY = '--all' in sys.argv[2:]
REDO = sys.argv[sys.argv.index('--redo') + 1:] if '--redo' in sys.argv else []
RATE, TAKES = 22050, 12
PUNCT = {'，': ',', '、': ',', '；': ',', '。': '.', '？': '?', '！': '!', '：': ':', ',': ',', '.': '.', '?': '?', '!': '!'}
is_han = lambda c: '一' <= c <= '鿿'
tone = lambda s: int(s[-1]) if s[-1].isdigit() else 5
base = lambda s: s.rstrip('012345').replace('ü', 'v')

items = json.load(open(os.path.join(root, 'content', 'items.json'), encoding='utf-8'))
amap_path = os.path.join(root, 'content', 'audio.json')
amap = {} if EVERY or not os.path.exists(amap_path) else json.load(open(amap_path, encoding='utf-8'))
replaced = [amap.pop(t) for t in REDO if t in amap]

# Each text with its syllables, from the item that teaches it; a word's own item wins over its use in a sentence.
reading = {}
for it in sorted(items, key=lambda it: it['type'] == 'word', reverse=True):
    han = [c for c in it['hanzi'] if is_han(c)]
    if len(han) != len(it.get('syl') or []):
        sys.exit('%s: %d characters but %d syllables in syl' % (it['hanzi'], len(han), len(it.get('syl') or [])))
    reading.setdefault(it['hanzi'], it['syl'])
for it in items:
    han, pos = [c for c in it['hanzi'] if is_han(c)], 0
    for t in it.get('tokens') or []:
        h = [c for c in t['h'] if is_han(c)]
        k = next((i for i in range(pos, len(han) - len(h) + 1) if han[i:i + len(h)] == h), None)
        if k is None:
            sys.exit('%s: tile %s is not in the sentence' % (it['hanzi'], t['h']))
        reading.setdefault(t['h'], it['syl'][k:k + len(h)])
        pos = k + len(h)
texts = [t for t in reading if t not in amap]
if not texts:
    sys.exit('every text already has a clip')

B = os.path.join(MODELS, 'matcha-icefall-zh-baker')
lexicon = {}
for line in open(os.path.join(B, 'lexicon.txt'), encoding='utf-8'):
    p = line.split()
    if len(p) >= 2 and p[0] not in lexicon:
        lexicon[p[0]] = p[1:]
tok = {}
for line in open(os.path.join(B, 'tokens.txt'), encoding='utf-8'):
    line = line.rstrip('\n')
    if line:
        sym, i = line.rsplit(' ', 1)
        tok[sym or ' '] = int(i)


def symbols(text, syls):
    """The voice's input for a text: its dictionary's readings, the app's syllable where they differ, spoken tone changes."""
    seq, chars, syls, i = [], [], list(syls), 0
    while i < len(text):
        if text[i] in PUNCT:
            seq.append(PUNCT[text[i]]); chars.append(text[i]); i += 1
            continue
        if not is_han(text[i]):
            i += 1
            continue
        n = next((n for n in range(min(10, len(text) - i), 0, -1) if len(lexicon.get(text[i:i + n], [])) == n), 0)
        own = syls[:max(n, 1)]
        dic = lexicon[text[i:i + n]] if n else [s.lower().replace('ü', 'v') for s in own]
        for c, d, a in zip(text[i:i + max(n, 1)], dic, own):
            seq.append(d if base(d) == base(a.lower()) else a.lower().replace('ü', 'v').rstrip('05'))
            chars.append(c)
        syls = syls[max(n, 1):]
        i += max(n, 1)
    for k in range(len(seq) - 1):
        a, b = seq[k], seq[k + 1]
        if not a[-1].isdigit() or not b[-1].isdigit():
            continue
        if tone(a) == 3 and tone(b) == 3:  # in a run of 3rd tones, all but the last are said as 2nd tones
            seq[k] = a[:-1] + '2'
        elif chars[k] == '不' and tone(a) == 4 and tone(b) == 4:
            seq[k] = a[:-1] + '2'
    return seq if seq and seq[-1] in '.?!' else seq + ['.']


acoustic = ort.InferenceSession(os.path.join(B, 'model-steps-3.onnx'), providers=['CPUExecutionProvider'])
vocoder = ort.InferenceSession(os.path.join(MODELS, 'vocos-22khz-univ.onnx'), providers=['CPUExecutionProvider'])


def synth(seq, length_scale):
    unknown = [s for s in seq if s not in tok]
    if unknown:
        sys.exit('the voice has no sound for: ' + ' '.join(unknown))
    ids = [1] + [i for s in seq for i in (tok[s], 1)]  # symbols separated by the blank symbol, as in training
    mel = acoustic.run(None, {'x': np.array([ids], np.int64), 'x_length': np.array([len(ids)], np.int64),
                              'noise_scale': np.array([0.667], np.float32), 'length_scale': np.array([length_scale], np.float32)})[0]
    mag, cos, sin = vocoder.run(None, {'mels': mel})
    # inverse STFT (n_fft 1024, hop 256, Hann window, centered frames)
    frames = np.fft.irfft((mag * (cos + 1j * sin))[0], n=1024, axis=0)
    win, hop = np.hanning(1025)[:-1], 256
    out, norm = np.zeros(1024 + hop * (frames.shape[1] - 1)), np.zeros(1024 + hop * (frames.shape[1] - 1))
    for t in range(frames.shape[1]):
        out[t * hop:t * hop + 1024] += frames[:, t] * win
        norm[t * hop:t * hop + 1024] += win ** 2
    return (out / np.maximum(norm, 1e-8))[512:-512].astype(np.float32)


def clean(x):
    """Trim silence at both ends, leave a little air, and even out the volume."""
    peak = float(np.max(np.abs(x)))
    env = np.convolve(np.abs(x), np.ones(RATE // 50) / (RATE // 50), mode='same')
    loud = np.flatnonzero(env > peak * 0.02)
    x = x[max(0, loud[0] - RATE // 100):loud[-1] + RATE // 25] / peak * 0.89
    return np.concatenate([np.zeros(int(0.06 * RATE), np.float32), x, np.zeros(int(0.15 * RATE), np.float32)])


S = os.path.join(MODELS, 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17')
P = os.path.join(MODELS, 'sherpa-onnx-paraformer-zh-small-2024-03-09')
recognizers = [
    sherpa_onnx.OfflineRecognizer.from_sense_voice(model=os.path.join(S, 'model.int8.onnx'), tokens=os.path.join(S, 'tokens.txt'), language='zh', use_itn=False),
    sherpa_onnx.OfflineRecognizer.from_paraformer(paraformer=os.path.join(P, 'model.int8.onnx'), tokens=os.path.join(P, 'tokens.txt')),
]
toned = lambda s: lazy_pinyin(''.join(filter(is_han, s)), style=Style.TONE3, neutral_tone_with_five=True)


def pitch(x):
    """Pitch curve of the voiced part as 5 points, in semitones (None if too little voicing)."""
    n, h = RATE // 25, RATE // 100
    peak, f0 = np.abs(x).max(), []
    for i in range(0, len(x) - n, h):
        f = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt(np.mean(f ** 2)) < 0.03 * peak:
            continue
        ac = np.correlate(f, f, 'full')[n - 1:]
        k = RATE // 450 + int(np.argmax(ac[RATE // 450:RATE // 120]))
        if ac[k] > 0.6 * ac[0]:
            f0.append(12 * np.log2(RATE / k))
    if len(f0) < 8:
        return None
    f0 = f0[len(f0) // 10:len(f0) - len(f0) // 10]
    return np.array([seg.mean() for seg in np.array_split(f0, 5)])


# The voice's pitch range, so a tone can be judged on a 1 (low) to 5 (high) scale like Chao's tone letters.
scale = np.concatenate([pitch(clean(synth([s, '.'], 1.15))) for s in ('ma1', 'ma2', 'ma3', 'ma4', 'shu1', 'guo2', 'hao3', 'shi4')])
low, high = np.percentile(scale, 5), np.percentile(scale, 95)
SHAPES = (1, 2, 3, 4)


def tone_heard(x):
    """1 level and high, 2 rising to high, 3 low (dipping or falling, as it's mostly said), 4 falling from high."""
    p = pitch(x)
    if p is None:
        return None
    p = 1 + 4 * (p - low) / (high - low)
    slope = p[-1] - p[0]
    if slope <= -1 and p[0] >= 4:
        return 4
    if slope >= 1 and p[-1] >= 3.5:
        return 2
    if abs(slope) < 0.8 and p.mean() >= 3.3:
        return 1
    return 3 if p.mean() <= 2.6 else None


def heard(x):
    """What each recognizer hears (16 kHz)."""
    x16 = np.interp(np.arange(0, len(x), RATE / 16000), np.arange(len(x)), x).astype(np.float32)
    out = []
    for r in recognizers:
        s = r.create_stream()
        s.accept_waveform(16000, x16)
        r.decode_stream(s)
        out.append(''.join(filter(is_han, s.result.text)))
    return out


# A lone particle can't be recognized on its own (吗 sounds like 妈), so it's checked the way it's used: right after a
# short word (你好吗, 你呢, 我的). Only the particle is saved.
CARRIER = {'吗': '你好', '吧': '走', '了': '对', '啊': '是', '呢': '你', '的': '我'}
carriers = {}


def carrier(c):
    if c not in carriers:
        carriers[c] = clean(synth(symbols(c, toned(c)), 1.15))
    return carriers[c]


audio_dir = os.path.join(root, 'audio')
used = {int(f[2:5]) for f in os.listdir(audio_dir) if f.startswith('zh') and f.endswith('.m4a')}
n = max(used or {0})
for text in texts:
    seq = symbols(text, reading[text])
    n_han = sum(map(is_han, text))
    particle = n_han == 1 and tone(seq[0]) == 5
    lead = CARRIER.get(text, '你') if particle else ''
    want = toned(lead + text)
    # A one-syllable word also has to show its tone's shape; how it ends (。！，) changes the shape, so takes try each.
    single = n_han == 1 and tone(seq[0]) in SHAPES
    full = 2 * len(recognizers) + 2 * single
    best = (-1, None, None, None)
    for take in range(TAKES):
        if single:
            seq = seq[:-1] + ['.!,'[take % 3]]
        # A particle is light and short, but read too short its first sound gets lost: takes try both lengths.
        x = clean(synth(seq, (0.95, 1.15)[take % 2] if particle else 1.15 if n_han <= 2 else 1.2))
        got = heard(np.concatenate([carrier(lead), x]) if lead else x)
        # 2 per recognizer that hears the same syllables and tones (so homophones count: 李悦 = 李月), 1 for the right
        # syllables in another tone.
        score = sum(2 if toned(g) == want else [s.rstrip('12345') for s in toned(g)] == [s.rstrip('12345') for s in want] for g in got)
        shape = tone_heard(x) if single else None
        score += 2 * (single and shape == tone(seq[0]))
        if score > best[0]:
            best = (score, x, got, shape)
        if score == full:
            break
    score, x, got, shape = best
    wav = os.path.join(audio_dir, 'tmp.wav')
    sf.write(wav, x, RATE)
    n += 1
    name = 'audio/zh%03d.m4a' % n
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-ac', '1', '-ar', str(RATE), '-c:a', 'aac', '-b:a', '80k',
                    '-movflags', '+faststart', os.path.join(root, name)], check=True)
    os.remove(wav)
    amap[text] = name
    print(name, text, ' '.join(seq), '' if score == full else '  <- check by ear: recognizers heard %s%s' % (
        ' / '.join(g or '(nothing)' for g in got), ', tone shape %s' % shape if single else ''))
json.dump(amap, open(amap_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if EVERY or replaced:
    keep = {os.path.basename(f) for f in amap.values()}
    for f in os.listdir(audio_dir):
        if f.startswith('zh') and f.endswith('.m4a') and f not in keep:
            os.remove(os.path.join(audio_dir, f))
