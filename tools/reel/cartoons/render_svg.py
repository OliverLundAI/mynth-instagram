#!/usr/bin/env python3
"""Renderar en egenritad teckning (src/*.svg) till PNG i hög upplösning för tools/video.py.

Användning: python3 tools/reel/cartoons/render_svg.py src/2026-10-30-skyltfonstret.svg 2026-10-30.png
"""
import pathlib, re, sys
from playwright.sync_api import sync_playwright

src, dst = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', src.read_text()).group(1).split()]
W = 2000
H = round(W * vb[3] / vb[2])
html = dst.with_suffix(".html")
html.write_text(f"<html><body style='margin:0;background:#fff'><img src='{src.as_uri()}' width={W} height={H}></body></html>")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": W, "height": H})
    pg.goto(html.as_uri())
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(dst))
    b.close()
html.unlink()
print(dst, W, H)
