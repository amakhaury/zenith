# Сборка сайта: src/ + site.config.json → docs/ (папку docs/ публикует GitHub Pages)
# Запуск: python3 tools/build.py     (нужен только Python 3, без Node.js и сторонних пакетов)
#
# Адрес сайта берётся из siteUrl в site.config.json:
#   https://amakhaury.github.io/zenith  → все ссылки получат префикс /zenith
#   https://zenith.ru                   → ссылки от корня + файл CNAME для своего домена
import base64, datetime, hashlib, json, os, re, shutil, sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from icons import ICONS, PHONE_PATH

SRC = os.path.join(ROOT, 'src')
OUT = os.path.join(ROOT, 'docs')
cfg = json.load(open(os.path.join(ROOT, 'site.config.json'), encoding='utf8'))

def read(p): return open(p, encoding='utf8').read()
def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf8').write(s)

site_url = cfg['siteUrl'].rstrip('/')
u = urlparse(site_url)
host, base = u.netloc, u.path.rstrip('/')          # base: '' или '/zenith'

shutil.rmtree(OUT, ignore_errors=True)

# 1. Копируем картинки, шрифты, иконки (HTML, CSS и JS собираются ниже)
SKIP_DIRS = {'assets/css', 'assets/js', 'assets/icons'}
for dirpath, dirnames, filenames in os.walk(SRC):
    rel = os.path.relpath(dirpath, SRC)
    rel = '' if rel == '.' else rel
    dirnames[:] = [d for d in dirnames if os.path.join(rel, d) not in SKIP_DIRS]
    for f in filenames:
        if f.endswith('.html') or f.startswith('.'): continue
        os.makedirs(os.path.join(OUT, rel), exist_ok=True)
        shutil.copy2(os.path.join(SRC, rel, f), os.path.join(OUT, rel, f))

# 2. Шрифт Felidae (если положили src/assets/fonts/felidae.woff2)
felidae_css = ''
if os.path.exists(os.path.join(SRC, 'assets/fonts/felidae.woff2')) and cfg.get('displayFont') != 'fallback':
    felidae_css = '@font-face{font-family:"Felidae";font-style:normal;font-weight:300 400;font-display:swap;src:url("../fonts/felidae.woff2") format("woff2")}'
    print(' Felidae: подключён')
else:
    print(' Felidae: файла нет — используется Cormorant Light')

# 3. CSS и JS
css = read(os.path.join(SRC, 'assets/css/main.css')).replace('/*@@FELIDAE@@*/', felidae_css)
write(os.path.join(OUT, 'assets/css/main.css'), css)
inline_css = css.replace('../fonts/', base + '/assets/fonts/')   # CSS встраивается в главную — пути от корня сайта
js = read(os.path.join(SRC, 'assets/js/main.js'))
write(os.path.join(OUT, 'assets/js/main.js'), js)
version = hashlib.sha256((css + js).encode('utf8')).hexdigest()[:8]

# 4. Подстановки
logo_raw = read(os.path.join(SRC, 'assets/icons/logo.svg')).strip()
logo_inner = re.sub(r'</svg>$', '', re.sub(r'^<svg[^>]*>', '', logo_raw))
logo_inline = f'<svg viewBox="0 0 91 64" width="91" height="64" aria-hidden="true" focusable="false">{logo_inner}</svg>'
logo_use = '<svg viewBox="0 0 91 64" width="91" height="64" aria-hidden="true" focusable="false"><use href="#logo"/></svg>'
logo_symbol = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="logo" viewBox="0 0 91 64">{logo_inner}</symbol></svg>'
svg_icon = lambda d: f'<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true" focusable="false"><path d="{d}"/></svg>'

order = ['whatsapp', 'instagram', 'telegram']
soc = cfg.get('socials') or {}
links = ''.join(f'<li><a href="{soc[k]}" target="_blank" rel="noopener" aria-label="{ICONS[k][0]}">{svg_icon(ICONS[k][1])}</a></li>'
                for k in order if soc.get(k))
socials = f'<ul class="socials">{links}</ul>' if links else ''

