"""Скачивает шрифты Google Fonts, которые нужны Ночнику и Эфиру, чтобы приложение выглядело так же без интернета.
Берутся только кириллица и латиница. Результат: папка инструменты\\fonts\\ (woff2 + css) и fonts\\map.txt
(строка: адрес, по которому страница просит файл <TAB> имя файла). Ночник.exe отвечает на эти адреса сам."""
import os, re, hashlib, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fonts')
os.makedirs(OUT, exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
CSS = [  # exactly as in nochnik.html and in Эфир after сборка_эфира.py
    'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap',
    'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=Manrope:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400&display=swap',
]
KEEP = ('cyrillic', 'latin')

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=30).read()

lines, files = [], {}
for i, url in enumerate(CSS):
    css = get(url).decode('utf8')
    blocks = re.findall(r'/\* ([\w-]+) \*/\s*(@font-face\s*\{[^}]*\})', css)
    kept = [b for subset, b in blocks if subset in KEEP]
    for b in kept:
        for f in re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)', b):
            if f not in files:
                name = hashlib.sha1(f.encode()).hexdigest()[:12] + '.woff2'
                open(os.path.join(OUT, name), 'wb').write(get(f))
                files[f] = name
    name = 'page%d.css' % i
    open(os.path.join(OUT, name), 'w', encoding='utf8').write('\n'.join(kept))
    lines.append(url + '\t' + name)
lines += [u + '\t' + n for u, n in files.items()]
open(os.path.join(OUT, 'map.txt'), 'w', encoding='utf8').write('\n'.join(lines) + '\n')
size = sum(os.path.getsize(os.path.join(OUT, n)) for n in files.values())
print('css: %d, шрифтов: %d, %d КБ' % (len(CSS), len(files), size // 1024))
