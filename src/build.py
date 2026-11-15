#!/usr/bin/env python3
"""Static site generator for fd432games.com.

Usage:  python src/build.py

Reads src/content.json and writes plain HTML pages into the repository root
(GitHub Pages serves the root of the gh-pages branch). No dependencies.

Output:
  index.html, pl/index.html                       home (EN / PL)
  <slug>/index.html, pl/<slug>/index.html         game pages (released games)
  cannon-shoot-block-down-2/ ...                  redirects from old WordPress URLs
  404.html, sitemap.xml, robots.txt
"""

import datetime
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "src" / "content.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
UI = DATA["ui"]
GAMES = DATA["games"]
LANGS = ("en", "pl")
YEAR = datetime.date.today().year

# Old URLs (WordPress / previous game names) that should keep working
REDIRECTS = {old: g["slug"] for g in GAMES for old in g.get("old_slugs", [])}


def per_lang(value, lang):
    """Values in content.json may be a single value or {"en": ..., "pl": ...}."""
    return value[lang] if isinstance(value, dict) else value


def shots_for(g, lang):
    return per_lang(g["shots"], lang)


def cover_for(g, lang):
    return g.get("cover") or shots_for(g, lang)[0]


def esc(s):
    return html.escape(s, quote=True)


def lang_dir(lang):
    return "" if lang == "en" else lang + "/"


def abs_url(lang, path=""):
    return f"{SITE['url']}/{lang_dir(lang)}{path}"


def game_theme(g):
    t = g["theme"]
    return f"--g-accent:{t['accent']};--g-ink:{t['ink']};--g-bg:{t['bg']};--g-bg2:{t['bg2']}"


def img_path(p, name):
    return f"{p}assets/img/games/{name}"


# ---------------------------------------------------------------- SVG pieces

def mark(cls="", label=None):
    a11y = f'role="img" aria-label="{esc(label)}"' if label else 'aria-hidden="true"'
    return (
        f'<svg class="{cls}" viewBox="0 0 64 64" {a11y} focusable="false">'
        '<path fill="#FFB21A" d="M35 10H10.5a4.5 4.5 0 0 0 0 9H26v8H14.5a4.5 4.5 0 0 0 0 9H26v15.5a2.5 2.5 0 0 0 2.5 2.5H35z"/>'
        '<path fill="#F3F1EC" fill-rule="evenodd" d="M35 10h4a22 22 0 0 1 0 44h-4zm0 9h4a13 13 0 0 1 0 26h-4z"/>'
        '<circle cx="42.5" cy="32" r="4.5" fill="#FFB21A"/></svg>'
    )


PLAY_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M6 3.8v16.4c0 .8.9 1.3 1.6.9l13.3-8.2c.6-.4.6-1.3 0-1.7L7.6 2.9C6.9 2.5 6 3 6 3.8z"/></svg>'
)

ARROW = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M13 6l6 6-6 6"/></svg>'
)


