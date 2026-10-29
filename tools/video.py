#!/usr/bin/env python3
"""Renderar ett serieinlägg som Reel (1080x1920, 9:16, 30 fps, H.264) från post.json.

Användning: python3 tools/video.py posts/2026-10-30/post.json
Skriver bredvid post.json:
  reel.mp4       videon
  cover.jpg      omslaget = dagens tredjedel av Mintsolen (tools/panorama.py), syns i profilrutnätet
  check-NN.jpg   en stillbild per scen i slutläge, för kontroll med Read (versioneras inte)

"slides" i post.json blir scener i tur och ordning, med samma bildtyper som render.py.
Första scenen ska vara {"type": "panel"}: Mintsolen glider in uppifrån och landar exakt i omslaget.
Scenerna läggs i ett 4:5-fält mitt i bilden (y 285..1635), så att inget hamnar under Reels-gränssnittet.
Avbryter med RENDERFEL om text inte får plats.
"""
import json, pathlib, shutil, subprocess, sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import render, panorama  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from PIL import Image  # noqa: E402

VW, VH, FPS = 1080, 1920, 30
TOP = (VH - render.H) // 2  # 285
STAGGER, ANIM = 0.14, 0.5

VIDEO_CSS = f"""
body{{background:var(--bg);width:{VW}px;height:{VH}px;overflow:hidden}}
.frame{{position:absolute;left:0;top:{TOP}px}}
.n,.hint{{display:none}}
.a{{animation:up {ANIM}s cubic-bezier(.2,.8,.2,1) both paused}}
@keyframes up{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:none}}}}
.sun{{animation:sun 1.2s cubic-bezier(.16,1,.3,1) both paused}}
@keyframes sun{{from{{transform:translateY(-1500px)}}to{{transform:none}}}}
{panorama.STYLE}
"""

# Element som animeras in, i ordning (förskjutna med STAGGER sekunder).
REVEAL = [".kicker", "h1", "blockquote", ".sub", ".by", ".pills span", ".row", ".steps li", ".url"]

REVEAL_JS = """([sel, stagger]) => {
  let i = 0;
  for (const s of sel) for (const el of document.querySelectorAll(s)) {
    el.classList.add('a'); el.style.animationDelay = (0.15 + i++ * stagger) + 's';
  }
  return i;
}"""
SEEK_JS = "t => { document.getAnimations().forEach(a => a.currentTime = t); }"


def duration(s, items):
    t = s["type"]
    if t == "panel":
        return 2.6
    if t == "cta":
        return 3.2
    base = 4.2 if t == "quote" else 3.6
    return base + max(0, items - 3) * 0.25


def scene_html(post, s, i, n, theme, k):
    head = (f"<html lang='sv'><head><meta charset='utf-8'><style>{render.CSS}{render.THEMES[theme]}{VIDEO_CSS}</style>"
            "</head><body>")
    if s["type"] == "panel":
        svg = (f'<svg width="{VW}" height="{VH}" viewBox="0 0 {VW} {VH}" style="position:absolute;inset:0">'
               f'<g class="sun">{panorama.sun_svg(k)}</g>'
               f'<g class="a" style="animation-delay:.9s">{panorama.texts_svg(k)}</g></svg>')
        return head + svg + "</body></html>"
    return head + f"<div class='frame'><div class='s'>{render.slide_html(s, i, n, False)}</div></div></body></html>"


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main(spec_path):
    spec_path = pathlib.Path(spec_path).resolve()
    out_dir = spec_path.parent
    post = json.loads(spec_path.read_text(encoding="utf-8"))
    slides = post["slides"]
    ser = render.theme_cfg().get("series") or {}
    dates = ser.get("dates", [])
    if post.get("date") not in dates:
        sys.exit("video.py är bara för seriedatum (tools/theme.json -> series.dates)")
    if not slides or slides[0]["type"] != "panel" or slides[-1]["type"] != "cta":
        sys.exit("Första scenen ska vara panel och sista cta")
    k = len(dates) - 1 - dates.index(post["date"])  # senast publicerad hamnar längst till vänster
    render.KICKER = render.series_label(post)
    theme = render.pick_theme(post)

    # Omslag: dagens tredjedel av panoramat.
    pano = Image.open(TOOLS / ser["panorama"]).convert("RGB")
    pano.crop((k * VW, 0, (k + 1) * VW, VH)).save(out_dir / "cover.jpg", "JPEG", quality=95, subsampling=0)

    mp4 = out_dir / "reel.mp4"
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
           "-map", "0:v", "-map", "1:a", "-shortest",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-g", str(FPS), "-keyint_min", str(FPS), "-sc_threshold", "0", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(mp4)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    problems, total = [], 0.0
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": VW, "height": VH})
        for i, s in enumerate(slides, 1):
            hp = out_dir / f"_scene{i:02d}.html"
            hp.write_text(scene_html(post, s, i, len(slides), theme, k), encoding="utf-8")
            pg.goto(hp.as_uri())
            pg.evaluate("document.fonts.ready.then(()=>1)")
            pg.wait_for_timeout(200)
            items = 0
            if s["type"] != "panel":
                items = pg.evaluate(REVEAL_JS, [REVEAL, STAGGER])
                pg.evaluate(SEEK_JS, 100000)  # slutläge för mätning
                pg.evaluate("document.querySelector('.frame').style.top = '0px'")  # FIT_JS mäter i 4:5-fältets koordinater
                fit = pg.evaluate(render.FIT_JS)
                pg.evaluate(f"document.querySelector('.frame').style.top = '{TOP}px'")
                if fit["over"] or fit["wide"]:
                    problems.append(f"scen {i}: texten får inte plats ({fit})")
            dur = duration(s, items)
            pg.evaluate(SEEK_JS, 100000)
            pg.screenshot(path=str(out_dir / f"check-{i:02d}.jpg"), type="jpeg", quality=90)
            for f in range(round(dur * FPS)):
                pg.evaluate(SEEK_JS, f * 1000 / FPS)
                enc.stdin.write(pg.screenshot(type="png"))
            total += dur
            hp.unlink()
        b.close()
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("ffmpeg misslyckades")
    if problems:
        sys.exit("RENDERFEL – korta texten:\n" + "\n".join(problems))
    print(json.dumps({"theme": theme, "series": render.KICKER, "tile": ["vänster", "mitten", "höger"][k],
                      "seconds": round(total, 1), "video": str(mp4), "cover": str(out_dir / "cover.jpg")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
