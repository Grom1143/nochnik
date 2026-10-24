"""Собирает Ночник.exe компилятором C#, который есть в каждой Windows (.NET Framework 4).
Внутрь кладутся: Ночник.html, иконка, шрифты (инструменты\\fonts, их качает шрифты.py) и библиотеки WebView2
(инструменты\\webview2, из NuGet-пакета Microsoft.Web.WebView2 1.0.4191.47, подписаны Microsoft).
Запуск: python инструменты\\собрать_exe.py  (после правок nochnik.html сначала пересобери Ночник.html)."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSC = r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
OUT = os.path.join(ROOT, 'Ночник.exe')
WV = os.path.join(HERE, 'webview2')
FONTS = os.path.join(HERE, 'fonts')

# one stylesheet with every face of both pages (Ночник and Эфир); unicode-range keeps loading to what a page uses
css, seen = [], set()
for n in sorted(os.listdir(FONTS)):
    if n.endswith('.css') and n != 'fonts.css':
        for block in open(os.path.join(FONTS, n), encoding='utf8').read().split('@font-face'):
            if block.strip() and block not in seen:
                seen.add(block); css.append('@font-face' + block.rstrip() + '\n')
open(os.path.join(FONTS, 'fonts.css'), 'w', encoding='utf8').write(''.join(css))

res = [(os.path.join(ROOT, 'Ночник.html'), 'page.html'), (os.path.join(ROOT, 'icon.png'), 'icon.png')]
res += [(os.path.join(WV, n), n) for n in ('WebView2Loader.dll', 'Microsoft.Web.WebView2.Core.dll', 'Microsoft.Web.WebView2.WinForms.dll')]
res += [(os.path.join(FONTS, n), 'fonts/' + n) for n in os.listdir(FONTS) if n.endswith(('.woff2', '.txt')) or n == 'fonts.css']

args = [CSC, '/nologo', '/target:winexe', '/platform:x64', '/optimize+', '/codepage:65001',
        '/out:' + OUT, '/win32icon:' + os.path.join(ROOT, 'icon.ico'),
        '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
        '/reference:' + os.path.join(WV, 'Microsoft.Web.WebView2.Core.dll'),
        '/reference:' + os.path.join(WV, 'Microsoft.Web.WebView2.WinForms.dll')]
args += ['/resource:%s,%s' % r for r in res]
args.append(os.path.join(HERE, 'Ночник.cs'))
r = subprocess.run(args, capture_output=True, text=True, encoding='cp866', errors='replace')
print(r.stdout.strip() or 'собрано: %s (%d КБ, ресурсов %d)' % (OUT, os.path.getsize(OUT) // 1024, len(res)))
sys.exit(r.returncode)
