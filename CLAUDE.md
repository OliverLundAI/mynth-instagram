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
- Skriv `posts/$DATE/post.json` med fälten `date`, `pillar`, `hook`, `caption`, `alt` (en per bild) och `slides`.
  Bildtyperna beskrivs i `tools/render.py`.

## 2. Rendera och kontrollera
- `python3 tools/render.py posts/$DATE/post.json` ger `01.jpg`, `02.jpg` osv.
- Temat väljs automatiskt: datum i `tools/theme.json` → `dark`, annars `light`. Datum i `small_dots_dates` ger små prickar även på cover och cta. Kontrollera att render.py rapporterar rätt tema och prickstorlek. Lägg inte till `theme` i post.json.
- Vid RENDERFEL: korta texten och rendera om (högst 3 försök).
- Titta på varje bild med Read-verktyget och kontrollera att ingen text är avklippt, överlappar eller är felstavad.
- Gå igenom kvalitetskontrollen i RULES.md avsnitt 5. Alla punkter måste vara ja.

## 3. Lägg upp bilderna publikt
- `git add posts/$DATE && git commit -m "Inlägg $DATE" && git push`
- `SHA=$(git rev-parse HEAD)`. Bildadresserna blir
  `https://raw.githubusercontent.com/OliverLundAI/mynth-instagram/$SHA/posts/$DATE/01.jpg` osv.
- Kontrollera med `curl -sI` att varje adress svarar 200 och har `content-type: image/jpeg`.

## 4. Publicera
- `python3 tools/publish.py publish posts/$DATE/post.json <url1> <url2> ...`
- Spara utdata (media_id, permalink) som `posts/$DATE/published.json`.
- Lägg in en rad överst i tabellen i LOG.md: `| $DATE | pelare | krok | antal bilder | permalink |`.
- `git add -A && git commit -m "Publicerat $DATE" && git push`

## 5. Förnyelse av token (bara på söndagar)
- `python3 tools/publish.py refresh` ger `access_token` och `expires_in`.
- Om den nya token skiljer sig från `IG_TOKEN`: uppdatera den schemalagda uppgiftens instruktion med den nya token
  (update_trigger), och ändra ingenting annat i instruktionen.

## 6. Rapport
Avsluta med en rad: datum, pelare, krok och permalink, eller vad som gick fel.
