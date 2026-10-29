# Mynth på Instagram – regler för autopiloten

Inläggen publiceras utan mänsklig granskning. Därför gäller reglerna nedan utan undantag.
Om ett utkast bryter mot en regel: skriv om det. Om det inte går: hoppa över dagen och logga varför.

## 1. Verifierade fakta (det enda som får påstås om Mynth)

- Mynth (Mynth AB) är en svensk, specialiserad GEO-byrå för företag som vill synas i AI. GEO = Generative Engine Optimization.
- Mynth mäter dagligen hur ett varumärke nämns och citeras i AI-motorer: ChatGPT, Gemini, Perplexity, Copilot och Google AI Overviews. När motorer räknas upp ska alla fem vara med.
- Mynth arbetar i tre spår:
  1. Mätning – daglig bevakning av hur kunden syns i AI-svar.
  2. Innehåll – artiklar och beslutssidor som fyller luckor där AI saknar svar om kunden.
  3. Tredjepartsnärvaro – databaser, redaktionella kontakter och återförsäljarkanaler, alltså platser där AI hämtar information.
- Två av de tre spåren fungerar oberoende av kundens egen webbplats.
- Mynth erbjuder en synlighetsanalys som första steg. Erbjudandet är skräddarsytt efter kundens mål.
- Webbplats: mynth.se. Kontakt: kontakt@mynth.se.
- Bannerns budskap: ”Rekommenderar AI er eller konkurrenten?” och ”En specialiserad GEO-byrå för företag som vill synas i AI.”

Allmän, okontroversiell förklaring av hur AI-assistenter fungerar är tillåten, t.ex. att de sammanfattar ett svar och nämner ett fåtal alternativ,
eller att de bygger svaren på information som finns om ett företag på nätet. Allt sådant ska vara utan siffror och utan påståenden om enskilda AI-bolags interna system.

## 2. Förbjudet (bryts aldrig)

- Statistik, siffror, procent, marknadsstorlekar och användartal – inga, inte ens med källa.
- Kundcase, kundnamn, ”våra kunder”, resultat, referenser och testimonials. Mynth har inga publicerade case.
- Namn på prospekt, företag, personer eller konkurrenter, och analysresultat för något företag.
- Priser, paket, rabatter och ”gratis”.
- Löften om resultat, som ”garanterat”, ”hamna överst”, ”ranka #1” eller ”fler kunder”.
- Underleverantörer och plattformar bakom tjänsten. Nämn aldrig verktyg vid namn.
- Varumärket Cito eller citogeo.se. Använd aldrig adressen hej@mynth.se.
- Påhittade citat från riktiga personer. Citatbilder får bara innehålla Mynths egna påståenden med ”Mynth” som avsändare.
- Vinkeln ”ett svar istället för tio blå länkar” (redan använd).

## 3. Ton och form

- Svenska, ”ni”-tilltal till företag. Sakligt, lugnt och självsäkert, utan hype och utan utropstecken.
- Formulera med ”risken”, inte ”chansen”. Risken är att inte nämnas, inte att AI talar illa.
- Bildtext: krok på första raden (under 125 tecken), korta stycken med luft, max 1 200 tecken.
  Avsluta med ”Länk i bio.” eller en mjuk fråga, och sedan 3–5 hashtags, alltid #GEO och #AIsynlighet.
- Inga emojis. Pilen → är okej i listor.
- Karusell med 3–6 bilder. Bild 1 är alltid `cover` (i serier `panel`, se avsnitt 6) och sista bilden är alltid `cta` (”Få er synlighetsanalys.” eller en liknande variant + mynth.se).
- Bildtexter på slides ska vara korta. Rubriken är högst cirka 6 ord och underraden en mening.
- Alt-text för varje bild (vad som står på den).

## 4. Variation

- Läs `LOG.md` före varje inlägg. Ingen krok, rubrik eller vinkel får upprepas inom 30 dagar.
- Följ veckodagens pelare i `PILLARS.md`, men hitta en ny vinkel inom pelaren varje gång.

## 5. Kvalitetskontroll före publicering (alla punkter måste vara ja)

1. Varje påstående om Mynth finns i avsnitt 1.
2. Inget i avsnitt 2 förekommer, varken i bildtexten eller på bilderna.
3. Ingen siffra förekommer, utom bildnumrering, serienumrering i formen ”Del 1/3” (se avsnitt 6) och de fem motorerna som namn.
4. render.py gick igenom utan RENDERFEL.
5. Inga stavfel. Läs igenom på svenska en gång till.

## 6. Serier (tre-i-en)

- En serie är tre inlägg i följd vars första bilder tillsammans bildar en sammanhängande panoramabild över en hel rad i profilrutnätet (WHOOP-inspirerat delat rutnät). Serien definieras i `tools/theme.json` under `series` (titel, datum, panoramabild).
- I en serie är bild 1 alltid `{"type": "panel"}` i stället för `cover`. render.py lägger in rätt tredjedel av panoramabilden. Skriv ingen egen text på den.
- Därefter följer bilderna dagens pelare som vanligt (t.ex. `text` → `text` → `cta`, `text(steps)` → `cta` eller `quote` → `text` → `cta`). Sista bilden är alltid `cta`, och karusellen har 3–6 bilder inklusive panelen.
- Eftersom panelen saknar rubrik bär bildtextens första rad hela kroken. Den ska kunna stå ensam.
- Alt-text för panelen: ”Del av en panoramabild: mintgröna prickar i en våg mot en färgtoning i mint och blått uppifrån som övergår i svart.” följt av texten som syns på just den delen: första datumet ”Text: mynth.se”, andra ”Text: Rekommenderar AI er eller konkurrenten?”, tredje ”Text: Synas i AI”.
- Varje inlägg följer sin veckodags pelare och alla regler ovan, och ska fungera fristående. Hänvisa inte till andra delar och lova inte när nästa del kommer.
- Serieetiketten (t.ex. ”Synas i AI · Del 1/3”) läggs på de övriga bilderna automatiskt av render.py. Skriv den inte i slides. Rubriker sätts i versaler av temat, så håll dem korta.
- Bildtexten avslutas, före hashtaggarna, med raden ”Del 1/3 i serien Synas i AI.” (rätt delnummer).
- Publicera exakt ett inlägg per seriedag. Ett extra eller saknat inlägg förskjuter panoramabilden i rutnätet.