def hero_art():
    """Brand illustration: a launcher, a dotted aiming trajectory and a stack of blocks."""
    traj = "M98 312 Q 240 20 424 196"
    palette = ["#FFB21A", "#F3F1EC", "#3B4357", "#FF3DDB", "#7CC24A", "#5CC8E0"]
    rows = [(372, 294, 4), (390, 258, 3), (408, 222, 2), (426, 186, 1)]
    order = [2, 0, 1, 2, 1, 5, 3, 0, 2, 0]
    blocks, i = [], 0
    for x0, y, n in rows:
        for k in range(n):
            c = palette[order[i % len(order)]]
            x = x0 + k * 36
            blocks.append(
                f'<rect x="{x}" y="{y}" width="34" height="34" rx="5" fill="{c}"/>'
                f'<rect x="{x + 4}" y="{y + 4}" width="26" height="5" rx="2.5" fill="#fff" opacity=".18"/>'
            )
            i += 1
    return f"""<svg viewBox="0 0 560 420" aria-hidden="true" focusable="false">
  <defs>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#FFB21A" stop-opacity=".35"/>
      <stop offset="1" stop-color="#FFB21A" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <ellipse cx="440" cy="250" rx="150" ry="120" fill="url(#glow)"/>
  <path d="{traj}" fill="none" stroke="#FFB21A" stroke-width="7" stroke-linecap="round" stroke-dasharray="0 16" class="trajectory" opacity=".9"/>
  <rect x="356" y="328" width="190" height="18" rx="4" fill="#232836"/>
  <rect x="356" y="328" width="190" height="4" rx="2" fill="#fff" opacity=".08"/>
  {''.join(blocks)}
  <g transform="translate(70 360)">
    <rect x="-8" y="-13" width="66" height="26" rx="13" fill="#F3F1EC" transform="rotate(-62)"/>
    <rect x="-8" y="-13" width="20" height="26" rx="10" fill="#FFB21A" transform="rotate(-62)"/>
    <circle cx="0" cy="18" r="20" fill="#232836" stroke="#3B4357" stroke-width="4"/>
    <circle cx="0" cy="18" r="5" fill="#FFB21A"/>
  </g>
  <rect x="20" y="380" width="120" height="16" rx="4" fill="#232836"/>
  <circle r="11" fill="#F3F1EC" class="ball-anim">
    <animateMotion dur="2.4s" repeatCount="indefinite" path="{traj}" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines=".35 0 .7 1"/>
  </circle>
  <circle cx="250" cy="137" r="11" fill="#F3F1EC" class="ball-static"/>
</svg>"""


# ---------------------------------------------------------------- layout

def head(lang, path, title, desc, p, og_image=None, jsonld=None, redirect_alt=None):
    t = UI[lang]
    other = "pl" if lang == "en" else "en"
    og_image = og_image or f"{SITE['url']}/assets/img/og-image.png"
    # Auto-redirect Polish browsers from EN pages on their first visit only.
    auto = ""
    if lang == "en" and redirect_alt is not None:
        auto = (
            "<script>(function(){try{var k='fd-lang';if(localStorage.getItem(k))return;"
            "var n=((navigator.languages&&navigator.languages[0])||navigator.language||'').toLowerCase();"
            "var w=n.indexOf('pl')===0?'pl':'en';localStorage.setItem(k,w);"
            f"if(w==='pl')location.replace('{redirect_alt}');}}catch(e){{}}}})();</script>\n"
        )
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n' if jsonld else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{abs_url(lang, path)}">
<link rel="alternate" hreflang="en" href="{abs_url('en', path)}">
<link rel="alternate" hreflang="pl" href="{abs_url('pl', path)}">
<link rel="alternate" hreflang="x-default" href="{abs_url('en', path)}">
<meta name="theme-color" content="#0b0d12">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{abs_url(lang, path)}">
<meta property="og:image" content="{og_image}">
<meta property="og:locale" content="{t['locale']}">
<meta property="og:locale:alternate" content="{UI[other]['locale']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{p}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{p}apple-touch-icon.png">
<link rel="stylesheet" href="{p}assets/css/style.css">
{auto}{ld}</head>"""


def header(lang, path, p):
    t = UI[lang]
    home = f"{p}{lang_dir(lang)}"
    en_href = f"{p}{path}"
    pl_href = f"{p}pl/{path}"

    def switch(code, href):
        if code == lang:
            return f'<span aria-current="true" lang="{code}">{code.upper()}</span>'
        return (f'<a href="{href}" hreflang="{code}" lang="{code}" data-set-lang="{code}" '
                f'aria-label="{UI[code]["lang_name"]}">{code.upper()}</a>')

    return f"""<a class="skip" href="#main">{t['skip']}</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{home}">{mark()}<span class="brand-word">FD432<span>Games</span></span></a>
    <nav class="nav" aria-label="{t['nav_label']}">
      <a href="{home}#games">{t['nav_games']}</a>
      <a href="{home}#studio">{t['nav_studio']}</a>
    </nav>
    <div class="lang">{switch('en', en_href)}{switch('pl', pl_href)}</div>
  </div>
