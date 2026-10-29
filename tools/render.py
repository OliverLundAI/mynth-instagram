#!/usr/bin/env python3
"""Renderar en Mynth-karusell från post.json till JPEG (1080x1350, Instagram 4:5).

Användning: python3 tools/render.py posts/2026-10-25/post.json
Skriver 01.jpg, 02.jpg ... bredvid post.json. Avbryter med fel om text inte får plats.

Bildtyper i post.json -> "slides":
  {"type":"cover", "title":"Rad 1\\nRad 2", "em":"kursiv rad"}           stora prickar
  {"type":"text",  "title":"...", "sub":"...", "pills":["..."]}           små prickar
  {"type":"text",  "title":"...", "sub":"...", "rows":[["Rubrik","Text"]]}
  {"type":"text",  "title":"...", "sub":"...", "steps":["...","..."]}     numrerad lista
  {"type":"quote", "quote":"...", "by":"..."}                             stort serifcitat (bara egna påståenden)
  {"type":"cta",   "title":"...", "em":"...", "url":"mynth.se"}          stora prickar
  {"type":"panel"}   bara i serier: dagens tredjedel av seriens panoramabild (tre-i-en i profilrutnätet)

Tema: väljs från tools/theme.json utifrån datum: "series" -> black (WHOOP-inspirerat, versal grotesk,
serieetikett "Titel · Del n/N" överst på varje bild), "dark_dates" -> dark, annars light.
"""
import html, json, pathlib, sys
from playwright.sync_api import sync_playwright
from PIL import Image

TOOLS = pathlib.Path(__file__).resolve().parent
FONTS = (TOOLS / "fonts").as_uri()
W, H, LINE_Y, SIDE = 1080, 1350, 1160, 96

CSS = f"""
@font-face{{font-family:Switzer;src:url({FONTS}/switzer-400.woff2);font-weight:400}}
@font-face{{font-family:Switzer;src:url({FONTS}/switzer-500.woff2);font-weight:500}}
@font-face{{font-family:Switzer;src:url({FONTS}/switzer-600.woff2);font-weight:600}}
@font-face{{font-family:Newsreader;src:url({FONTS}/newsreader-normal.woff2);font-weight:200 800;font-style:normal}}
@font-face{{font-family:Newsreader;src:url({FONTS}/newsreader-italic.woff2);font-weight:200 800;font-style:italic}}
:root{{--bg:#faf9f5;--fg:#141413;--fg2:#30302e;--fg3:#5e5d59;--fg4:#87867f;--b2:#dedcd1;--mint:#0bbfa6;--logo:#0a0a0c}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:var(--bg)}}
.s{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:var(--bg);
   font-family:Switzer,'Helvetica Neue',Arial,sans-serif;color:var(--fg);font-feature-settings:'pnum','lnum','liga'}}
.logo{{position:absolute;left:{SIDE}px;top:96px;height:44px}}
.n{{position:absolute;right:{SIDE}px;top:104px;font-size:26px;color:var(--fg4);letter-spacing:.01em}}
.c{{position:absolute;left:{SIDE}px;right:{SIDE}px;top:300px}}
h1{{font-family:Newsreader,Georgia,serif;font-weight:400;font-size:116px;line-height:1.04;
    letter-spacing:-.01em;font-variation-settings:'opsz' 72;text-wrap:balance}}
h1 em{{font-style:italic;color:var(--fg3)}}
.sub{{font-size:38px;line-height:1.45;color:var(--fg3);margin-top:40px;max-width:820px;text-wrap:pretty}}
.pills{{display:flex;flex-wrap:wrap;gap:14px;margin-top:56px;max-width:860px}}
.pills span{{border:2px solid var(--b2);border-radius:9999px;padding:14px 28px;font-size:30px;font-weight:500;color:var(--fg2)}}
.rows{{margin-top:56px;border-top:2px solid var(--b2)}}
.row{{padding:30px 0;border-bottom:2px solid var(--b2)}}
.row b{{display:block;font-weight:600;font-size:32px;margin-bottom:8px}}
.row span{{display:block;max-width:760px;font-size:30px;line-height:1.45;color:var(--fg3);text-wrap:pretty}}
.steps{{margin-top:56px;list-style:none;counter-reset:s}}
.steps li{{counter-increment:s;display:flex;gap:28px;padding:22px 0;border-top:2px solid var(--b2);font-size:32px;line-height:1.4;color:var(--fg2)}}
.steps li:last-child{{border-bottom:2px solid var(--b2)}}
.steps li::before{{content:counter(s,decimal-leading-zero);font-weight:500;color:var(--fg4);min-width:48px}}
blockquote{{font-family:Newsreader,Georgia,serif;font-size:84px;line-height:1.12;letter-spacing:-.01em;
    font-variation-settings:'opsz' 72;text-wrap:balance}}
.by{{margin-top:40px;font-size:30px;color:var(--fg3)}}
.url{{font-family:Newsreader,Georgia,serif;font-size:64px;font-variation-settings:'opsz' 48;margin-top:48px}}
.line{{position:absolute;right:0;height:2px;background:var(--b2)}}
.dots{{position:absolute;display:flex;align-items:flex-end}}
.dots i{{display:block;border-radius:50%;background:var(--mint)}}
.hint{{position:absolute;left:{SIDE}px;font-size:26px;color:var(--fg3);letter-spacing:.01em}}
.kicker{{position:absolute;left:{SIDE}px;top:222px;font-size:26px;font-weight:600;letter-spacing:.16em;
    text-transform:uppercase;color:var(--mint)}}
"""

