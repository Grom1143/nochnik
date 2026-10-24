"""Встраивает Aether (C:/Users/andre/aether/index.html) в Ночник как режим «Эфир».

Исходник Aether не меняется: берём копию, переводим интерфейс на русский,
добавляем кнопку «назад в Ночник» и кладём всё в nochnik.html в виде base64.
Запуск:  python сборка_эфира.py   (обновит nochnik.html и Ночник.html)
"""
import base64, re, sys

SRC = r'C:\Users\andre\aether\index.html'
DST = r'C:\Users\andre\Desktop\Ночник\nochnik.html'
FULL = r'C:\Users\andre\Desktop\Ночник\Ночник.html'

RU = [
    ('<html lang="en">', '<html lang="ru">'),
    ('<title>Aether — a living instrument</title>', '<title>Эфир — живой инструмент</title>'),
    ('<span class="brand-name">AETHER</span>', '<span class="brand-name">ЭФИР</span>'),
    ('aria-live="polite">Aurora</span>', 'aria-live="polite">Ночь</span>'),
    ('<span class="micro">Palette</span>', '<span class="micro">Палитра</span>'),
    ("pal.name + ' palette (' + (i + 1) + ')'", "'Палитра «' + pal.name + '» (' + (i + 1) + ')'"),
    ("pal.name + ' palette'", "'Палитра «' + pal.name + '»'"),
    ('A study in light &amp; sound — Nº 01', 'Этюд света и звука — № 01'),
    ('<span>Move · bend</span>', '<span>Веди · изгибай</span>'),
    ('<span>Click · bloom</span>', '<span>Клик · вспышка</span>'),
    ('<span>Keys · play</span>', '<span>Клавиши · играй</span>'),
    ('<span class="touch-hint">Tap · bloom</span>', '<span class="touch-hint">Тап · вспышка</span>'),
    ('An instrument of light &amp; sound', 'Инструмент света и звука'),
    ('<h1>Aether</h1>', '<h1>Эфир</h1>'),
    ('A generative audiovisual meditation.<br><em>Move</em> to shape it. <em>Play</em> it like an instrument.',
     'Живая медитация из света и звука.<br><em>Веди</em> курсором — она меняется. <em>Играй</em> на ней, как на инструменте.'),
    ('Enter with sound', 'Войти со звуком'), ('Enter in silence', 'Войти в тишине'),
    ('<span>Headphones recommended</span>', '<span>Лучше в наушниках</span>'),
    ('<span>Live generative audio</span>', '<span>Звук рождается вживую</span>'),
    ('No two moments alike', 'Ни один миг не повторится'),
    ('MMXXVI · A living study', 'MMXXVI · Живой этюд'),
    ('<span>Rec</span>', '<span>Запись</span>'),
    ('Aether · Instructions', 'Эфир · Как играть'), ('>How to play</h2>', '>Как играть</h2>'),
    ('<div class="rule-key">Move</div>', '<div class="rule-key">Веди</div>'),
    ('Bend the light with your cursor. The whole field swirls around you.', 'Изгибай свет курсором: всё поле закручивается вокруг тебя.'),
    ('<div class="rule-key">Click / tap</div>', '<div class="rule-key">Клик / тап</div>'),
    ('Release a bloom — light, sound, a ripple in the dark.', 'Выпусти вспышку — свет, звук и круги по темноте.'),
    ('Play the pentatonic scale. Every note paints its own light.', 'Играй пентатонику. Каждая нота рисует свой свет.'),
    ('<kbd>Space</kbd>', '<kbd>Пробел</kbd>'),
    ('Send a chord through everything. A full bloom.', 'Аккорд сквозь всё поле — большое цветение.'),
    ('Sound on or off. Change the palette of the world.', 'Звук вкл/выкл. Смена палитры мира.'),
    ('<div class="rule-key"><kbd>R</kbd> / red dot</div>', '<div class="rule-key"><kbd>R</kbd> / красная точка</div>'),
    ('Record a thirty-second clip. If sound is on, the clip keeps it.', 'Запиши клип до 30 секунд. Если звук включён, он попадёт в запись.'),
    ('<div class="rule-key">Camera</div>', '<div class="rule-key">Камера</div>'),
    ('Save a high-resolution still to your downloads.', 'Сохрани кадр в высоком разрешении в «Загрузки».'),
    ('Made for you, with a little stardust.', 'Сделано для тебя, с щепоткой звёздной пыли.'),
    ('Aether · New recording', 'Эфир · Новая запись'), ('A moment, kept.', 'Мгновение сохранено.'),
    ('>Save clip</a>', '>Сохранить клип</a>'), ('type="button">Discard</button>', 'type="button">Удалить</button>'),
    ('Light and sound, held for a little longer.', 'Свет и звук, задержанные чуть дольше.'),
    ("'Mute sound (M)'", "'Выключить звук (M)'"), ("'Mute sound'", "'Выключить звук'"),
    ("'Enable sound (M)'", "'Включить звук (M)'"), ("'Enable sound'", "'Включить звук'"),
    ('title="Enable sound (M)"', 'title="Включить звук (M)"'), ('aria-label="Enable sound"', 'aria-label="Включить звук"'),
    ('title="Save a still"', 'title="Сохранить кадр"'), ('aria-label="Save a still"', 'aria-label="Сохранить кадр"'),
    ('title="Fullscreen"', 'title="Во весь экран"'), ('aria-label="Fullscreen"', 'aria-label="Во весь экран"'),
    ('title="How to play"', 'title="Как играть"'), ('aria-label="How to play"', 'aria-label="Как играть"'),
    ("'Record a clip (R, max 30s)'", "'Записать клип (R, до 30 с)'"), ("'Record a clip'", "'Записать клип'"),
    ('title="Record a clip (R, max 30s)"', 'title="Записать клип (R, до 30 с)"'), ('aria-label="Record a clip"', 'aria-label="Записать клип"'),
    ("'Finish recording'", "'Закончить запись'"),
    ("'Play ' + def.name", "'Нота ' + def.name"),
    ("toast('Sound muted')", "toast('Звук выключен')"),
    ("toast('Sound on — listen closely')", "toast('Звук включён — прислушайся')"),
    ("toast('Audio is not available here')", "toast('Звук здесь недоступен')"),
    ("toast('Finish the recording first')", "toast('Сначала закончи запись')"),
    ("toast('Could not save the still')", "toast('Не удалось сохранить кадр')"),
    ("toast('Still saved to your downloads')", "toast('Кадр сохранён в «Загрузки»')"),
    ("toast('Video recording is not available here')", "toast('Запись видео здесь недоступна')"),
    ("toast('Recording failed')", "toast('Запись не удалась')"),
    ("toast('Nothing was recorded')", "toast('Ничего не записалось')"),
    ("'Recording with sound — press the dot to finish' : 'Recording silently — press the dot to finish'",
     "'Пишу со звуком — нажми точку, чтобы закончить' : 'Пишу без звука — нажми точку, чтобы закончить'"),
    ("toast('Could not start recording')", "toast('Не удалось начать запись')"),
    ("toast('Clip saved to your downloads')", "toast('Клип сохранён в «Загрузки»')"),
    ("toast('Fullscreen is unavailable')", "toast('Полный экран недоступен')"),
    ("sec · ${mb} MB · ${hasAudio ? 'sound' : 'silent'}", "с · ${mb} МБ · ${hasAudio ? 'со звуком' : 'без звука'}"),
]

