# mynth-instagram

Autopilot för @mynth.se på Instagram. En schemalagd Claude-körning gör varje dag följande:

1. Väljer dagens pelare (`PILLARS.md`) och läser `LOG.md` för att undvika upprepning.
2. Skriver bildtext och karusell enligt `RULES.md` (bara verifierade fakta, ingen statistik och inga kund- eller prospektdata).
3. Renderar bilderna med `tools/render.py` i Mynths designsystem.
4. Pushar bilderna hit, eftersom repot är publikt och Instagram hämtar bilderna härifrån.
5. Publicerar med `tools/publish.py` och loggar inlägget i `LOG.md`.

Ändra `RULES.md` eller `PILLARS.md` för att styra innehållet. Ändringarna gäller från nästa körning.
