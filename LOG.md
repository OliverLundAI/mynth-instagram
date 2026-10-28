# Publiceringslogg

En rad per inlägg, nyaste överst. Fylls i automatiskt efter publicering.

| Datum | Pelare | Krok | Bilder | Länk |
|---|---|---|---|---|
| 2026-10-28 | Vad vi mäter | Ett enskilt AI-svar säger lite om hur ni syns. | 4 | https://www.instagram.com/p/DfB2zC3FhR4/ |
| 2026-10-27 | Så fungerar AI-svar | Så blir en fråga till ett AI-svar. | 4 | https://www.instagram.com/p/De_OghvFmvG/ |
| 2026-10-26 | Risken | Ni märker inte när AI väljer bort er. | 4 | https://www.instagram.com/p/De8s6IQnMyp/ |
| 2026-10-25 | Tanke | AI beskriver er utifrån det som finns om er. | 3 | https://www.instagram.com/p/De6KT55lReK/ |
| 2026-10-25 | Vad Mynth gör | Kunderna frågar AI. Nämns ni? | 4 | https://www.instagram.com/p/De6E3LinDrE/ |

## Avbrutna körningar

| Datum | Steg | Orsak |
|---|---|---|
| 2026-10-28 | 4. Publicera (`publish.py publish`, `media_publish`) | Instagram API svarade `Media ID is not available` / "The media is not ready for publishing" (kod 9007, subkod 2207027) trots att alla containrar rapporterat `FINISHED`. Kontrollerat efteråt: inget nytt inlägg på kontot, kvot 0/100. Inlägget (pelare Vad vi mäter, krok ”Ett enskilt AI-svar säger lite om hur ni syns.”) är renderat, kvalitetskontrollerat och pushat i `posts/2026-10-28/`, redo att publiceras manuellt. Löst samma dag: `publish.py` försöker nu igen vid just detta fel, och inlägget publicerades i en manuell körning. |
| 2026-10-26 | 0. Förberedelser (`publish.py limit`) | Instagram API svarade `API access blocked.` (OAuthException, kod 200) på `GET me`, även vid nytt försök och utan versionsprefix. Inget skrevs, renderades eller publicerades. Orsak: Meta-appen var borttagen. Löst samma dag när appen återställdes, och inlägget publicerades i en manuell körning. |
