# Volgende stappen — WWFT-check tool

*Bijgewerkt: 2026-07-07 na v0.9 sprint*

---

## Direct te doen (geen code nodig)

### 1. ANTHROPIC_API_KEY instellen in Streamlit Secrets
De AI Vraag & Antwoord-functie in de handleiding is gebouwd maar inactief zonder API-sleutel.

**Stappen:**
1. Ga naar [streamlit.io/cloud](https://share.streamlit.io) → jouw app → Settings → Secrets
2. Voeg toe:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
3. Save → app herstart automatisch

### 2. Mail aan Yvonne versturen
Concept staat in `mail_yvonne_concept.md` (repo root). Inhoud:
- Overzicht v0.4–v0.9 wijzigingen
- Uitleg MIDDEN-vloer voor MKB (art. 6 Wwft discussie)
- Uitleg over de drie PDF's (DK-cyclus ✅, RB-handboek ✅, AFM-leidraad ⚠️ niet relevant voor BFT-toezicht)

---

## Volgende bouwsprint

### A. Handleiding AI Q&A verbeteren (optioneel)
Huidige RAG is keyword-based (eenvoudig maar werkt). Verbeterpunten als het antwoorden te vaag blijken:
- Chunk-grootte aanpassen in `wwft_rb_chunks.json` (nu ~6 pagina's per chunk, kleiner = preciezer)
- Top-k van 4 naar 6 chunks verhogen
- Zoeklogica verbeteren: stemming / synoniemen (bijv. "PEP" → "politiek prominente persoon")

### B. Hertoetsing / Fase 4 — hoogste prioriteit uit gap-analyse
Yvonne's UC-document noemt periodieke hertoetsing expliciet. Nu nog niet gebouwd.
- **Wat**: "Datum volgende review" berekenen en vastleggen in rapport
- **Logica**: gebaseerd op risicoclassificatie (al aanwezig: 6 mnd / 1 jr / 3 jr)
- **UI**: stap 9 of apart veld "Hertoetsing gepland op: [datum]"
- **Later**: signalering/notificatie bij verlopen datum (vereist persistente opslag)

### C. Auditlog voor BFT-controles
- Momenteel: elke sessie is los, geen centrale logging
- **Minimaal**: download-knop voor JSON-export van het onderzoek (naast Word-rapport)
- **Volledig**: centrale opslag per cliënt (vereist database)

### D. Rolgebaseerde toegang
- Medewerker: kan onderzoek uitvoeren
- Compliance officer (Yvonne): kan alle dossiers inzien, rapporten beoordelen
- Vereist: authenticatie (Streamlit heeft `st.experimental_user` voor SSO)

---

## Openstaande vragen voor Yvonne

1. **Melder ID**: Heeft DK Accountants al een Melder ID bij FIU-Nederland? Zijn er aparte ID's voor accountants en belastingadviseurs?
2. **AFAS-import**: Werkt het Word-rapport (.docx) goed in AFAS, of is er een specifiek exportformaat nodig?
3. **Scope hertoetsing**: Wil ze de tool ook inzetten voor Fase 4 (periodieke hertoetsing), of nu eerst Fase 1 volledig afronden?
4. **Pilotgroep**: Wie gaan de tool als eerste gebruiken? Heeft ze feedback van de werkvloer nodig voor een volgende sprint?

---

## Technische context voor volgende sessie

### Bestanden
| Bestand | Inhoud |
|---------|--------|
| `demo/app.py` | Hoofdbestand, ~1950 regels |
| `demo/wwft_rb_chunks.json` | 40 chunks RB Handboek Wwft (442KB) |
| `demo/de_wwft_cyclus_dk.pdf` | DK Accountants Wwft-cyclus overzicht |
| `demo/requirements.txt` | Inclusief `anthropic>=0.104.0` |
| `mail_yvonne_concept.md` | Concept-mail klaar voor verzending |

### API-sleutels in gebruik
- `KVK_API_KEY` — Handelsregister
- `OPENSANCTIONS_API_KEY` — sanctie/PEP-screening
- `ANTHROPIC_API_KEY` — AI Q&A (nieuw in v0.9, nog niet in Secrets gezet)

### Architectuurkeuzes
- **RAG is keyword-based** (geen vectordatabase nodig) — past binnen Streamlit Cloud gratis tier
- **Word-output** voor AFAS-compatibiliteit (UC zei "PDF" maar dat is verspreking, Word is correct)
- **MIDDEN als risicovloer** voor MKB — LAAG alleen bij expliciete art. 6-checkbox
- **pdfplumber** voor PDF's lezen op Windows (pdftoppm werkt niet, Read-tool ook niet voor PDF op Windows)

### Toezichthouder
DK Accountants & Join Administraties vallen onder **BFT** (Bureau Financieel Toezicht), NIET de AFM.
De AFM Leidraad Wwft 2024 is daarom niet leidend.

---

## Versiegeschiedenis

| Versie | Wat |
|--------|-----|
| v0.1–v0.3 | Basisflow: KvK, rechtsvorm-routes, OpenSanctions screening |
| v0.4 | PEP-check stap 5b, hertoetsingstermijn op risico |
| v0.5 | Tipping off verbod (art. 23), bewaarplicht 7 jaar |
| v0.6 | FIU-meldingsbeoordeling (stap 8) |
| v0.7 | Opdrachtbevestiging template (NV COS 4410) |
| v0.8 | Buitenlandse rechtsvorm als risicofactor; MIDDEN-vloer art. 6 Wwft |
| v0.9 | Handleiding: AI Q&A (RB handboek RAG) + Bronnen-tab + DK PDF download |
