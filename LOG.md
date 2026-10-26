# Publiceringslogg

En rad per inlägg, nyaste överst. Fylls i automatiskt efter publicering.

| Datum | Pelare | Krok | Bilder | Länk |
|---|---|---|---|---|
| 2026-10-25 | Tanke | AI beskriver er utifrån det som finns om er. | 3 | https://www.instagram.com/p/De6KT55lReK/ |
| 2026-10-25 | Vad Mynth gör | Kunderna frågar AI. Nämns ni? | 4 | https://www.instagram.com/p/De6E3LinDrE/ |

## Avbrutna körningar

| Datum | Steg | Orsak |
|---|---|---|
| 2026-10-26 | 0. Förberedelser (`publish.py limit`) | Instagram API svarade `API access blocked.` (OAuthException, kod 200) på `GET me`, även vid nytt försök och utan versionsprefix. Inget skrevs, renderades eller publicerades. Kontrollera appens/kontots status i Meta for Developers och token. |