services = ['Лестницы из камня', 'Столешницы из камня', 'Подоконники из камня', 'Мраморные полы', 'Балясины из камня']
jsonld = {
    '@context': 'https://schema.org', '@type': 'HomeAndConstructionBusiness',
    'name': cfg['brand'], 'url': site_url + '/', 'logo': site_url + '/icon-512.png',
    'image': site_url + '/assets/img/og-image.jpg', 'description': cfg['seoDescription'],
    'telephone': cfg['phoneHref'],
    'areaServed': [{'@type': 'City', 'name': c} for c in cfg['cities']],
    'sameAs': [soc[k] for k in order if soc.get(k) and k != 'instagram'],
    'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': 'Изделия из камня',
                        'itemListElement': [{'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': s}} for s in services]},
}
if cfg.get('email'): jsonld['email'] = cfg['email']
V = {
    'brand': cfg['brand'], 'siteUrl': site_url, 'siteHost': host + base,
    'seoTitle': cfg['seoTitle'], 'seoDescription': cfg['seoDescription'],
    'phoneDisplay': cfg['phoneDisplay'], 'phoneHref': cfg['phoneHref'], 'email': cfg.get('email', ''),
    'contactName': cfg.get('contactName', ''), 'waNumber': cfg.get('whatsappNumber') or re.sub(r'\D', '', cfg['phoneHref']),
    'waIcon': svg_icon(ICONS['whatsapp'][1]), 'callIcon': svg_icon(PHONE_PATH),
    'companyName': cfg['company']['name'], 'companyInn': cfg['company']['inn'],
    'companyOgrn': cfg['company']['ogrn'], 'companyAddress': cfg['company']['address'],
    'year': str(datetime.date.today().year), 'version': version, 'policyDate': '12.11.2026',
    'socials': socials,
    'instagramNote': '<span>* Instagram — продукт компании Meta, признанной экстремистской организацией и запрещённой в РФ</span>' if soc.get('instagram') else '',
    'metrikaAttr': f' data-metrika="{cfg["metrikaId"]}"' if cfg.get('metrikaId') else '',
    'verification': f'<meta name="yandex-verification" content="{cfg["yandexVerification"]}">' if cfg.get('yandexVerification') else '',
    'displayFontPreload': '/assets/fonts/felidae.woff2' if felidae_css else '/assets/fonts/display-cyr.woff2',
    'jsonld': json.dumps(jsonld, ensure_ascii=False, separators=(',', ':')),
}
def fill(tpl, extra={}):
    def sub(m):
        k = m.group(1)
        if k in extra: return extra[k]
        if k not in V: sys.exit('Нет значения для {{' + k + '}}')
        return V[k]
    return re.sub(r'\{\{(\w+)\}\}', sub, tpl)

def with_base(html):
    """Ссылки от корня (/assets/…, /politika/) → с префиксом проекта (/zenith/assets/…)."""
    if not base: return html
    html = re.sub(r'((?:href|src|srcset|imagesrcset)=")/(?!/)', rf'\1{base}/', html)
    return re.sub(r'(, )/(?=assets/)', rf'\1{base}/', html)          # остальные элементы srcset

# CSP вместо заголовков .htaccess (GitHub Pages свои заголовки ставить не даёт)
def csp(script_hash):
    return ("default-src 'self'; "
            f"script-src 'self' '{script_hash}' https://mc.yandex.ru https://yastatic.net; "
            "img-src 'self' data: https://mc.yandex.ru https://mc.yandex.com; "
            "connect-src 'self' https://mc.yandex.ru https://mc.yandex.com; "
            "style-src 'self' 'unsafe-inline'; font-src 'self'; "
            "frame-src https://mc.yandex.ru https://mc.yandex.com; "
            "form-action 'self' https://wa.me https://api.whatsapp.com; base-uri 'self'")
security_meta = '<meta name="referrer" content="strict-origin-when-cross-origin">'

# главная
index = fill(read(os.path.join(SRC, 'index.html')), {'styles': f'<style>{inline_css}</style>', 'logoSvg': logo_use})
index = index.replace('<body>', '<body>' + logo_symbol, 1)
inline_script = re.search(r'<script>([^<]+)</script>', index).group(1)
script_hash = 'sha256-' + base64.b64encode(hashlib.sha256(inline_script.encode('utf8')).digest()).decode()
index = index.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{csp(script_hash)}">\n{security_meta}', 1)
write(os.path.join(OUT, 'index.html'), with_base(index))

for rel in ['politika/index.html', '404.html']:
    html = fill(read(os.path.join(SRC, rel)), {'logoSvg': logo_inline})
    html = html.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n{security_meta}', 1)
    write(os.path.join(OUT, rel), with_base(html))

# 5. Служебные файлы
today = datetime.date.today().isoformat()
write(os.path.join(OUT, 'robots.txt'), f'User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n')
write(os.path.join(OUT, 'sitemap.xml'), f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{site_url}/</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>\n  <url><loc>{site_url}/politika/</loc><lastmod>{today}</lastmod><priority>0.2</priority></url>\n</urlset>\n')
write(os.path.join(OUT, 'site.webmanifest'), json.dumps({'name': cfg['brand'], 'short_name': cfg['brand'], 'start_url': base + '/', 'display': 'browser', 'background_color': '#101010', 'theme_color': '#101010', 'icons': [{'src': base + '/icon-192.png', 'sizes': '192x192', 'type': 'image/png'}, {'src': base + '/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}, ensure_ascii=False))
write(os.path.join(OUT, '.nojekyll'), '')                    # отдавать файлы как есть, без Jekyll
if not host.endswith('github.io'):
    write(os.path.join(OUT, 'CNAME'), host + '\n')           # свой домен для GitHub Pages

print(f'Готово: docs/ | адрес {site_url}/ | version {version}')
