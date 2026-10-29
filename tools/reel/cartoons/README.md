# Skämtteckningar till serien ”Synas i AI”

Varje seriedag visar en enrutad skämtteckning: tusch och grå lavering på vitt papper, som en klassisk
tidningsteckning. Videon ritar fram tuschlinjerna, sedan laveringen, och skriver bildtexten för hand under.
Bildtexten läggs på av `tools/video.py` (från `tools/theme.json` → `series.cartoons`), så teckningen ska inte ha någon text.

## Leverans

- Lägg filerna här med datumet som namn: `2026-10-30.png`, `2026-10-31.png`, `2026-11-01.png` (PNG eller JPG; ändra då `file` i theme.json).
- Kvadratisk eller nästan kvadratisk, minst 1500 px bred, vit bakgrund.
- Svart tusch, gråskala. Ingen färg, ingen text, ingen signatur, inga logotyper, inga riktiga personer eller varumärken.
- Måste vara egen eller fritt licensierad bild, inte en kopia av någon annans teckning.
- Saknas dagens fil när den schemalagda körningen startar (07:32) avbryts körningen och loggas, och inget publiceras.

## Teckningarna

### Fredag 2026-10-30 · Myt eller verklighet
Bildtext: ”Jag ser en leverantör i er framtid. Tyvärr inte han bakom draperiet.”

Prompt (engelska fungerar bäst i bildverktyg):
> Single-panel editorial gag cartoon, black ink line drawing with soft grey wash on a plain white background, classic magazine cartoon style, loose confident linework.
> A fortune teller in a headscarf sits at a small round table with a glowing crystal ball, speaking to a businesswoman client seated across from her.
> To the side, a hopeful businessman in a suit peeks out from behind a heavy velvet curtain, clearly waiting to be mentioned.
> No text, no letters, no signature, no logos.

### Lördag 2026-10-31 · Testa själv
Bildtext: ”Spegel, spegel på väggen där – vem ska kunderna välja här?”

> Single-panel editorial gag cartoon, black ink line drawing with soft grey wash on a plain white background, classic magazine cartoon style, loose confident linework.
> A businesswoman in a blazer stands in her office in front of an ornate full-length wall mirror.
> In the mirror, instead of her own reflection, a different smug businessman smiles and waves back at her. She looks startled.
> No text, no letters, no signature, no logos.

### Söndag 2026-11-01 · Tanke
Bildtext: ”Om just er har jag bara den här broschyren.”

> Single-panel editorial gag cartoon, black ink line drawing with soft grey wash on a plain white background, classic magazine cartoon style, loose confident linework.
> A friendly round robot librarian stands behind a library counter, apologetically holding up a single thin, flimsy pamphlet to a businessman.
> Behind the robot, tall bookshelves are packed with thick, heavy volumes.
> No text, no letters, no signature, no logos.
