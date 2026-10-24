"""Regression run for Ночник: each scenario injects a script, runs headless Edge with virtual time, reads data-run."""
import subprocess, re, html, os, tempfile
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
SRC = r'C:\Users\andre\Desktop\Ночник\nochnik.html'
HERE = os.path.join(tempfile.gettempdir(), 'nochnik-tests'); os.makedirs(HERE, exist_ok=True)
SHIM = ('<script>(function(){var RD=Date;var base=new RD();base.setHours(23,30,0,0);window.__off=base-RD.now();'
        'function D(){var a=[].slice.call(arguments);if(!a.length)return new RD(RD.now()+window.__off);'
        'return new (Function.prototype.bind.apply(RD,[null].concat(a)))()}D.prototype=RD.prototype;'
        'D.now=function(){return RD.now()+window.__off};D.UTC=RD.UTC;D.parse=RD.parse;window.Date=D})()</script>')
PRE = ('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       '{shim}<script>try{{localStorage.setItem("nochnik.napIntro","false")}}catch(e){{}}window.__e=[];onerror=function(m,s,l){{__e.push(m+" @"+l)}}</script></head><body>')
DONE = 'function done(s){document.body.setAttribute("data-run",JSON.stringify(__e)+"|"+s)}'
P = 'var $=function(s){return document.querySelector(s)};var pad=function(n){return String(n).padStart(2,"0")};'

SCEN = {
 'boot': (False, 3000, 'setTimeout(function(){done($$(".opt")+"/"+$$(".chan")+"/"+$$(".item"))},800);var $$=function(s){return document.querySelectorAll(s).length};',
          lambda r: r == '4/8/3'),
 'sounds': (False, 4000, 'setTimeout(function(){document.querySelectorAll(".chan-btn").forEach(function(b){b.click()});$("[data-min=\\"15\\"]").click();setTimeout(function(){done($("#miniWhat").textContent.split(" · ").length+"|"+$("#miniTm").textContent)},1200)},300);',
          lambda r: re.fullmatch(r'8\|стихнет через (15:00|14:5\d)', r) is not None),
 'preset': (False, 3000, 'setTimeout(function(){$(".preset").click();setTimeout(function(){done($("#miniWhat").textContent)},500)},300);',
          lambda r: r == 'Дождь · Море · Ветер'),
 'nap-intro': (False, 14000, 'setTimeout(function(){localStorage.setItem("nochnik.napIntro","true");$("#lampBtn").click();setTimeout(function(){var a=$("#nap").hidden+"/"+$("#lamp").hidden;setTimeout(function(){done(a+"|"+$("#lamp").hidden+"|"+$("#nap").hidden);$("#lamp").click()},11500)},1000)},300);',
          lambda r: r == 'false/true|false|true'),  # the intro plays, then the night light opens and the intro goes away
 'galaxy': (False, 9000, 'setTimeout(function(){$("#galBtn").click();setTimeout(function(){var r=$("#galCard h3").textContent+"|"+!!$("#galCv").getContext("webgl")+"|"+$("#galTags").children.length;$("#galBar [data-a=sun]").click();setTimeout(function(){r+="|"+$("#galCard h3").textContent;document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}));setTimeout(function(){done(r+"|"+$("#galaxy").hidden)},900)},1500)},2500)},300);',
          lambda r: r == 'Млечный Путь|true|9|Солнце · вы здесь|true'),  # WebGL galaxy opens, flies to the Sun, Esc closes
 'calm': (False, 4000, 'setTimeout(function(){$("#skyBtn").click();setTimeout(function(){var r=document.documentElement.classList.contains("calm")+"|"+/^Над Ростовом/.test($("#calmCap").textContent);dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"}));setTimeout(function(){done(r+"|"+document.documentElement.classList.contains("calm"))},300)},800)},300);',
          lambda r: r == 'true|true|false'),
 'lamp-off': (True, 6000, 'setTimeout(function(){$("#lampBtn").click();$("[data-off=\\"15\\"]").click();setTimeout(function(){var c=document.documentElement.classList.contains("lamp-on");window.__off+=16*60000;setTimeout(function(){var L=$("#lamp"),d=L.classList.contains("dark");$("#lampNight").click();setTimeout(function(){var r=c+"|"+d+"|"+L.classList.contains("dark")+"|"+L.hidden;L.click();done(r+"|"+L.hidden+"|"+document.documentElement.classList.contains("lamp-on"))},300)},1500)},1600)},300);',
          lambda r: r == 'true|true|false|false|true|false'),  # the light goes out after the chosen time, a touch brings it back
 'cat': (False, 3000, 'setTimeout(function(){$("[data-mix^=cat]").click();setTimeout(function(){done($("#miniWhat").textContent)},500)},300);',
          lambda r: 'Кот' in r and len(r.split(' · ')) == 3),
 'breath': (False, 8000, 'setTimeout(function(){$("[data-p=\\"478\\"]").click();$("#bStart").click();setTimeout(function(){done($("#bPhase").textContent+"|"+$("#bStat").textContent)},5000)},300);',
          lambda r: r.startswith('Вдох|цикл 1 из 8')),  # rAF does not advance under virtual time: checks the first frame
 'scan': (False, 40000, 'setTimeout(function(){$("[data-p=scan]").click();$("#bStart").click();setTimeout(function(){done($("#bCount").textContent)},31000)},300);',
          lambda r: r == '1 / 12'),  # same: first frame only
 'weekday': (False, 3000, 'setTimeout(function(){var d=new Date();var i=$("#wd-"+d.getDay());i.value="09:30";i.dispatchEvent(new Event("change",{bubbles:true}));setTimeout(function(){done($("#left").textContent.slice(0,19))},300)},300);',
          lambda r: r == 'До подъёма в 09:30 '),
 'dawn+snooze': (False, 90000, 'setTimeout(function(){var d=new Date(Date.now()+60000);var w=$("#wake");w.value=pad(d.getHours())+":"+pad(d.getMinutes());w.dispatchEvent(new Event("change"));$("#dawn").checked=true;$("#dawn").dispatchEvent(new Event("change"));$("#lampBtn").click();setTimeout(function(){var a=$("#miniWhat").textContent+"/"+$("#snooze").hidden;$("#snooze").click();setTimeout(function(){done(a+"|"+$("#miniWhat").textContent+"|"+$("#lampSub").textContent.slice(0,13))},62000)},3000)},300);',
          lambda r: r == 'Птицы/false||ещё немного ·'),
 'second-night': (False, 8000, 'setTimeout(function(){var d=new Date(Date.now()+60000);var w=$("#wake");w.value=pad(d.getHours())+":"+pad(d.getMinutes());w.dispatchEvent(new Event("change"));$("#dawn").checked=true;$("#dawn").dispatchEvent(new Event("change"));$("#lampBtn").click();setTimeout(function(){var a=$("#lampSub").textContent.slice(0,12);$("#lamp").click();var d3=new Date(Date.now()+3*36e5);w.value=pad(d3.getHours())+":"+pad(d3.getMinutes());w.dispatchEvent(new Event("change"));$("#lampBtn").click();done(a+"|"+$("#lamp").style.getPropertyValue("--dawn")+"|"+$("#lamp").classList.contains("day")+"|"+$("#lampSub").textContent.slice(-5))},3000)},300);',
          lambda r: r.startswith('Доброе утро.|0.000|false|') and r[-3] == ':'),  # a night light used at dawn must open dark the next evening
 'night-log': (True, 4000, 'setTimeout(function(){$("#lampBtn").click();setTimeout(function(){window.__off+=(7*60+40)*60000;$("#lamp").click();setTimeout(function(){var d=JSON.parse(localStorage.getItem("nochnik.diary"));done(d.length+"|"+d[0].bed+"-"+d[0].wake+"|"+$("#toastTxt").textContent.slice(0,23))},300)},500)},500);',
          lambda r: r == '1|23:30-07:10|Ночь записана в дневник'),
 'diary-save': (False, 3000, 'setTimeout(function(){location.hash="diary";setTimeout(function(){$("#dSave").click();setTimeout(function(){done(document.querySelectorAll("#dChart .bar").length+"|"+$("#dEx").hidden)},300)},300)},300);',
          lambda r: r == '1|true'),
 'no-sleep': (False, 3000, 'setTimeout(function(){location.hash="diary";setTimeout(function(){$("#dNoSleep").click();setTimeout(function(){done(document.querySelectorAll("#dChart rect.ns").length+"|"+$("#dNoSleep").getAttribute("aria-pressed")+"|"+$("#dStats").textContent.indexOf("8 ч")+"|"+JSON.parse(localStorage.getItem("nochnik.diary"))[0].ns)},300)},300)},300);',
          lambda r: r.startswith('1|true|') and r.endswith('|true') and r.split('|')[2] != '-1'),  # a sleepless night: 0 h on the chart, 8 h of debt
 'release': (False, 3000, 'setTimeout(function(){$(".item .rel").click();setTimeout(function(){done(document.querySelectorAll(".item").length+"|"+localStorage.getItem("nochnik.released"))},900)},300);',
          lambda r: r == '2|1'),
 'rasp (сеть)': (True, 20000, 'setTimeout(function(){$("#raspBtn").click();setTimeout(function(){done($("#toastTxt").textContent.slice(0,31)+"|"+!!localStorage.getItem("nochnik.raspAt"))},12000)},300);',
          lambda r: r == 'Подъём заполнен по расписанию: |true'),  # needs internet and edu.donstu.ru
}

src = open(SRC, encoding='utf8').read()
ok_all = True
for name, (shim, budget, js, check) in SCEN.items():
    page = PRE.format(shim=SHIM if shim else '') + src + '<script>' + DONE + P + js + '</script></body></html>'
    fn = os.path.join(HERE, 'reg_%s.html' % re.sub(r'\W', '_', name))
    open(fn, 'w', encoding='utf8').write(page)
    out = subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--virtual-time-budget=%d' % budget, '--dump-dom',
                          'file:///' + fn.replace('\\', '/')], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=240).stdout
    m = re.search(r'data-run="([^"]*)"', out)
    raw = html.unescape(m.group(1)) if m else '<no result>'
    errs, _, res = raw.partition('|')
    good = m is not None and errs == '[]' and check(res)
    ok_all &= good
    print(('PASS' if good else 'FAIL'), name.ljust(12), res if good else raw)
print('ALL PASS' if ok_all else 'SOME FAILED')
