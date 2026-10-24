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
:root{{--bg:#faf9f5;--fg:#141413;--fg2:#30302e;--fg3:#5e5d59;--fg4:#87867f;--b2:#dedcd1;--mint:#0bbfa6}}
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
"""

# M-ikonen från Mynths designsystem (artifact "Mynth LinkedIn-banner", Profilbild)
LOGO = ('<svg class="logo" viewBox="0 0 348 243" aria-label="Mynth"><polygon fill="#0a0a0c" '
        'points="0,0 0,243 49.5,243 49.5,71 110.5,243 151.5,243 212.5,71 212.5,243 262,243 262,0 '
        '186.5,0 131,168 75.5,0"/><circle fill="#56bca6" cx="324" cy="219" r="24"/></svg>')

# Krymper rubriken tills innehållet slutar minst 90px ovanför hårlinjen.
FIT_JS = f"""() => {{
  const c = document.querySelector('.c'); const h = c.querySelector('h1, blockquote');
  const limit = {LINE_Y} - 90; let size = h ? parseFloat(getComputedStyle(h).fontSize) : 0;
  while (h && c.getBoundingClientRect().bottom > limit && size > 60) {{ size -= 4; h.style.fontSize = size + 'px'; }}
  const over = c.getBoundingClientRect().bottom > limit;
  const r = c.getBoundingClientRect().right > {W - SIDE + 2};
  return {{bottom: c.getBoundingClientRect().bottom, size, over, wide: r}};
}}"""


def esc(t):
    return html.escape(t or "").replace("\n", "<br>")


def chrome(i, n, big, hint):
    d, gap = (170, 60) if big else (64, 24)
    w = 3 * d + 2 * gap
    left = W - SIDE - w
    dots = "".join(f'<i style="width:{d}px;height:{d}px"></i>' for _ in range(3))
    return (LOGO + f'<div class="n">{i:02d} / {n:02d}</div>'
            + f'<div class="line" style="top:{LINE_Y}px;left:{left - 48}px"></div>'
            + f'<div class="dots" style="left:{left}px;top:{LINE_Y - d}px;gap:{gap}px">{dots}</div>'
            + f'<div class="hint" style="top:{LINE_Y - 34}px">{esc(hint)}</div>')


def slide_html(s, i, n):
    t = s["type"]
    last = i == n
    hint = "Länk i bio" if last else "Svep →"
    title = esc(s.get("title"))
    em = f'<br><em>{esc(s["em"])}</em>' if s.get("em") else ""
    if t in ("cover", "cta"):
        body = f'<div class="c" style="top:320px"><h1>{title}{em}</h1>'
        if s.get("url"):
            body += f'<div class="url">{esc(s["url"])}</div>'
        return chrome(i, n, True, hint) + body + "</div>"
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
    if not 2 <= len(slides) <= 10:
        sys.exit("Karusellen måste ha 2–10 bilder (Instagram API-gräns).")
    out, problems = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(slides, 1):
            hp = spec_path.parent / f"_{i:02d}.html"
            hp.write_text(f"<html lang='sv'><head><meta charset='utf-8'><style>{CSS}</style></head>"
                          f"<body><div class='s'>{slide_html(s, i, len(slides))}</div></body></html>", encoding="utf-8")
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
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1])