# один язык с Ночником: те же шрифты, тёплый акцент, мягкие кнопки, своя палитра «Ночь» первой
LOOK = [
    ('family=Inter:wght@300;400;500;600', 'family=Manrope:wght@300;400;500;600'),
    ("--sans:'Inter',system-ui", "--sans:'Manrope',system-ui"),
    ('--ink:#f4f1e9;', '--ink:#ede7d7;'),
    ('--accent:#a9f4dc;', '--accent:#f4b36a;'),
    ('--accent-glow:rgba(169,244,220,.30);', '--accent-glow:rgba(244,179,106,.30);'),
    ('--accent-faint:rgba(169,244,220,.12);', '--accent-faint:rgba(244,179,106,.12);'),
    ('html{background:#03050a}', 'html{background:#070a1a}'),
    ('margin:0;overflow:hidden;background:#03050a;', 'margin:0;overflow:hidden;background:#070a1a;'),
    ('.btn-solid{background:var(--ink);border-color:var(--ink);color:#05080c}',
     '.btn-solid{background:rgba(244,179,106,.15);border-color:rgba(244,179,106,.45);color:var(--accent)}'),
    ("background:var(--accent);border-color:var(--accent);color:#04120e;\n    transform:translateY(-2px)",
     "background:rgba(244,179,106,.26);border-color:var(--accent);color:var(--ink);\n    transform:translateY(-2px)"),
    ("localStorage.getItem('aether.palette')", "localStorage.getItem('nochnik.aether.palette')"),
    ("localStorage.setItem('aether.palette'", "localStorage.setItem('nochnik.aether.palette'"),
]
PALETTES = """  const PALETTES = [
    { id: 'night', name: 'Ночь', bg: '#070a1a', bg2: '#03040c', accent: '#f4b36a',
      colors: ['#f4b36a', '#b993f0', '#67d3b6', '#8ea4ff'] },
    { id: 'aurora', name: 'Сияние', bg: '#04070d', bg2: '#010308', accent: '#a9f4dc',
      colors: ['#6ef4d6', '#887aff', '#46a6ff', '#34d3c8'] },
    { id: 'ember', name: 'Угли', bg: '#0b0506', bg2: '#040203', accent: '#ffb98a',
      colors: ['#ff945e', '#ff5c7a', '#ffc56e', '#c66bff'] },
    { id: 'tide', name: 'Прилив', bg: '#030a12', bg2: '#01050a', accent: '#9ad8ff',
      colors: ['#58c9ff', '#466eff', '#78e2ff', '#b08bff'] }
  ];"""

