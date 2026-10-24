#!/usr/bin/env bash
# Hämtar typsnitt (laddas ner vid körning – distribueras inte i repot) och beroenden.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts .cache
if [ ! -f fonts/newsreader-normal.woff2 ]; then
  (cd .cache && npm i --silent @fontsource-variable/newsreader >/dev/null 2>&1)
  cp .cache/node_modules/@fontsource-variable/newsreader/files/newsreader-latin-opsz-normal.woff2 fonts/newsreader-normal.woff2
  cp .cache/node_modules/@fontsource-variable/newsreader/files/newsreader-latin-opsz-italic.woff2 fonts/newsreader-italic.woff2
fi
if [ ! -f fonts/switzer-600.woff2 ]; then
  curl -sS "https://api.fontshare.com/v2/css?f[]=switzer@400,500,600&display=swap" -o .cache/switzer.css
  python3 - <<'PY'
import re, subprocess
css = open('.cache/switzer.css').read()
for b in css.split('@font-face')[1:]:
    if "font-family: 'Switzer'" not in b or 'italic' in b: continue
    w = re.search(r'font-weight:\s*(\d+)', b).group(1)
    u = re.search(r"url\('(//[^']+\.woff2)'\)", b).group(1)
    subprocess.run(['curl', '-sS', '-o', f'fonts/switzer-{w}.woff2', 'https:' + u], check=True)
PY
fi
python3 -c "import playwright, PIL" 2>/dev/null || pip install --break-system-packages -q playwright pillow
ls fonts
