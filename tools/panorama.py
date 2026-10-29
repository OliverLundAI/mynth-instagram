#!/usr/bin/env python3
"""Tre-i-en ("Mintsolen"): en panoramabild som delas på tre Reels-omslag i profilrutnätet.

Användning: python3 tools/panorama.py tools/series/<namn>.png

Panoramat är 3240x1920. Omslag k (0 = vänster i profilrutnätet) = x k*1080 .. (k+1)*1080, alltså
ett 9:16-omslag per Reel. Profilrutnätet visar mitten i 3:4 (y 240..1680), så motivet och texterna
ligger där och de tre synliga delarna möts sömlöst över raden.

sun_svg() och texts_svg() används också av tools/video.py, så att videons intro landar exakt i omslaget.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright
from PIL import Image

TOOLS = pathlib.Path(__file__).resolve().parent
FONTS = (TOOLS / "fonts").as_uri()
TW, TH = 1080, 1920          # ett Reels-omslag (9:16)
PW, PH = 3 * TW, TH          # hela panoramat
VIS_Y = (TH - TW * 4 // 3) // 2   # 240: överkant för det som syns i rutnätet (3:4)
VIS_H = TW * 4 // 3               # 1440
MINT = "#0bbfa6"

# Mintsolen: en jätteskiva som går in uppifrån och sveper över hela raden.
SUN_R = 2453
SUN_CX = PW // 2
SUN_CY = VIS_Y + round(VIS_H * 2 / 3) - SUN_R   # nedersta punkten två tredjedelar ner i rutan

TEXT_Y = VIS_Y + round(VIS_H * 0.9)
TEXTS = [  # (omslag, x i omslaget, ankare, text, klass)
    (0, 96, "start", "Synas i AI", "k"),
    (1, TW // 2, "middle", "Rekommenderar AI er eller konkurrenten?", "t"),
    (2, TW - 96, "end", "mynth.se", "u"),
]

STYLE = f"""
@font-face{{font-family:Switzer;src:url({FONTS}/switzer-500.woff2);font-weight:500}}
@font-face{{font-family:Switzer;src:url({FONTS}/switzer-600.woff2);font-weight:600}}
.pt{{font-family:Switzer,Arial,sans-serif;font-size:32px;letter-spacing:.16em;text-transform:uppercase;font-weight:600;fill:#fff}}
.pt.k{{fill:{MINT}}} .pt.u{{text-transform:none;letter-spacing:.06em;font-weight:500;fill:#bdbdbd}}
"""


def sun_svg(k=None):
    """Solen i panoramakoordinater, eller förskjuten till omslag k (0..2) om k anges."""
    dx = -k * TW if k is not None else 0
    return f'<circle cx="{SUN_CX + dx}" cy="{SUN_CY}" r="{SUN_R}" fill="{MINT}"/>'


def texts_svg(k=None):
    out = []
    for t, x, anc, txt, cls in TEXTS:
        if k is not None and t != k:
            continue
        ax = x + (t * TW if k is None else 0)
        out.append(f'<text x="{ax}" y="{TEXT_Y}" text-anchor="{anc}" class="pt {cls}">{txt}</text>')
    return "".join(out)


def main(dst):
    dst = pathlib.Path(dst).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    html = (f"<html><head><meta charset='utf-8'><style>*{{margin:0}}body{{background:#000}}{STYLE}</style></head><body>"
            f'<svg width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}"><rect width="{PW}" height="{PH}" fill="#000"/>'
            f"{sun_svg()}{texts_svg()}</svg></body></html>")
    tmp = dst.with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    png = dst.with_name(dst.stem + "_2x.png")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": PW, "height": PH}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.evaluate("document.fonts.ready.then(()=>1)")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(png))
        b.close()
    # Dubbel upplösning, nedskalad för skarpa kanter. Sparas förlustfritt.
    Image.open(png).convert("RGB").resize((PW, PH), Image.LANCZOS).save(dst, "PNG", optimize=True)
    png.unlink(); tmp.unlink()
    print(dst)


if __name__ == "__main__":
    main(sys.argv[1])
