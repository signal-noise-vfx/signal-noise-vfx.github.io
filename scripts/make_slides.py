"""Render the Instagram carousel for one Signal/Noise issue and queue it for posting.

Usage: python scripts/make_slides.py social/slides.json
Input (slides.json):
{
  "issue": "05", "date": "30 NOV 2026",
  "summary": "one or two sentences for the cover",
  "stories": [{"tag": "ADOBE · AFTER EFFECTS", "head": "short headline", "dek": "one sentence"}, x3],
  "caption": "full Instagram caption"
}
Writes social/01_cover.jpg ... 05_outro.jpg and social/post.json (mode "post"),
which triggers the "Post to Instagram" GitHub Action when pushed.
Also writes social/preview.png (contact sheet) for checking, which is not committed.
"""
import json, sys, pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
F = ROOT / 'scripts' / 'fonts'
OUT = ROOT / 'social'
W, H, M = 1080, 1350, 90
BG, FG, DIM, ACC, SUB = (14, 14, 16), (240, 240, 240), (130, 130, 138), (255, 60, 60), (200, 200, 206)
BARS = [(192,192,192),(192,192,0),(0,192,192),(0,192,0),(192,0,192),(192,0,0),(0,0,192)]
FOOT_Y = H - 130          # nothing may cross this line
TOTAL = 5


def fnt(n, s): return ImageFont.truetype(str(F / f'{n}.ttf'), s)


def base(n):
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    for y in range(0, H, 4): d.line([(0, y), (W, y)], fill=(18, 18, 21))
    bw = W / 7
    for i, c in enumerate(BARS): d.rectangle([int(i*bw), 0, int((i+1)*bw), 14], fill=c)
    mono = fnt('jetbrains-mono-700', 26)
    x = M
    for part, col in (('SIGNAL', FG), ('/', ACC), ('NOISE', FG)):
        d.text((x, 64), part, font=mono, fill=col); x += d.textlength(part, font=mono)
    t = f'{n:02d}/{TOTAL:02d}'
    d.text((W - M - d.textlength(t, font=mono), 64), t, font=mono, fill=DIM)
    d.line([(M, 116), (W - M, 116)], fill=(40, 40, 46), width=2)
    return im, d


def wrap(d, text, font, maxw):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def block(d, xy, text, font, fill, lh, draw=True):
    x, y = xy
    for l in wrap(d, text, font, W - 2*M):
        if draw: d.text((x, y), l, font=font, fill=fill)
        y += lh
    return y


def footer(d, text):
    mono = fnt('jetbrains-mono-400', 24)
    d.line([(M, FOOT_Y), (W - M, FOOT_Y)], fill=(40, 40, 46), width=2)
    d.text((M, H - 100), text, font=mono, fill=DIM)
    a = fnt('DejaVuSans-Bold', 30)
    d.text((W - M - d.textlength('→', font=a), H - 104), '→', font=a, fill=ACC)


def cover(issue, date, summary):
    im, d = base(1)
    d.rectangle([M, 230, M + 22, 252], fill=ACC)
    d.text((M + 40, 224), f'ISSUE {issue}  ·  {date}', font=fnt('jetbrains-mono-700', 30), fill=FG)
    d.text((M - 18, 270), issue, font=fnt('space-grotesk-700', 400), fill=FG)
    d.text((M, 760), 'AI news for', font=fnt('space-grotesk-700', 76), fill=FG)
    d.text((M, 846), 'VFX & promo', font=fnt('space-grotesk-700', 76), fill=ACC)
    for size in (36, 33, 30, 28):
        f = fnt('inter-400', size)
        if block(d, (M, 975), summary, f, SUB, int(size * 1.44), draw=False) <= FOOT_Y - 20:
            break
    block(d, (M, 975), summary, f, SUB, int(size * 1.44))
    footer(d, 'SWIPE FOR THE HEADLINES')
    return im


def story(n, num, tag, head, dek):
    # shrink headline, then body, until everything clears the footer
    for hs, bs in ((88, 36), (80, 36), (72, 34), (66, 32), (60, 30), (56, 28)):
        im, d = base(n)
        hf, bf = fnt('space-grotesk-700', hs), fnt('inter-400', bs)
        y = block(d, (M, 710), head, hf, FG, int(hs * 1.09), draw=False)
        end = block(d, (M, y + 80), dek, bf, SUB, int(bs * 1.44), draw=False)
        if end <= FOOT_Y - 20:
            break
    d.text((M - 10, 250), num, font=fnt('space-grotesk-700', 300), fill=(34, 34, 40))
    mono = fnt('jetbrains-mono-700', 28)
    tw = d.textlength(tag, font=mono)
    d.rectangle([M, 620, M + tw + 36, 668], outline=ACC, width=3)
    d.text((M + 18, 627), tag, font=mono, fill=ACC)
    y = block(d, (M, 710), head, hf, FG, int(hs * 1.09))
    d.rectangle([M, y + 30, M + 90, y + 38], fill=ACC)
    block(d, (M, y + 80), dek, bf, SUB, int(bs * 1.44))
    footer(d, f'STORY {num} OF 03')
    return im


def outro(issue):
    im, d = base(5)
    bw = W / 7
    for i, c in enumerate(BARS): d.rectangle([int(i*bw), 300, int((i+1)*bw), 520], fill=c)
    low = [(0,0,192),BG,(192,0,192),BG,(0,192,192),BG,(192,192,192)]
    for i, c in enumerate(low): d.rectangle([int(i*bw), 520, int((i+1)*bw), 560], fill=c)
    d.text((M, 650), 'See more in', font=fnt('space-grotesk-700', 84), fill=FG)
    d.text((M, 744), f'Issue {issue}', font=fnt('space-grotesk-700', 84), fill=ACC)
    block(d, (M, 880), 'The full digest, with every story, source and what it means for your work.',
          fnt('inter-400', 36), SUB, 52)
    mono = fnt('jetbrains-mono-700', 34)
    d.rectangle([M, 1070, W - M, 1150], outline=FG, width=3)
    t = 'LINK IN BIO'; a = fnt('DejaVuSans-Bold', 36); tw = d.textlength(t, font=mono) + 50
    x = (W - tw) / 2; d.text((x, 1090), t, font=mono, fill=FG); d.text((x + tw - 34, 1088), '↗', font=a, fill=ACC)
    footer(d, 'NEW ISSUE EVERY MON & THU')
    return im


def main(spec_path):
    s = json.loads(pathlib.Path(spec_path).read_text(encoding='utf-8'))
    assert len(s['stories']) == 3, 'exactly 3 stories'
    OUT.mkdir(exist_ok=True)
    ims = [cover(s['issue'], s['date'], s['summary'])]
    for i, st in enumerate(s['stories']):
        ims.append(story(i + 2, f'{i+1:02d}', st['tag'].upper(), st['head'], st['dek']))
    ims.append(outro(s['issue']))
    names = ['01_cover', '02_story', '03_story', '04_story', '05_outro']
    for n, im in zip(names, ims):
        im.save(OUT / f'{n}.jpg', 'JPEG', quality=92)
    sheet = Image.new('RGB', (5 * 440, 550), (60, 60, 60))
    for i, im in enumerate(ims): sheet.paste(im.resize((432, 540)), (i * 440, 5))
    sheet.save(OUT / 'preview.png')
    post = {'mode': 'post', 'issue': s['issue'], 'caption': s['caption'], 'slides': [n + '.jpg' for n in names]}
    (OUT / 'post.json').write_text(json.dumps(post, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Rendered 5 slides and queued social/post.json. Check social/preview.png.')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'social/slides.json')