# возвращение в Ночник: кнопка-луна и Esc (если не открыто окно и не идёт запись)
BACK = '''<style>
  .to-nochnik{position:fixed;z-index:60;left:50%;top:26px;transform:translateX(-50%);display:inline-flex;align-items:center;gap:8px;
    padding:8px 14px 8px 11px;border-radius:999px;border:1px solid rgba(244,179,106,.35);background:rgba(10,8,6,.45);
    color:#f4b36a;font:500 11px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;cursor:pointer;transition:background .3s,opacity .3s}
  .to-nochnik:hover{background:rgba(244,179,106,.16)}
  .to-nochnik svg{width:14px;height:14px}
  @media (max-width:760px){.to-nochnik{top:auto;bottom:calc(150px + env(safe-area-inset-bottom))}}
</style>
<button class="to-nochnik" id="toNochnik" type="button" title="Вернуться в Ночник (Esc)" hidden>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/></svg>Ночник
</button>
<script>
(() => {
  if (window.parent === window) return; // opened on its own: nothing to go back to
  const back = () => window.parent.postMessage({ nochnik: 'close-aether' }, '*');
  const b = document.getElementById('toNochnik'); b.hidden = false; b.addEventListener('click', back);
  // capture phase runs before Aether's own handler, so we still see an open modal / recording
  addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (!document.getElementById('helpModal').hidden || !document.getElementById('clipModal').hidden ||
        document.getElementById('recPill').classList.contains('show')) return;
    back();
  }, true);
})();
</script>
'''

h = open(SRC, encoding='utf8').read()
h, k = re.subn(r'  const PALETTES = \[.*?\n  \];', lambda m: PALETTES, h, count=1, flags=re.S)
if k != 1:
    print('не нашёл PALETTES'); sys.exit(1)
for a, b in RU + LOOK:
    if a not in h:
        print('нет строки:', a[:70]); sys.exit(1)
    h = h.replace(a, b)
h = h.replace('</body>', BACK + '</body>', 1) if '</body>' in h else h + BACK

blob = base64.b64encode(h.encode('utf8')).decode()
n = open(DST, encoding='utf8').read()
n2, k = re.subn(r'(<script type="text/plain" id="aetherSrc">)[^<]*(</script>)', lambda m: m.group(1) + blob + m.group(2), n)
if k != 1:
    print('в nochnik.html нет блока aetherSrc'); sys.exit(1)
open(DST, 'w', encoding='utf8').write(n2)
# Ночник.html — та же страница с полной HTML-обёрткой; её открывает ярлык на рабочем столе
open(FULL, 'w', encoding='utf8').write('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="theme-color" content="#060915">\n<meta name="color-scheme" content="dark">\n<link rel="icon" href="icon.png">\n</head>\n<body>\n' + n2 + '\n</body>\n</html>\n')
print('Эфир встроен:', len(h), 'символов ->', len(blob), 'байт base64')
