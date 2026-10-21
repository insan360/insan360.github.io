#!/usr/bin/env python3
"""Build the İnsanlık Eli website.

Reads everything in content/ and templates/, writes the finished site to _site/.
GitHub runs this automatically after every change (see .github/workflows/deploy.yml).
To try it on a computer:  pip install -r requirements.txt  &&  python build.py
"""
import datetime as dt
import html
import json
import os
import re
import shutil
import sys

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, 'content')
OUT = os.path.join(ROOT, '_site')

MONTHS = {
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'tr': ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'],
    'ar': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
}

errors = []


def fail(msg):
    errors.append(msg)


# ----------------------------------------------------------------- loading
def read_yaml(path):
    try:
        with open(path, encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        fail(f'{os.path.relpath(path, ROOT)}: the text could not be read ({e}). Check colons and indentation.')
        return {}


def read_md(path):
    """Return (front_matter, markdown_body) of a content file."""
    rel = os.path.relpath(path, ROOT)
    with open(path, encoding='utf-8') as f:
        text = f.read().lstrip('﻿')
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.S)
    if not m:
        fail(f'{rel}: the file must start with a --- block (title, date, ...) and close it with ---.')
        return None, ''
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        fail(f'{rel}: the part between the --- lines has an error ({e}). Tip: put titles that contain a colon in quotes.')
        return None, ''
    return fm, m.group(2)


MD = markdown.Markdown(extensions=['extra', 'sane_lists'])


def render_md(text):
    MD.reset()
    out = MD.convert(text or '')
    # open external links in a new tab
    out = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', out)
    return out


def plain(text, limit=None):
    t = re.sub(r'<[^>]+>', ' ', render_md(text))
    t = html.unescape(re.sub(r'\s+', ' ', t)).strip()
    if limit and len(t) > limit:
        t = t[:limit].rsplit(' ', 1)[0].rstrip('.,;:') + '…'
    return t


def to_date(value, rel):
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value).strip())
    except Exception:
        fail(f'{rel}: the date "{value}" is not valid. Write it as YYYY-MM-DD, for example 2026-10-21.')
        return None


def load_collection(kind, lang):
    folder = os.path.join(CONTENT, kind, lang)
    items = []
    if not os.path.isdir(folder):
        return items
    for name in sorted(os.listdir(folder)):
        if not name.endswith('.md') or name.startswith(('_', '.')):
            continue
        path = os.path.join(folder, name)
        rel = os.path.relpath(path, ROOT)
        fm, body = read_md(path)
        if fm is None:
            continue
        if fm.get('draft'):
            continue
        if not fm.get('title'):
            fail(f'{rel}: "title:" is missing.')
            continue
        slug = name[:-3]
        item = dict(fm)
        item['lang'] = lang
        item['body'] = render_md(body)
        item['excerpt'] = plain(body, 170)
        if kind == 'news':
            m = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)$', slug)
            if m:
                slug = m.group(2)
                item.setdefault('date', m.group(1))
            if not item.get('date'):
                fail(f'{rel}: no date. Start the file name with the date, like 2026-10-21-my-news.md')
                continue
            item['date'] = to_date(item['date'], rel)
            if item['date'] is None:
                continue
        item['slug'] = slug
        if kind in ('programs', 'projects') and not item.get('image'):
            # a photo uploaded as static/img/<kind>/<file-name>.jpg is used automatically
            auto = f'/img/{kind}/{slug}.jpg'
            if os.path.exists(os.path.join(ROOT, 'static', auto.lstrip('/'))):
                item['image'] = auto
        item['ref'] = f'{kind}/{slug}'
        item['url'] = f'/{lang}/{kind}/{slug}/'
        item['src'] = rel
        for key in ('image',):
            if item.get(key):
                check_asset(item[key], rel)
        for g in item.get('gallery') or []:
            check_asset(g, rel)
        items.append(item)
    if kind == 'news':
        items.sort(key=lambda x: (x['date'], x['slug']), reverse=True)
    elif kind == 'programs':
        items.sort(key=lambda x: (x.get('order') or 99, x['title']))
    return items


