"""Готовит данные настоящего неба для Ночника из каталога d3-celestial (© Olaf Frohn, BSD-3).

Вход (скачать в любую папку и передать её путь):
  stars.6.json, constellations.lines.json, constellations.json, mw.json
  из https://github.com/ofrohn/d3-celestial/tree/master/data
Выход: sky-data.js  — одна строка `const SKYDATA = {...}` с base64 массивами Int16.

Кодирование (всё целые int16):
  звёзды: [ra*90, dec*360, mag*1000, bv*1000] — ra 0..360°, точность ~0.01°
  линии созвездий и Млечный Путь: [ra*90, dec*360], ломаные разделены парой (-32768, -32768)
Звёзды южнее −50° над Ростовом (47° с. ш.) не восходят никогда — их не берём.
Запуск: python данные_неба.py <папка с json> <куда положить sky-data.js>
"""
import json, sys, base64, struct, math, os

src, out = sys.argv[1], sys.argv[2]
J = lambda f: json.load(open(os.path.join(src, f), encoding='utf8'))
SEP = (-32768, -32768)


def ra_of(lon):
    return lon % 360.0


def b64(nums):
    return base64.b64encode(struct.pack('<%dh' % len(nums), *nums)).decode()


def enc_pt(lon, lat):
    return [int(round(ra_of(lon) * 90)), int(round(lat * 360))]  # 360° * 90 = 32400 fits int16


# ---- stars
stars = []
# stars.8.json (if it is there) gives the faint stars that show up when the view is magnified; kept to 7.5m
STARS, MAXMAG = ('stars.8.json', 7.5) if os.path.exists(os.path.join(src, 'stars.8.json')) else ('stars.6.json', 6.5)
for f in J(STARS)['features']:
    lon, lat = f['geometry']['coordinates']
    if lat < -50: continue
    p = f['properties']
    mag = float(p['mag'])
    if mag > MAXMAG: continue
    try: bv = float(p.get('bv') or 0.6)
    except ValueError: bv = 0.6
    stars.append((mag, enc_pt(lon, lat) + [int(round(mag * 1000)), int(round(max(-0.4, min(2.0, bv)) * 1000))]))
stars.sort()  # brightest first: the renderer can stop early for a faint-star budget
star_nums = [n for _, s in stars for n in s]

# ---- constellation lines
lines = []
names = {}
for f in J('constellations.json')['features']:
    names[f['id']] = (f['properties'].get('ru') or f['properties']['name'], f['properties'].get('rank', '3'), f['geometry']['coordinates'])
con = []
for f in J('constellations.lines.json')['features']:
    cid = f['id']
    pts = []
    for ln in f['geometry']['coordinates']:
        if max(p[1] for p in ln) < -45: continue
        for lon, lat in ln: pts += enc_pt(lon, lat)
        pts += SEP
    if not pts: continue
    nm, rank, (llon, llat) = names[cid]
    nm = nm[0].upper() + nm[1:].lower() if nm.isupper() else nm
    con.append({'id': cid, 'n': nm, 'r': int(rank), 'l': [round(ra_of(llon), 2), round(llat, 2)], 'p': b64(pts)})


# ---- Milky Way: five nested density levels, simplified (Douglas–Peucker on the sphere, ~0.35°)
def dist_pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    if dx == dy == 0: return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def dp(pts, eps):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop(); best, bi = 0, -1
        for k in range(i + 1, j):
            # scale ra difference by cos(dec) so the tolerance is roughly in true degrees
            c = math.cos(math.radians(pts[k][1]))
            d = dist_pt_seg((pts[k][0] * c, pts[k][1]), (pts[i][0] * c, pts[i][1]), (pts[j][0] * c, pts[j][1]))
            if d > best: best, bi = d, k
        if best > eps:
            keep[bi] = True; stack += [(i, bi), (bi, j)]
    return [p for p, k in zip(pts, keep) if k]


mw = []
total = 0
for f in J('mw.json')['features']:
    nums = []
    for poly in f['geometry']['coordinates']:
        for ring in poly:
            r = dp(ring, 0.35)
            if len(r) < 4: continue
            total += len(r)
            for lon, lat in r: nums += enc_pt(lon, lat)
            nums += SEP
    mw.append(b64(nums))

data = {'stars': b64(star_nums), 'con': con, 'mw': mw,
        'src': 'd3-celestial © Olaf Frohn, BSD-3; звёзды: Hipparcos/Tycho до %sm' % MAXMAG}
js = 'const SKYDATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
open(out, 'w', encoding='utf8').write(js)
print('звёзд', len(stars), '| созвездий', len(con), '| точек Млечного Пути', total, '| размер', len(js) // 1024, 'КБ')