</header>"""


def footer(lang, p):
    t = UI[lang]
    home = f"{p}{lang_dir(lang)}"
    return f"""<footer class="site-footer">
  <div class="wrap footer-inner">
    <div class="footer-brand">{mark()}<span>© {YEAR} FD432Games. {t['rights']}</span></div>
    <nav class="footer-links" aria-label="Footer">
      <a href="{home}#games">{t['footer_games']}</a>
      <a href="{home}#studio">{t['footer_studio']}</a>
      <a href="{home}privacy/">{t['footer_privacy']}</a>
    </nav>
  </div>
</footer>
<script src="{p}assets/js/main.js" defer></script>
</body>
</html>
"""


def play_url(g, lang):
    return f"{g['play_url']}&hl={lang}"


# ---------------------------------------------------------------- home

def game_media(g, lang, p, href=None):
    c = g[lang]
    if g.get("cover"):
        inner = f'<img src="{img_path(p, g["cover"])}" alt="{esc(c["name"])}" loading="lazy" width="1024" height="500">'
    elif g["orientation"] == "portrait":
        phones = "".join(
            f'<div class="phone"><img src="{img_path(p, s)}" alt="" loading="lazy" width="500" height="1000"></div>'
            for s in shots_for(g, lang)[:3]
        )
        inner = f'<div class="phones">{phones}</div>'
    else:
        inner = f'<img src="{img_path(p, shots_for(g, lang)[0])}" alt="{esc(c["name"])}" loading="lazy" width="1600" height="760">'
    badge = f'<span class="badge">{UI[lang]["in_dev"]}</span>' if g["status"] == "dev" else ""
    if href:
        return f'<a class="game-media {g["orientation"]}" href="{href}" tabindex="-1" aria-hidden="true">{badge}{inner}</a>'
    return f'<div class="game-media {g["orientation"]}">{badge}{inner}</div>'


def game_card(g, lang, p):
    t, c = UI[lang], g[lang]
    if g["status"] == "dev":
        return f"""<article class="game-card wide" style="{game_theme(g)}">
  {game_media(g, lang, p)}
  <div class="game-body">
    <h3>{esc(c['name'])}</h3>
    <p>{esc(c['summary'])}</p>
  </div>
</article>"""
    href = f"{p}{lang_dir(lang)}{g['slug']}/"
    tags = "".join(f"<li>{esc(x)}</li>" for x in c["tags"])
    return f"""<article class="game-card" style="{game_theme(g)}">
  {game_media(g, lang, p, href)}
  <div class="game-body">
    <ul class="tags">{tags}</ul>
    <h3><a href="{href}">{esc(c['name'])}</a></h3>
    <p>{esc(c['summary'])}</p>
    <div class="actions">
      <a class="btn btn-game" href="{play_url(g, lang)}" target="_blank" rel="noopener">{PLAY_ICON}{t['play_short']}</a>
      <a class="btn btn-ghost" href="{href}" aria-label="{esc(t['details_aria'].format(name=c['name']))}">{t['details_btn']}{ARROW}</a>
    </div>
  </div>
</article>"""


def home_page(lang):
    t = UI[lang]
    p = "" if lang == "en" else "../"
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE["name"],
        "url": SITE["url"] + "/",
        "logo": SITE["url"] + "/assets/img/icon-512.png",
    }
    cards = "\n".join(game_card(g, lang, p) for g in GAMES)
    studio_text = "".join(f"<p>{esc(x)}</p>" for x in t["studio_text"])
    studio_tags = "".join(f"<li>{esc(x)}</li>" for x in t["studio_tags"])
    body = f"""
<body>
{header(lang, '', p)}
<main id="main">
  <section class="hero">
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <p class="eyebrow">{t['hero_eyebrow']}</p>
        <h1>{t['hero_title_html']}</h1>
        <p class="lead">{esc(t['hero_lead'])}</p>
        <div class="actions">
          <a class="btn btn-primary" href="#games">{t['cta_games']}{ARROW}</a>
          <a class="btn btn-ghost" href="#studio">{t['cta_studio']}</a>
        </div>
      </div>
      <div class="hero-art">{hero_art()}</div>
    </div>
  </section>

  <section id="games" class="section">
    <div class="wrap">
      <div class="section-head">
        <h2>{t['games_title']}</h2>
        <p>{t['games_lead']}</p>
      </div>
      <div class="games">
{cards}
      </div>
    </div>
  </section>

  <section id="studio" class="section studio">
    <div class="wrap studio-inner">
      <div class="studio-mark">{mark()}</div>
      <div class="studio-text">
        <h2 class="h2">{t['studio_title']}</h2>
        {studio_text}
        <ul class="tags">{studio_tags}</ul>
      </div>
    </div>
  </section>
