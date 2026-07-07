# WWFT Check Tool

**Live demo: [https://wwft-check.streamlit.app](https://wwft-check.streamlit.app)**

Een interactieve compliance-tool voor het uitvoeren van cliëntenonderzoek conform de Wet ter voorkoming van witwassen en financieren van terrorisme (WWFT). Gebouwd als demo voor interne presentatie aan de kopgroep.

---

## Wat doet de tool?

### Cliëntenonderzoek (8 stappen)

| Stap | Functie |
|------|---------|
| 1 | **KvK-opzoeking** — bedrijfsgegevens ophalen via de KvK Handelsregister API (naam, rechtsvorm, SBI-codes, adres, oprichtingsdatum) |
| 2 | **Bedrijfsgegevens** — weergave met risico-indicatie per SBI-sector |
| 3 | **Doel en aard zakelijke relatie** — conform art. 3 lid 2 sub b WWFT |
| 4 | **Personen en UBO-onderzoek** — 6 routes op basis van rechtsvorm (eenmanszaak, VOF/maatschap, CV, BV/NV, stichting, vereniging) met volledige art. 33-identificatievelden |
| 5 | **Sanctie- en PEP-screening** — automatisch via OpenSanctions (~40 bronnen: OFAC, EU, VN, PEP-registers) |
| 5b | **Handmatige PEP-check** — vastlegging inclusief bron van vermogen en bron van middelen (verplicht bij PEP, art. 8 lid 4 Wwft) |
| 6 | **Adverse media search** — DuckDuckGo op fraude, witwassen, faillissement e.d. |
| 7 | **Integriteitsvragen** — conform NBA Nadere Voorschriften WWFT (vragen 4 t/m 11) |
| 8 | **Risicobeoordeling** — automatische scoring met risicogebaseerde hertoetsingstermijn (6 mnd / 1 jr / 3 jr) |
| 9 | **FIU-meldingsbeoordeling** — vastlegging of er aanleiding is voor melding bij FIU-Nederland (art. 16 Wwft), inclusief checklist en tipping off verbod |
| 10 | **Rapport downloaden** — Word-rapport met alle stappen, bewaarplicht-vermelding en FIU-sectie |

### Handleiding (apart tabblad)
- **Interactief stappenplan** — klikbare tijdlijn met uitklapbare antwoorden per stap
- **Volledige handleiding** — naslagwerk voor medewerkers (8 hoofdstukken, bronnen, praktijkvoorbeeld)
- **Compliance officer** — altijd zichtbaar in de sidebar als aanspreekpunt voor vragen en twijfelgevallen

---

## Rechtsvorm-routes (Stap 4)

De tool detecteert automatisch de rechtsvorm via KvK en toont het juiste formulier:

| Rechtsvorm | Vertegenwoordiger | UBO-logica |
|---|---|---|
| Eenmanszaak | Ondernemer = cliënt én UBO | Geen aparte UBO-vaststelling |
| VOF / Maatschap | Optredende vennoot/maat | >25% winst of zeggenschap; anders pseudo-UBO |
| CV | Beherend vennoot | Beherend én stille vennoten op >25% kapitaal/winst |
| BV / NV | Bestuurder(s) | >25% eigendom of zeggenschap; bestuurder ≠ automatisch UBO |
| Stichting | Bestuurder(s) | >25% zeggenschap of begunstiging |
| Vereniging | Bestuurder(s) | >25% stemrecht |

---

## Vereiste API-sleutels

| API | Gebruik | Kosten |
|-----|---------|--------|
| [KvK Handelsregister](https://developers.kvk.nl) | Bedrijfsgegevens opzoeken | Gratis (registratie vereist) |
| [OpenSanctions](https://www.opensanctions.org/api/) | Sanctie- en PEP-screening | Gratis t/m 100 req/dag |

Zonder API-sleutels start de tool automatisch in **demo modus** met voorbeelddata.

---

## Installatie

```bash
# 1. Repository klonen
git clone https://github.com/Sylvainbouwman/wwft-check.git
cd wwft-check

# 2. Afhankelijkheden installeren
pip install -r demo/requirements.txt

# 3. API-sleutels instellen (.env in de demo/ map)
KVK_API_KEY=jouw-sleutel
OPENSANCTIONS_API_KEY=jouw-sleutel

# 4. App starten
cd demo
python -m streamlit run app.py
```

De app is bereikbaar op [http://localhost:8501](http://localhost:8501).

---

## Projectstructuur

```
wwft-check/
├── demo/
│   ├── app.py                          # Streamlit-applicatie (hoofdbestand)
│   ├── requirements.txt                # Python-afhankelijkheden
│   ├── wwft-handleiding-medewerkers_v1.md   # Handleiding voor medewerkers
│   └── wwft_stappenplan_visueel.html   # Interactief HTML-stappenplan
└── README.md
```

---

## Roadmap

### Fase 1 — Verbreding van het onderzoek
- ✅ Handmatige PEP-check vastleggen
- ✅ PEP verscherpt onderzoek: bron van vermogen + bron van middelen vastleggen (art. 8 lid 4 Wwft)
- ✅ Tipping off verbod (art. 23 Wwft): waarschuwing in UI en rapport bij hoog-risico uitkomst
- ✅ Bewaarplicht 7 jaar: vermeld in rapport en stap 8 (art. 33 Wwft)
- ✅ Hertoetsingstermijn op basis van risicoclassificatie: 6 mnd (hoog) / 1 jaar (midden) / 3 jaar (laag)
- ✅ FIU-meldingsbeoordeling (stap 9): vastlegging aanleiding, type, omschrijving, intern beraad en Melder ID; checklist in UI en rapport; tipping off verbod prominently vermeld
- ✅ Vloer MIDDEN voor MKB-cliënten: LAAG alleen bij expliciete art. 6 Wwft-kwalificatie (beursgenoteerd / overheid / financiële instelling)
- Buitenlandse rechtsvorm als expliciete risicofactor in de beoordeling

### Fase 2 — Integratie met bestaande systemen
- Koppeling met DMS/dossiersysteem (bijv. AFAS, Exact)
- Exportformaat aanpasbaar per kantoor (huisstijl rapport)
- Rolgebaseerde toegang: medewerker vs. compliance officer

### Fase 3 — Beheer & toezicht
- FIU-melding workflow: medewerker begeleiden bij meldprocedure (incl. Melder ID, geheimhouding)
- Opdrachtbevestiging template met Wwft-clausules (NV COS 4410)
- Auditlog voor BFT-controles
- Dashboardoverzicht openstaande en afgeronde dossiers
- Notificaties bij verlopen hertoetsingstermijn

---

## Status

**v0.6 — demo** · live via [Streamlit Community Cloud](https://wwft-check.streamlit.app) · gebouwd voor interne presentatie aan de kopgroep · niet geschikt voor productiegebruik zonder aanvullende beveiligings- en infrastructuurmaatregelen.