def check_asset(url, rel):
    if not isinstance(url, str) or not url.startswith('/'):
        fail(f'{rel}: image path "{url}" should start with /img/')
        return
    if not os.path.exists(os.path.join(ROOT, 'static', url.lstrip('/'))):
        fail(f'{rel}: image "{url}" was not found. Upload it to static{url}')


# ----------------------------------------------------------------- building
def main():
    site = read_yaml(os.path.join(CONTENT, 'site.yml'))
    langs = site.get('languages', ['tr', 'en', 'ar'])
    T = {l: read_yaml(os.path.join(CONTENT, 'i18n', f'{l}.yml')) for l in langs}
    data = {}
    for l in langs:
        data[l] = {k: load_collection(k, l) for k in ('programs', 'projects', 'news')}
    if errors:
        report()

    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'templates')), autoescape=True,
                      trim_blocks=True, lstrip_blocks=True)

    def fmt_date(d, lang):
        return f'{d.day} {MONTHS[lang][d.month - 1]} {d.year}'

    env.filters['date'] = fmt_date
    env.filters['tojson_attr'] = lambda v: html.escape(json.dumps(v, ensure_ascii=False))
    env.globals['site'] = site
    env.globals['year'] = dt.date.today().year

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, 'static'), OUT)

    # every ref -> {lang: url}, so the language switcher can jump to the same page
    refs = {}

    def reg(ref, lang, url):
        refs.setdefault(ref, {})[lang] = url

    pages = []  # (template, lang, url, ref, context)
    for l in langs:
        d = data[l]
        prog_by_slug = {p['slug']: p for p in d['programs']}
        for p in d['programs']:
            p['projects'] = [x for x in d['projects'] if x.get('program') == p['slug']]
        for x in d['projects']:
            x['program_item'] = prog_by_slug.get(x.get('program'))
            if x.get('program') and not x['program_item']:
                # programme exists in another language only: fall back to its English title
                other = next((p for ll in langs for p in data[ll]['programs'] if p['slug'] == x['program']), None)
                x['program_item'] = dict(title=other['title'], url=None) if other else None
        media = media_items(data, l, langs)
        base = dict(lang=l, t=T[l], programs=d['programs'], projects=d['projects'], news=d['news'], media=media)

        def add(tpl, url, ref, _l=l, _base=base, **kw):
            pages.append((tpl, _l, url, ref, {**_base, **kw}))
            reg(ref, _l, url)

        add('home.html', f'/{l}/', 'home')
        add('about.html', f'/{l}/about/', 'about')
        add('programs.html', f'/{l}/programs/', 'programs')
        add('projects.html', f'/{l}/projects/', 'projects')
        add('news_list.html', f'/{l}/news/', 'news')
        add('media.html', f'/{l}/media/', 'media')
        add('reports.html', f'/{l}/reports/', 'reports')
        add('contact.html', f'/{l}/contact/', 'contact')
        add('donate.html', f'/{l}/donate/', 'donate')
        for p in d['programs']:
            add('program.html', p['url'], p['ref'], item=p)
        for x in d['projects']:
            add('project.html', x['url'], x['ref'], item=x)
        for n in d['news']:
            add('news.html', n['url'], n['ref'], item=n, more=[m for m in d['news'] if m is not n][:3])

    for tpl, l, url, ref, ctx in pages:
        alt = {ll: refs.get(ref, {}).get(ll) or f'/{ll}/' for ll in langs}
        hreflang = {ll: u for ll, u in refs.get(ref, {}).items()}
        html_out = env.get_template(tpl).render(**ctx, page_url=url, alt=alt, hreflang=hreflang, ref=ref, langs=langs, T=T)
        write(url, html_out)

    # root: send visitors to their language
    write('/', env.get_template('root.html').render(langs=langs, default=site.get('default_lang', 'tr'), T=T))
    write('/404.html', env.get_template('404.html').render(lang=site.get('default_lang', 'tr'), t=T[site.get('default_lang', 'tr')],
                                                          T=T, langs=langs, alt={l: f'/{l}/' for l in langs}, hreflang={},
                                                          page_url='/404.html', ref='404', programs=[], projects=[], news=[], media=[]))

    # old insanlikeli.org addresses -> new pages (only where the new page exists)
    existing = {p[2] for p in pages}
    for old, new in old_redirects(data, langs).items():
        target = new if new in existing else '/' + new.strip('/').split('/')[0] + '/'
        write(old, env.get_template('redirect.html').render(to=target))

    # sitemap + robots
    base_url = site.get('url', '').rstrip('/')
    urls = [p[2] for p in pages]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f'  <url><loc>{base_url}{u}</loc></url>' for u in urls]
    sm.append('</urlset>')
    write('/sitemap.xml', '\n'.join(sm) + '\n')
    write('/robots.txt', f'User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n')
    print(f'Built {len(pages)} pages into _site/')