# M-ikonen från Mynths designsystem (artifact "Mynth LinkedIn-banner", Profilbild)
LOGO = ('<svg class="logo" viewBox="0 0 348 243" aria-label="Mynth"><polygon style="fill:var(--logo)" '
        'points="0,0 0,243 49.5,243 49.5,71 110.5,243 151.5,243 212.5,71 212.5,243 262,243 262,0 '
        '186.5,0 131,168 75.5,0"/><circle fill="#56bca6" cx="324" cy="219" r="24"/></svg>')

# Teman. Ljust är standard. "theme" i post.json styr; saknas det används tools/theme.json:
# datum i en serie ("series" -> "dates") -> black, datum i "dark_dates" -> dark, annars light.
THEMES = {
    "light": "",
    "dark": ":root{--bg:#0a0a0c;--fg:#faf9f5;--fg2:#dedcd1;--fg3:#b0aea5;--fg4:#87867f;--b2:#3a3a37;--mint:#0bbfa6;--logo:#faf9f5}",
    # WHOOP-inspirerat: kolsvart, stor versal grotesk, mint som enda accent. Används för serier.
    "black": (":root{--bg:#000;--fg:#fff;--fg2:#e8e8e8;--fg3:#a6a6a6;--fg4:#6e6e6e;--b2:#2b2b2b;--mint:#0bbfa6;--logo:#fff}"
              "h1{font-family:Switzer,'Helvetica Neue',Arial,sans-serif;font-weight:600;text-transform:uppercase;"
              "font-size:92px;line-height:.96;letter-spacing:-.025em;font-variation-settings:normal}"
              "h1,blockquote{word-spacing:.06em}.c.big h1{font-size:132px;line-height:.92;letter-spacing:-.03em}"
              "h1 em{font-style:normal;color:var(--mint)}"
              "blockquote{font-family:Switzer,'Helvetica Neue',Arial,sans-serif;font-weight:600;text-transform:uppercase;"
              "font-size:86px;line-height:.98;letter-spacing:-.025em;font-variation-settings:normal}"
              ".by{text-transform:uppercase;letter-spacing:.14em;font-size:24px;font-weight:500}"
              ".url{font-family:Switzer,'Helvetica Neue',Arial,sans-serif;font-weight:600;font-size:52px;letter-spacing:-.01em}"
              ".n{letter-spacing:.14em}.hint{text-transform:uppercase;letter-spacing:.16em;font-size:22px;font-weight:500}"
              ".row b{text-transform:uppercase;letter-spacing:.06em;font-size:28px}"
              ".pills span{text-transform:uppercase;letter-spacing:.08em;font-size:24px;font-weight:600}"),
}


def theme_cfg():
    cfg = TOOLS / "theme.json"
    return json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}


def series_label(post):
    """Serie i flera delar: theme.json -> "series": {"title": "...", "dates": [...]}.
    Ger t.ex. "Synas i AI · Del 1/3" för första datumet, annars None."""
    ser = theme_cfg().get("series") or {}
    dates = ser.get("dates", [])
    if post.get("date") not in dates:
        return None
    return f"{ser['title']} · Del {dates.index(post['date']) + 1}/{len(dates)}"


def panel_image(post):
    """Tre-i-en: dagens tredjedel av panoramabilden i theme.json -> series.panorama (se tools/panorama.py).
    Senast publicerade hamnar längst till vänster i profilrutnätet, så första datumet blir högra delen."""
    ser = theme_cfg().get("series") or {}
    dates = ser.get("dates", [])
    if post.get("date") not in dates or not ser.get("panorama"):
        sys.exit("bildtypen panel kräver att datumet ingår i en serie med panorama i tools/theme.json")
    k = len(dates) - 1 - dates.index(post["date"])
    return Image.open(TOOLS / ser["panorama"]).convert("RGB").crop((k * 1012, 0, k * 1012 + W, H))


def pick_theme(post):
    t = post.get("theme")
    if not t:
        if series_label(post):
            t = theme_cfg().get("series", {}).get("theme", "black")
        else:
            t = "dark" if post.get("date") in theme_cfg().get("dark_dates", []) else "light"
    if t not in THEMES:
        sys.exit(f"okänt tema: {t}")
    return t


def small_dots(post):
    """Små prickar (som på textbilderna) även på cover/cta för datum i theme.json -> small_dots_dates."""
    cfg = TOOLS / "theme.json"
    dates = json.loads(cfg.read_text(encoding="utf-8")).get("small_dots_dates", []) if cfg.exists() else []
    return post.get("date") in dates