</main>
"""
    alt = "pl/" if lang == "en" else None
    return head(lang, "", t["home_title"], t["home_desc"], p, jsonld=jsonld, redirect_alt=alt) + body + footer(lang, p)


# ---------------------------------------------------------------- game page

def game_page(g, lang):
    t, c = UI[lang], g[lang]
    p = "../" if lang == "en" else "../../"
    home = f"{p}{lang_dir(lang)}"
    slug, orient = g["slug"], g["orientation"]
    shot_list = shots_for(g, lang)
    shots_abs = [f"{SITE['url']}/assets/img/games/{s}" for s in shot_list]
    sw, sh = g.get("shot_size", [1600, 900])
    alts = c.get("shot_alts", [])
    og = f"{SITE['url']}/assets/img/og-{slug}.jpg" if g.get("cover") else None

    video = g.get("video")
    if video:
        hero_media = f"""<div class="hero-video {orient}">
        <video controls playsinline preload="none" width="{video['width']}" height="{video['height']}"
          poster="{img_path(p, per_lang(video['poster'], lang))}" aria-label="{esc(t['video_label'])} — {esc(c['name'])}">
          <source src="{p}assets/video/{per_lang(video['src'], lang)}" type="video/mp4">
        </video>
      </div>"""
    elif orient == "portrait":
        media = "".join(
            f'<div class="phone"><img src="{img_path(p, s)}" alt="{esc(c["name"])}" width="{sw}" height="{sh}"></div>'
            for s in shot_list[:2]
        )
        hero_media = f'<div class="hero-phones">{media}</div>'
    else:
        hero_media = (f'<div class="hero-shot"><img src="{img_path(p, shot_list[0])}" '
                      f'alt="{esc(c["name"])}" width="{sw}" height="{sh}"></div>')

    tags = "".join(f"<li>{esc(x)}</li>" for x in c["tags"])
    extra_facts = "".join(f"<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>" for a, b in c.get("facts", []))

    def alt(i):
        return f"{c['name']} — {alts[i]}" if i < len(alts) else f"{c['name']} — {i + 1}"

    shots = "".join(
        f'<button class="shot" type="button" data-full="{img_path(p, s)}" '
        f'aria-label="{esc(t["screens_open"].format(n=i + 1, name=c["name"]))}">'
        f'<img src="{img_path(p, s)}" alt="{esc(alt(i))}" loading="lazy" width="{sw}" height="{sh}"></button>'
        for i, s in enumerate(shot_list)
    )
    shots_cls = f"{orient} {'odd' if len(shot_list) % 2 else 'even'}"
    desc = "".join(f"<p>{esc(x)}</p>" for x in c["description"])
    steps = "".join(f"<li><strong>{esc(a)}</strong><span>{esc(b)}</span></li>" for a, b in c["steps"])
    features = "".join(f"<li><h3>{esc(a)}</h3><p>{esc(b)}</p></li>" for a, b in c["features"])

    minis = []
    for o in GAMES:
        if o is g:
            continue
        oc = o[lang]
        thumb = (f'<div class="mini-thumb"><img src="{img_path(p, cover_for(o, lang))}" '
                 f'alt="" loading="lazy"></div>')
        sub = t["in_dev"] if o["status"] == "dev" else oc["tagline"]
        inner = f'{thumb}<div><strong>{esc(oc["name"])}</strong><span>{esc(sub)}</span></div>'
        if o["status"] == "dev":
            minis.append(f'<div class="mini" style="{game_theme(o)}">{inner}</div>')
        else:
            minis.append(f'<a class="mini" style="{game_theme(o)}" href="{home}{o["slug"]}/">{inner}</a>')

    jsonld = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": c.get("full_name", c["name"]),
        "description": c["tagline"],
        "url": abs_url(lang, slug + "/"),
        "image": shots_abs,
        "inLanguage": lang,
        "gamePlatform": "Android",
        "operatingSystem": "Android",
        "applicationCategory": "GameApplication",
        "publisher": {"@type": "Organization", "name": SITE["name"], "url": SITE["url"] + "/"},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }

    body = f"""