def media_items(data, lang, langs):
    """Every real photo used in news and projects, newest first. Captions in the page language when available."""
    seen, items = set(), []
    order = [lang] + [l for l in langs if l != lang]
    for l in order:
        for n in data[l]['news']:
            same = next((x for x in data[lang]['news'] if x['slug'] == n['slug']), None)
            for img in [n.get('image')] + list(n.get('gallery') or []):
                if img and img not in seen:
                    seen.add(img)
                    items.append(dict(src=img, title=same['title'] if same else '', url=same['url'] if same else n['url'],
                                      date=n['date']))
    items.sort(key=lambda x: x['date'], reverse=True)
    for l in order:
        for x in data[l]['projects']:
            same = next((p for p in data[lang]['projects'] if p['slug'] == x['slug']), None)
            if x.get('image') and x['image'] not in seen:
                seen.add(x['image'])
                items.append(dict(src=x['image'], title=same['title'] if same else '', url=same['url'] if same else x['url'], date=None))
    return items


def old_redirects(data, langs):
    m = {}
    pages = {
        'en': {'en/home-page-0': '', 'en/about-us': 'about', 'en/all-projects': 'projects', 'en/akhbarna': 'news',
               'en/media-center': 'media', 'en/articles-reports': 'reports', 'en/twasl-mna': 'contact', 'en/for-support': 'donate'},
        'tr': {'tr/ev': '', 'tr/biz-kimiz-0': 'about', 'tr/all-projects': 'projects', 'tr/akhbarna': 'news',
               'tr/media-center': 'media', 'tr/articles-reports': 'reports', 'tr/twasl-mna': 'contact', 'tr/for-support': 'donate'},
        'ar': {'ar/alsfht-alryysyt': '', 'ar/mn-nhn-0': 'about', 'ar/all-projects': 'projects', 'ar/akhbarna': 'news',
               'ar/media-center': 'media', 'ar/articles-reports': 'reports', 'ar/twasl-mna': 'contact', 'ar/for-support': 'donate'},
    }
    for l, mp in pages.items():
        for old, new in mp.items():
            m[f'/{old}/'] = f'/{l}/{new + "/" if new else ""}'
    nodes = {'370': 'news/iddef-visit', '369': 'news/kevser-foundation-visit', '368': 'news/nezir-association-visit',
             '367': 'news/benin-mosque-construction', '364': 'news/kim-foundation-visit', '333': 'news/nigeria-mosque-completed',
             '336': 'news/nigeria-mosque-completed', '332': 'news/gaza-safe-drinking-water', '335': 'news/gaza-safe-drinking-water',
             '331': 'news/gaza-situation-report', '334': 'news/gaza-situation-report', '366': 'projects/safe-drinking-water',
             '365': 'projects/emergency-food-assistance', '363': 'projects/infant-nutrition-support',
             '362': 'projects/hot-meals-community-kitchens', '361': 'projects/orphan-sponsorship-gaza'}
    for l in langs:
        for nid, path in nodes.items():
            m[f'/{l}/node/{nid}/'] = f'/{l}/{path}/'
    return m


def write(url, content):
    path = url.lstrip('/')
    if path == '' or path.endswith('/'):
        path += 'index.html'
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)


def report():
    print('\nThe site was NOT updated because of these problems:\n', file=sys.stderr)
    for e in errors:
        print('  - ' + e, file=sys.stderr)
    print('', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
    main()
    if errors:
        report()
