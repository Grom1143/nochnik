"""Текстура Луны для Ночника: видимая сторона в ортографической проекции (как Луна видна с Земли).
Источник — карта NASA SVS CGI Moon Kit (LRO, общественное достояние) в равнопромежуточной проекции, 1024×512.
Запуск: python -I текстура_луны.py <moon1k.jpg> <выход.txt> [размер]  → base64 JPEG в одну строку (для MOONTEX)."""
import sys, io, math, base64
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 320
eq = Image.open(src).convert('L'); W, H = eq.size; px = eq.load()

def sample(u, v):   # bilinear, u wraps around the globe
    x, y = u % W, min(H - 1.001, max(0, v))
    x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0; x1 = (x0 + 1) % W
    a = px[x0, y0] * (1 - fx) + px[x1, y0] * fx
    b = px[x0, y0 + 1] * (1 - fx) + px[x1, y0 + 1] * fx
    return a * (1 - fy) + b * fy

img = Image.new('L', (N, N), 0); o = img.load(); r = N / 2 - 1
for j in range(N):
    for i in range(N):
        X, Y = (i + .5 - N / 2) / r, (N / 2 - j - .5) / r       # east to the right, north up
        rr = X * X + Y * Y
        if rr > 1: X, Y = X / math.sqrt(rr), Y / math.sqrt(rr); rr = 1   # a hair past the limb: repeat the edge
        Z = math.sqrt(max(0, 1 - rr))
        lat, lon = math.asin(Y), math.atan2(X, Z)                 # sub-Earth point is lon 0, lat 0
        o[i, j] = round(sample((lon / (2 * math.pi) + .5) * W, (.5 - lat / math.pi) * H))
# contrast stretched over the disk (1–99 %), black outside it: the same look as the first, 160 px texture
from PIL import ImageOps, ImageDraw
mask = Image.new('L', (N, N), 0); ImageDraw.Draw(mask).ellipse((1, 1, N - 2, N - 2), fill=255)
img = Image.composite(ImageOps.autocontrast(img, cutoff=1, mask=mask), Image.new('L', (N, N), 0), mask)
buf = io.BytesIO(); img.save(buf, 'JPEG', quality=88, optimize=True)
open(out, 'w').write(base64.b64encode(buf.getvalue()).decode())
print('%dx%d, %d КБ' % (N, N, len(buf.getvalue()) // 1024))
