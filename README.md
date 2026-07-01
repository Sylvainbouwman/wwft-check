# WWFT Check Tool

**Live demo: [https://wwft-check.streamlit.app](https://wwft-check.streamlit.app)**

Een interactieve compliance-tool voor het uitvoeren van cliëntonderzoek conform de Wet ter voorkoming van witwassen en financieren van terrorisme (WWFT).

## Wat doet de tool?

- **KvK-opzoeking** — bedrijfsgegevens ophalen via de KvK Handelsregister API (naam, rechtsvorm, SBI-codes, oprichtingsdatum, adres, medewerkers)
- **Sanctie-screening** — automatische toetsing tegen de OpenSanctions-database (OFAC, EU, VN en meer)
- **Adverse media search** — DuckDuckGo-zoekopdracht op negatieve berichtgeving over de cliënt
- **Risicoclassificatie** — geautomatiseerde scoring op basis van rechtsvorm, SBI-sector, land van vestiging en sanctieresultaten
- **CDD-formulier** — standaard (art. 3) of verscherpt (art. 8) cliëntonderzoek op basis van de risicoklasse
- **PDF-rapport** — volledig downloadbaar rapport met alle bevindingen, inclusief klikbare bronlinks

## Vereiste API-sleutels

| API | Gebruik | Kosten |
|-----|---------|--------|
| [KvK Handelsregister](https://developers.kvk.nl) | Bedrijfsgegevens opzoeken | Gratis (registratie vereist) |
| [OpenSanctions](https://www.opensanctions.org/api/) | Sanctie- en PEP-screening | Gratis t/m 100 req/dag |

## Installatie

```bash
# 1. Repository klonen
git clone https://github.com/Sylvainbouwman/wwft-check.git
cd wwft-check

# 2. Afhankelijkheden installeren
pip install -r demo/requirements.txt

# 3. API-sleutels instellen
copy demo\.env.example demo\.env
# Vul KVK_API_KEY en OPENSANCTIONS_API_KEY in via Kladblok

# 4. App starten
cd demo
python -m streamlit run app.py
```

De app is daarna bereikbaar op [http://localhost:8501](http://localhost:8501).

## Projectstructuur

```
wwft-check/
├── demo/
│   ├── app.py              # Streamlit-applicatie
│   ├── requirements.txt    # Python-afhankelijkheden
│   └── .env.example        # Voorbeeldconfiguratie (geen echte sleutels)
└── functioneel_ontwerp.html  # Functioneel ontwerp (UC01–UC07)
```

## Toekomstige uitbreidingen

- UBO-register koppeling (KvK)
- PEP-screening (Politically Exposed Persons)
- Integratie met dossiersysteem / DMS
- Rolgebaseerde toegang per medewerker
- Auditlog voor toezichthouders

## Status

Demo-versie — live via [Streamlit Community Cloud](https://wwft-check.streamlit.app), gebouwd voor interne presentatie aan de kopgroep. Niet geschikt voor productiegebruik zonder aanvullende beveiligings- en infrastructuurmaatregelen.
