#!/usr/bin/env python3
"""Tre-i-en (WHOOP-inspirerat delat rutnät): en panoramabild som delas på tre inläggs omslag.

Användning: python3 tools/panorama.py tools/series/<namn>.jpg
Bilden är 3104x1350. Omslag k (0 = vänster i profilrutnätet) = x k*1012 .. k*1012+1080.
Instagram visar 4:5-inlägg som 3:4 i profilrutnätet (beskärs 34 px per sida), så de synliga
delarna (k*1012+34 .. k*1012+1046) möts sömlöst över raden.
"""
import math, pathlib, sys
from playwright.sync_api import sync_playwright

TOOLS = pathlib.Path(__file__).resolve().parent
FONTS = (TOOLS / "fonts").as_uri()
PW, PH, TW, CROP = 3104, 1350, 1080, 34
STEP = 1012


def vis(k):  # synligt intervall för omslag k i panoramakoordinater
    return k * STEP + CROP, k * STEP + TW - CROP


TEXTS = [  # (omslag, x i synlig yta, y, ankare, text, klass)
    (0, 96, 150, "start", "Synas i AI", "k"),
    (1, 506, 1215, "middle", "Rekommenderar AI er eller konkurrenten?", "t"),
    (2, 916, 1215, "end", "mynth.se", "u"),
]


STOPS = [(0, (0x0b, 0x6e, 0x63)), (.55, (0x0b, 0xbf, 0xa6)), (1, (0x9b, 0xf5, 0xe1))]


def mix(t):
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if t <= b:
            u = (t - a) / (b - a)
            return "#" + "".join(f"{round(x + (y - x) * u):02x}" for x, y in zip(ca, cb))
    return "#9bf5e1"


BG = """<defs>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset=".25" stop-color="#000" stop-opacity=".15"/>
  <stop offset=".62" stop-color="#000" stop-opacity="1"/><stop offset="1" stop-color="#000" stop-opacity="1"/>
</linearGradient>
<linearGradient id="hue" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#0bbfa6"/><stop offset=".5" stop-color="#11a6a0"/><stop offset="1" stop-color="#2f7fd8"/>
</linearGradient>
</defs>
<rect width="3104" height="1350" fill="url(#hue)"/>
<rect width="3104" height="1350" fill="url(#fade)"/>
"""


def svg():
    out = []
    boxes = []
    for k, x, y, anc, txt, cls in TEXTS:
        ax = vis(k)[0] + x
        out.append(f'<text x="{ax}" y="{y}" text-anchor="{anc}" class="{cls}">{txt}</text>')
        boxes.append((ax, y))
    # Prickfält: en mjuk våg av mintprickar som löper över alla tre omslagen.
    sp = 46
    for j in range(0, PH // sp + 2):
        for i in range(0, PW // sp + 2):
            x, y = i * sp + 10, j * sp + 8
            y0 = 640 + 250 * math.sin(2 * math.pi * x / PW * 1.15 + 0.9)
            d = abs(y - y0)
            r = 17 * math.exp(-(d / 150) ** 2)
            if y < 220 or y > 1110:
                continue
            if r > 4.2:
                # Färg efter storlek: djup teal i kanten, mint i mitten, ljus mint i vågens kärna.
                t = min(1, (r - 4.2) / 12)
                out.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{mix(t)}"/>')
            else:
                out.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#ffffff" fill-opacity=".12"/>')
    return "\n".join(out)


def main(dst):
    html = f"""<html><head><meta charset='utf-8'><style>
@font-face{{font-family:Switzer;src:url({FONTS}/switzer-500.woff2);font-weight:500}}
@font-face{{font-family:Switzer;src:url({FONTS}/switzer-600.woff2);font-weight:600}}
*{{margin:0}} body{{background:#000;width:{PW}px;height:{PH}px}}
text{{font-family:Switzer,Arial,sans-serif;text-transform:uppercase;letter-spacing:.16em}}
.k{{font-size:30px;font-weight:600;fill:#ffffff}}
.t{{font-size:30px;font-weight:600;fill:#f2f2f0}}
.u{{font-size:30px;font-weight:500;fill:#cfeee7;text-transform:none;letter-spacing:.06em}}
</style></head><body><svg width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}">
{BG}{svg()}</svg></body></html>"""
    dst = pathlib.Path(dst).resolve()
    tmp = dst.with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": PW, "height": PH})
        pg.goto(tmp.as_uri())
        pg.evaluate("document.fonts.ready.then(()=>1)")
        pg.wait_for_timeout(300)
        png = dst.with_suffix(".png")
        pg.screenshot(path=str(png))
        b.close()
    from PIL import Image
    Image.open(png).convert("RGB").save(dst, "JPEG", quality=94, optimize=True)
    png.unlink(); tmp.unlink()
    print(dst)


if __name__ == "__main__":
    main(sys.argv[1])
