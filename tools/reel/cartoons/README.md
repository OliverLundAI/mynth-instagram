# Skämtteckningar till serien (tre-i-en)

Varje seriedag visar en enrutad skämtteckning: tusch och grå lavering på vitt papper, som en klassisk
tidningsteckning. Videon ritar fram tuschlinjerna, sedan laveringen, och handskriver bildtexten under i versaler (Architects Daughter). Övrig typografi följer Mynths profil: Newsreader för rubriker, Switzer för etiketter, mint (#0BBFA6) som enda accent och logotypens prick.
Bildtexten läggs på av `tools/video.py` (från `tools/theme.json` → `series.cartoons`), så teckningen ska inte ha någon text.

## Teckningarna för 30/10–1/11

Mynth ritar själv i en enkel tuschstil. Källfilerna ligger i `src/` (SVG) och renderas till PNG med
`python3 tools/reel/cartoons/render_svg.py src/<fil>.svg <datum>.png`.

| Datum | Pelare | Teckning | Bildtext |
|---|---|---|---|
| 2026-10-30 | Myt eller verklighet | Butiksägaren putsar skyltfönstret, folk går förbi med blicken i mobilen | ”Vi har aldrig haft ett snyggare skyltfönster.” |
| 2026-10-31 | Testa själv | Spegeln visar en annan person | ”Spegel, spegel på väggen där – vem ska kunderna välja här?” |
| 2026-11-01 | Tanke | Robotar viskar vidare om företaget, företagaren förskräckt | ”Det är i alla fall vad nätet säger om er.” |

## Byta mot riktiga illustrationer

- Lägg filen här med datumet som namn (PNG eller JPG; ändra då `file` i theme.json).
- Kvadratisk eller liggande, minst 1500 px bred, vit bakgrund, svart tusch och grå lavering.
- Ingen text, ingen signatur, inga logotyper, inga riktiga personer eller varumärken.
- Egen eller fritt licensierad bild, aldrig en kopia av någon annans teckning.
- Saknas dagens fil när den schemalagda körningen startar (08:52, för publicering runt 09:00) avbryts körningen och loggas, och inget publiceras.
