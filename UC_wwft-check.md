# UC_wwft-check — Wwft Cliëntenonderzoek Tool

| | |
|---|---|
| **Eigenaar** | Sylvain Bouwman |
| **Domein** | Compliance / Wwft |
| **Status** | Live (demo) |
| **Versie** | v1 — juni 2026 |

## Doel

Interactief en gestructureerd cliëntenonderzoek uitvoeren conform de Wet ter voorkoming van witwassen en financieren van terrorisme (Wwft), inclusief KvK-verificatie, OpenSanctions-screening en PDF-rapportage.

## Betrokkenen

| Rol | Toelichting |
|---|---|
| Eigenaar | Sylvain Bouwman |
| Gebruikers | Medewerkers Join Administraties en DK Accountants die Wwft-onderzoek uitvoeren |
| Initiatief | Gebouwd als demo-bijdrage aan de interne werkgroep (Bram) |

## Trigger

Aanvang van een nieuwe klantrelatie of periodieke hertoetsing van bestaande cliënten conform Wwft-verplichting.

## As-is situatie

Wwft-onderzoek wordt handmatig uitgevoerd: afzonderlijke checks op KvK, sanctielijsten en UBO-register. Bevindingen worden losjes vastgelegd. Geen gestandaardiseerde werkwijze of automatische rapportage.

## To-be situatie

1. Medewerker opent de tool en voert klantnaam of KvK-nummer in
2. Automatische KvK-verificatie haalt bedrijfsgegevens op
3. OpenSanctions-screening controleert op sanctielijsten (EU, VN, OFAC)
4. Gestructureerde vragenlijst leidt medewerker door het cliëntenonderzoek
5. Tool beoordeelt risicocategorie (laag / midden / hoog)
6. PDF-rapport wordt gegenereerd als vastlegging in het dossier

## Live

[wwft-check.streamlit.app](https://wwft-check.streamlit.app)

## Waarde

| | |
|---|---|
| **Kwaliteit** | Gestandaardiseerde werkwijze; geen vergeten stappen in het onderzoek |
| **Compliance** | Aantoonbare vastlegging van het cliëntenonderzoek conform Wwft |
| **Tijdwinst** | Automatische KvK- en sanctiescreening in plaats van handmatig zoeken |