# Krymper rubriken tills innehållet slutar minst 90px ovanför hårlinjen.
FIT_JS = f"""() => {{
  const c = document.querySelector('.c'); const h = c.querySelector('h1, blockquote');
  const limit = {LINE_Y} - 90; let size = h ? parseFloat(getComputedStyle(h).fontSize) : 0;
  while (h && c.getBoundingClientRect().bottom > limit && size > 60) {{ size -= 4; h.style.fontSize = size + 'px'; }}
  while (h && h.scrollWidth > h.clientWidth + 1 && size > 60) {{ size -= 4; h.style.fontSize = size + 'px'; }}
  const over = c.getBoundingClientRect().bottom > limit;
  const r = c.getBoundingClientRect().right > {W - SIDE + 2};
  const r2 = r || (h && h.scrollWidth > h.clientWidth + 1);
  return {{bottom: c.getBoundingClientRect().bottom, size, over, wide: r2}};
}}"""


def esc(t):
    return html.escape(t or "").replace("\n", "<br>")


KICKER = None  # serieetikett, sätts i main()


def chrome(i, n, big, hint):
    d, gap = (170, 60) if big else (64, 24)
    w = 3 * d + 2 * gap
    left = W - SIDE - w
    dots = "".join(f'<i style="width:{d}px;height:{d}px"></i>' for _ in range(3))
    return (LOGO + f'<div class="n">{i:02d} / {n:02d}</div>'
            + f'<div class="line" style="top:{LINE_Y}px;left:{left - 48}px"></div>'
            + f'<div class="dots" style="left:{left}px;top:{LINE_Y - d}px;gap:{gap}px">{dots}</div>'
            + f'<div class="hint" style="top:{LINE_Y - 34}px">{esc(hint)}</div>'
            + (f'<div class="kicker">{esc(KICKER)}</div>' if KICKER else ""))


def slide_html(s, i, n, small=False):
    t = s["type"]
    last = i == n
    hint = "Länk i bio" if last else "Svep →"
    title = esc(s.get("title"))
    em = f'<br><em>{esc(s["em"])}</em>' if s.get("em") else ""
    if t in ("cover", "cta"):
        body = f'<div class="c big" style="top:320px"><h1>{title}{em}</h1>'
        if s.get("url"):
            body += f'<div class="url">{esc(s["url"])}</div>'
        return chrome(i, n, not small, hint) + body + "</div>"
    if t == "quote":
        by = f'<p class="by">{esc(s["by"])}</p>' if s.get("by") else ""
        return chrome(i, n, False, hint) + f'<div class="c"><blockquote>{esc(s["quote"])}</blockquote>{by}</div>'
    if t == "text":
        body = f'<div class="c"><h1>{title}{em}</h1>'
        if s.get("sub"):
            body += f'<p class="sub">{esc(s["sub"])}</p>'
        if s.get("pills"):
            body += '<div class="pills">' + "".join(f"<span>{esc(p)}</span>" for p in s["pills"]) + "</div>"
        if s.get("rows"):
            body += '<div class="rows">' + "".join(
                f'<div class="row"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in s["rows"]) + "</div>"
        if s.get("steps"):
            body += '<ol class="steps">' + "".join(f"<li>{esc(x)}</li>" for x in s["steps"]) + "</ol>"
        return chrome(i, n, False, hint) + body + "</div>"
    raise ValueError(f"okänd bildtyp: {t}")


def main(spec_path):
    spec_path = pathlib.Path(spec_path).resolve()
    post = json.loads(spec_path.read_text(encoding="utf-8"))
    slides = post["slides"]
    global KICKER
    KICKER = series_label(post)
    theme = pick_theme(post)
    small = small_dots(post)
    if not 2 <= len(slides) <= 10:
        sys.exit("Karusellen måste ha 2–10 bilder (Instagram API-gräns).")
    out, problems = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(slides, 1):
            if s["type"] == "panel":
                jpg = spec_path.parent / f"{i:02d}.jpg"
                panel_image(post).save(jpg, "JPEG", quality=92, optimize=True)
                out.append(str(jpg))
                continue
            hp = spec_path.parent / f"_{i:02d}.html"
            hp.write_text(f"<html lang='sv'><head><meta charset='utf-8'><style>{CSS}{THEMES[theme]}</style></head>"
                          f"<body><div class='s'>{slide_html(s, i, len(slides), small)}</div></body></html>", encoding="utf-8")
            pg.goto(hp.as_uri())
            pg.evaluate("document.fonts.ready.then(()=>1)")
            pg.wait_for_timeout(250)
            fit = pg.evaluate(FIT_JS)
            if fit["over"] or fit["wide"]:
                problems.append(f"bild {i}: texten får inte plats ({fit})")
            png = spec_path.parent / f"_{i:02d}.png"
            pg.screenshot(path=str(png))
            jpg = spec_path.parent / f"{i:02d}.jpg"
            Image.open(png).convert("RGB").save(jpg, "JPEG", quality=92, optimize=True)
            png.unlink(); hp.unlink()
            out.append(str(jpg))
        b.close()
    if problems:
        sys.exit("RENDERFEL – korta texten:\n" + "\n".join(problems))
    print(json.dumps({"theme": theme, "small_dots": small, "series": KICKER, "images": out}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
