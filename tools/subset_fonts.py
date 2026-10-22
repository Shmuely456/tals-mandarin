"""Rebuild the app's font files, keeping only the characters the app and its lessons use.

Run after adding a lesson (new characters):  python3 tools/subset_fonts.py <folder with source .ttf files>
Sources: Google Fonts Fredoka (wght 500..700), Nunito (wght 500..800), Noto Serif SC 500 and 700.
"""
import glob, json, os, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
src = sys.argv[1]
text = open(os.path.join(root, 'index.html'), encoding='utf-8').read()
for f in glob.glob(os.path.join(root, 'content', '*.json')):
    text += open(f, encoding='utf-8').read()
latin = 'U+0000-024F,U+0300-036F,U+1E00-1EFF,U+2000-206F,U+20A0-20CF,U+2100-215F,U+2190-21FF,U+2200-22FF'
cjk = ''.join(sorted({c for c in text if ord(c) > 0x2000}))
open(os.path.join(here, '.cjk-chars.txt'), 'w', encoding='utf-8').write(cjk)
jobs = [
    ('Fredoka_wght_500__700.ttf', 'fredoka.woff2', ['--unicodes=' + latin]),
    ('Nunito_wght_500__800.ttf', 'nunito.woff2', ['--unicodes=' + latin]),
    ('NotoSerifSC_wght_500.ttf', 'noto-serif-sc-500.woff2', ['--unicodes=' + latin, '--text-file=' + os.path.join(here, '.cjk-chars.txt')]),
    ('NotoSerifSC_wght_700.ttf', 'noto-serif-sc-700.woff2', ['--unicodes=' + latin, '--text-file=' + os.path.join(here, '.cjk-chars.txt')]),
]
for inp, out, opts in jobs:
    subprocess.run(['pyftsubset', os.path.join(src, inp), '--flavor=woff2', '--layout-features=*', '--output-file=' + os.path.join(root, 'fonts', out)] + opts, check=True)
    print(out, os.path.getsize(os.path.join(root, 'fonts', out)) // 1024, 'KB')
os.remove(os.path.join(here, '.cjk-chars.txt'))
