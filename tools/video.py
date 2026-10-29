#!/usr/bin/env python3
"""Renderar ett serieinlägg som Reel (1080x1920, 9:16, 30 fps, H.264 + AAC) från post.json.

Användning: python3 tools/video.py posts/2026-10-30/post.json
Skriver bredvid post.json:
  reel.mp4       videon, med ljudeffekter och musikbädd (tools/reel/sfx.py)
  cover.jpg      omslaget = dagens tredjedel av Mintsolen (tools/panorama.py), syns i profilrutnätet
  check-NN.jpg   en stillbild per scen i ett läge där allt syns, för kontroll med Read (versioneras inte)

"slides" i post.json blir scener i tur och ordning. Scenerna är tecknade demonstrationer i tools/reel/stage.js:
  {"type":"panel"}                                         Mintsolen glider in och landar i omslaget (alltid först)
  {"type":"ask", "caption":"...", "question":"...", "outcome":"missing"|"question"}
        en kund skriver en fråga till en AI-assistent, svaret räknar upp några alternativ (utan namn),
        förstoringsglaset letar efter "Ert företag". missing = stämpeln "Inte nämnt", question = "Nämns ni?"
  {"type":"sources", "caption":"..."}                      AI:n hämtar sin bild av företaget från webbplats,
        artiklar, databaser, redaktioner och återförsäljare, och formulerar ett svar
  {"type":"checklist", "caption":"...", "items":["...", ...]}   2–4 punkter som bockas av
  {"type":"text", "title":"...", "sub":"..."}              kort påstående i stor text
  {"type":"quote", "quote":"...", "by":"Mynth"}            eget påstående
  {"type":"cartoon"}        dagens skämtteckning: tools/theme.json -> series.cartoons[datum] = {file, caption, alt}.
        Tuschlinjerna ritas fram, sedan laveringen, och bildtexten tonas fram under i Newsreader. Saknas filen avbryts körningen.
  {"type":"cta", "title":"Få er", "em":"synlighetsanalys.", "url":"mynth.se"}   alltid sist
Avbryter med RENDERFEL om text inte får plats.
"""
import base64, json, pathlib, shutil, subprocess, sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "reel"))
import render, panorama, sfx  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from PIL import Image  # noqa: E402

VW, VH, FPS = 1080, 1920, 30
REEL = TOOLS / "reel"


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def page_html():
    css = (REEL / "stage.css").read_text(encoding="utf-8").replace("FONTS/", render.FONTS + "/")
    js = (REEL / "stage.js").read_text(encoding="utf-8")
    return (f"<html lang='sv'><head><meta charset='utf-8'><style>{css}{panorama.STYLE}</style></head>"
            f"<body><div id='stage'></div><script>{js}</script></body></html>")


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
    ctx = {
        "kicker": render.series_label(post),
        "seriesTitle": ser.get("title", ""),
        "panelSvg": f'<g class="sun">{panorama.sun_svg(k)}</g><g class="ptxt">{panorama.texts_svg(k)}</g>',
        "sunSvg": f'<g class="sun">{panorama.sun_svg(k)}</g>',
    }

    # Omslag: dagens tredjedel av panoramat.
    pano = Image.open(TOOLS / ser["panorama"]).convert("RGB")
    pano.crop((k * VW, 0, (k + 1) * VW, VH)).save(out_dir / "cover.jpg", "JPEG", quality=95, subsampling=0)

    html = out_dir / "_stage.html"
    html.write_text(page_html(), encoding="utf-8")
    silent = out_dir / "_video.mp4"
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-g", str(FPS), "-keyint_min", str(FPS), "-sc_threshold", "0", "-r", str(FPS), str(silent)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    problems, cues, start = [], [], 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": VW, "height": VH})
        for i, s in enumerate(slides, 1):
            pg.goto(html.as_uri())
            pg.evaluate("document.fonts.ready.then(()=>1)")
            pg.wait_for_timeout(150)
            params = {key: v for key, v in s.items() if key != "type"}
            if s["type"] == "cartoon":
                c = (ser.get("cartoons") or {}).get(post["date"])
                f = TOOLS / c["file"] if c else None
                if not f or not f.exists():
                    sys.exit(f"Teckningen för {post['date']} saknas ({c['file'] if c else 'ingen post i series.cartoons'}).")
                mime = "image/png" if f.suffix.lower() == ".png" else "image/jpeg"
                # som data-URL, så att canvas får läsa pixlarna (file:// räknas som annat ursprung)
                params = {"src": f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode(), "caption": c["caption"]}
                pg.evaluate("""src => new Promise((ok, err) => { const i = new Image(); i.onload = () => { window.IMAGES = {[src]: i}; ok(); };
                               i.onerror = () => err('kunde inte läsa teckningen'); i.src = src; })""", params["src"])
            info = pg.evaluate("([t, p, c]) => { c.images = window.IMAGES || {}; window.S = buildScene(t, p, c); return {d: S.duration, cues: S.cues, o: !!S.overflow}; }",
                               [s["type"], params, dict(ctx, last=i == len(slides))])
            if info["o"]:
                problems.append(f"scen {i} ({s['type']}): texten får inte plats")
            dur = info["d"]
            cues += [[start + c[0]] + c[1:] for c in info["cues"]]
            # kontrollbild: läget strax före slutet, där allt är framme
            pg.evaluate("t => S.render(t)", dur - 320)
            pg.screenshot(path=str(out_dir / f"check-{i:02d}.jpg"), type="jpeg", quality=90)
            for f in range(round(dur / 1000 * FPS)):
                pg.evaluate("t => S.render(t)", f * 1000 / FPS)
                enc.stdin.write(pg.screenshot(type="png"))
            start += round(dur / 1000 * FPS) * 1000 / FPS
        b.close()
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("ffmpeg misslyckades (video)")
    html.unlink()
    if problems:
        silent.unlink()
        sys.exit("RENDERFEL – korta texten:\n" + "\n".join(problems))

    seconds = start / 1000
    wav = out_dir / "_audio.wav"
    sfx.mix(cues, seconds, wav, beat_from=2.7)
    mp4 = out_dir / "reel.mp4"
    r = subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", "-movflags", "+faststart", str(mp4)])
    silent.unlink(); wav.unlink()
    if r.returncode != 0:
        sys.exit("ffmpeg misslyckades (ljud)")
    print(json.dumps({"series": ctx["kicker"], "tile": ["vänster", "mitten", "höger"][k], "seconds": round(seconds, 1),
                      "scenes": [s["type"] for s in slides], "video": str(mp4), "cover": str(out_dir / "cover.jpg")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