<body>
{header(lang, slug + '/', p)}
<main id="main" class="game-page" style="{game_theme(g)}">
  <section class="game-hero {orient}">
    <div class="wrap game-hero-inner">
      <div class="game-hero-copy">
        <nav class="crumbs" aria-label="Breadcrumb">
          <a href="{home}#games">{t['crumb_games']}</a><span aria-hidden="true">/</span><span aria-current="page">{esc(c['name'])}</span>
        </nav>
        <h1>{esc(c['name'])}</h1>
        <p class="lead">{esc(c['tagline'])}</p>
        <ul class="tags">{tags}</ul>
        <div class="actions">
          <a class="btn btn-game" href="{play_url(g, lang)}" target="_blank" rel="noopener">{PLAY_ICON}{t['play_btn']}</a>
          <a class="btn btn-ghost" href="#screens">{t['screens_title']}</a>
        </div>
        <dl class="facts">
          <div><dt>{t['fact_platform']}</dt><dd>Android</dd></div>
          <div><dt>{t['fact_price']}</dt><dd>{t['fact_price_val']}</dd></div>
          <div><dt>{t['fact_mode']}</dt><dd>{t['fact_mode_val']}</dd></div>
          {extra_facts}
        </dl>
      </div>
      {hero_media}
    </div>
  </section>

  <section id="screens" class="section">
    <div class="wrap">
      <h2 class="h2">{t['screens_title']}</h2>
      <div class="shots {shots_cls}">{shots}</div>
    </div>
  </section>

  <section class="section">
    <div class="wrap split">
      <div class="prose">
        <h2 class="h2">{t['about_game']}</h2>
        {desc}
      </div>
      <div>
        <h2 class="h2">{t['howto_title']}</h2>
        <ol class="steps">{steps}</ol>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2 class="h2">{t['features_title']}</h2>
      <ul class="features">{features}</ul>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2 class="h2">{t['more_games']}</h2>
      <div class="mini-games">{''.join(minis)}</div>
    </div>
  </section>
</main>
<dialog class="lightbox" aria-label="{t['screens_title']}">
  <button class="lb-close" type="button">{t['close']}</button>
  <img alt="">
</dialog>
"""
    title = f"{c.get('full_name', c['name'])} — {SITE['name']}"
    alt = "../pl/" + slug + "/" if lang == "en" else None
    return head(lang, slug + "/", title, c["tagline"] + " " + c["summary"], p,
                og_image=og, jsonld=jsonld, redirect_alt=alt) + body + footer(lang, p)


# ---------------------------------------------------------------- misc pages

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "pl": ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca",
           "sierpnia", "września", "października", "listopada", "grudnia"],
}


def format_date(iso, lang):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"


def privacy_page(lang):
    """One privacy policy for all games. Text: src/privacy/<lang>.html, data: content.json."""
    t = UI[lang]
    pv = DATA["privacy"]
    p = "../" if lang == "en" else "../../"
    home = f"{p}{lang_dir(lang)}"
    games = [g for g in GAMES if g.get("privacy")]
    services = pv["services"]

    head_cells = "".join(f'<th scope="col">{esc(s[lang])}</th>' for s in services)
    rows = []
    for g in games:
        c = g[lang]
        used = set(g["privacy"]["services"])
        cells = "".join(
            f'<td class="yes"><span aria-hidden="true">✓</span><span class="sr-only">{t["yes"]}</span></td>'
            if s["id"] in used else
            f'<td class="no"><span aria-hidden="true">—</span><span class="sr-only">{t["no"]}</span></td>'
            for s in services
        )
        name = esc(c.get("full_name", c["name"]))
        rows.append(f'<tr><th scope="row"><a href="{home}{g["slug"]}/">{name}</a>'
                    f'<small>{esc(g.get("package", ""))}</small></th>{cells}</tr>')
    table = (f'<div class="table-wrap"><table class="legal-table games-table">'
             f'<thead><tr><th scope="col">{t["col_game"]}</th>{head_cells}</tr></thead>'
             f'<tbody>{"".join(rows)}</tbody></table></div>')
    consent = "".join(
        f'<li><strong>{esc(g[lang]["name"])}:</strong> {esc(g["privacy"]["consent_path"][lang])}</li>'
        for g in games if g["privacy"].get("consent_path")
    )

    text = (ROOT / "src" / "privacy" / f"{lang}.html").read_text(encoding="utf-8")
    text = text.split("-->", 1)[1].strip() if text.lstrip().startswith("<!--") else text
    for key, val in {
        "updated": format_date(pv["updated"], lang),
        "owner": esc(pv["owner"]),
        "country": esc(per_lang(pv["country"], lang)),
        "email": esc(pv["email"]),
        "games_table": table,
        "consent_list": f'<ul class="consent-list">{consent}</ul>',
    }.items():
        text = text.replace("{{" + key + "}}", val)
    assert "{{" not in text, "unfilled placeholder in privacy text"

    body = f"""
