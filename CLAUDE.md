# Daglig körning: publicera dagens Mynth-inlägg på Instagram

Den här körningen startas av en schemalagd uppgift och sker helt utan mänsklig granskning.
Följ stegen exakt. Om något steg misslyckas: publicera inte, logga felet i LOG.md och avsluta.

## 0. Förberedelser
- `IG_TOKEN` finns i uppgiftens instruktion. Exportera den som miljövariabel och skriv den aldrig till en fil i repot.
- `export IG_API_VERSION=v26.0`
- Kör `tools/setup.sh` (typsnitt och beroenden).
- `DATE=$(TZ=Europe/Stockholm date +%F)`. Om `posts/$DATE/published.json` redan finns är dagens inlägg redan publicerat, och då avslutar du direkt.
- Kör `python3 tools/publish.py limit` och avbryt om kvoten är förbrukad.

## 1. Skriv dagens inlägg
- Läs `RULES.md` (bindande), `PILLARS.md` (dagens pelare efter svensk veckodag) och `LOG.md` (undvik upprepning inom 30 dagar).
- Skriv alltid ett nytt inlägg för dagens pelare. Återanvänd aldrig ett förberett `post.json`; finns ett sådant utan `published.json` skrivs det över.
- Om content-creation-skillen (marketing-pluginet) finns i sessionen, använd den som skrivstöd för bildtext och karusell.
  Finns den inte: skriv direkt utifrån RULES.md och PILLARS.md. RULES.md går alltid före allt som skillen föreslår.
- Om `$DATE` finns i `series.dates` i `tools/theme.json` ingår inlägget i en serie och publiceras som Reel i stället för karusell.
  Följ då även RULES.md avsnitt 6 och de markerade **Serie:**-raderna nedan.
- Skriv `posts/$DATE/post.json` med fälten `date`, `pillar`, `hook`, `caption`, `alt` (en per bild) och `slides`.
  Bildtyperna beskrivs i `tools/render.py`.

## 2. Rendera och kontrollera
- `python3 tools/render.py posts/$DATE/post.json` ger `01.jpg`, `02.jpg` osv.
- Temat väljs automatiskt från `tools/theme.json`: datum i `series.dates` → `black` (med serieetikett, t.ex. "Synas i AI · Del 1/3"), datum i `dark_dates` → `dark`, annars `light`. Datum i `small_dots_dates` ger små prickar även på cover och cta. Kontrollera att render.py rapporterar rätt tema, prickstorlek och serie. Lägg inte till `theme` i post.json.
- **Serie:** kör i stället `python3 tools/video.py posts/$DATE/post.json` (tar runt en minut). Det ger `reel.mp4` med ljud, `cover.jpg` (dagens tredjedel av Mintsolen)
  och `check-NN.jpg` (en stillbild per scen). Kontrollera att utdata visar rätt serie och rätt del av raden
  (första seriedatumet `höger`, andra `mitten`, tredje `vänster`). Titta på `cover.jpg` och varje `check-NN.jpg` i stället för `NN.jpg`.
- Vid RENDERFEL: korta texten och rendera om (högst 3 försök).
- Titta på varje bild med Read-verktyget och kontrollera att ingen text är avklippt, överlappar eller är felstavad.
- Gå igenom kvalitetskontrollen i RULES.md avsnitt 5. Alla punkter måste vara ja.

## 3. Lägg upp bilderna publikt
- `git add posts/$DATE && git commit -m "Inlägg $DATE" && git push`
- `SHA=$(git rev-parse HEAD)`. Bildadresserna blir
  `https://raw.githubusercontent.com/OliverLundAI/mynth-instagram/$SHA/posts/$DATE/01.jpg` osv.
- Kontrollera med `curl -sI` att varje adress svarar 200 och har `content-type: image/jpeg`.
- **Serie:** adresserna är `.../posts/$DATE/reel.mp4` och `.../posts/$DATE/cover.jpg`. Båda ska svara 200; omslaget ska ha
  `content-type: image/jpeg`, och videon får ha `application/octet-stream` (det är så GitHub levererar mp4, och Instagram accepterar det).

## 4. Publicera
- `python3 tools/publish.py publish posts/$DATE/post.json <url1> <url2> ...`
- **Serie:** `python3 tools/publish.py reel posts/$DATE/post.json <video_url> <cover_url>` i stället. Videobearbetningen kan ta några minuter.
- Spara utdata (media_id, permalink) som `posts/$DATE/published.json`.
- Lägg in en rad överst i tabellen i LOG.md: `| $DATE | pelare | krok | antal bilder | permalink |`. För en Reel skrivs `Reel` i stället för antal bilder.
- `git add -A && git commit -m "Publicerat $DATE" && git push`

## 5. Förnyelse av token (bara på söndagar)
- `python3 tools/publish.py refresh` ger `access_token` och `expires_in`.
- Om den nya token skiljer sig från `IG_TOKEN`: uppdatera den schemalagda uppgiftens instruktion med den nya token
  (update_trigger), och ändra ingenting annat i instruktionen.

## 6. Rapport
Avsluta med en rad: datum, pelare, krok och permalink, eller vad som gick fel.