<body>
{header(lang, 'privacy/', p)}
<main id="main" class="legal">
  <div class="wrap legal-inner">
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="{home}">FD432Games</a><span aria-hidden="true">/</span><span aria-current="page">{t['privacy_title']}</span>
    </nav>
    <h1>{t['privacy_title']}</h1>
    {text}
  </div>
</main>
"""
    alt = "../pl/privacy/" if lang == "en" else None
    return head(lang, "privacy/", f"{t['privacy_title']} — {SITE['name']}", t["privacy_desc"], p,
                redirect_alt=alt) + body + footer(lang, p)


def not_found_page():
    p = "/"  # 404.html is served at any URL depth, so links must be root-absolute
    en, pl = UI["en"], UI["pl"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found — FD432Games</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#0b0d12">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
{header('en', '', p)}
<main id="main" class="wrap notfound">
  <div>
    {mark()}
    <h1>Missed shot.</h1>
    <p>This page doesn't exist (anymore). The games are still here, though.</p>
    <div class="actions"><a class="btn btn-primary" href="/#games">{en['cta_games']}{ARROW}</a></div>
    <hr>
    <div lang="pl">
      <h1>Pudło.</h1>
      <p>Tej strony nie ma (już). Gry wciąż są na miejscu.</p>
      <div class="actions"><a class="btn btn-ghost" href="/pl/#games">{pl['cta_games']}</a></div>
    </div>
  </div>
</main>
{footer('en', p)}"""


def redirect_page(target):
    url = f"{SITE['url']}/{target}/"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="{url}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=../{target}/">
<script>location.replace("../{target}/" + location.hash);</script>
</head>
<body><p><a href="../{target}/">{url}</a></p></body>
</html>
"""


def sitemap():
    paths = [""] + [g["slug"] + "/" for g in GAMES if g["status"] != "dev"] + ["privacy/"]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path in paths:
        for lang in LANGS:
            out.append(f"  <url><loc>{abs_url(lang, path)}</loc>")
            for alt in LANGS:
                out.append(f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{abs_url(alt, path)}"/>')
            out.append("  </url>")
    out.append("</urlset>\n")
    return "\n".join(out)


# ---------------------------------------------------------------- write

def write(rel, text):
    f = ROOT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8", newline="\n")
    print("  wrote", rel)


def main():
    print("Building fd432games.com")
    for lang in LANGS:
        write(f"{lang_dir(lang)}index.html", home_page(lang))
        for g in GAMES:
            if g["status"] != "dev":
                write(f"{lang_dir(lang)}{g['slug']}/index.html", game_page(g, lang))
        write(f"{lang_dir(lang)}privacy/index.html", privacy_page(lang))
    for old, new in REDIRECTS.items():
        write(f"{old}/index.html", redirect_page(new))
    write("404.html", not_found_page())
    write("sitemap.xml", sitemap())
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    write(".nojekyll", "")
    print("Done.")


if __name__ == "__main__":
    main()
