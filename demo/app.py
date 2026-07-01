import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from fpdf import FPDF
from duckduckgo_search import DDGS

load_dotenv()

KVK_API_KEY = os.getenv("KVK_API_KEY", "")
KVK_BASE_URL = os.getenv("KVK_BASE_URL", "https://api.kvk.nl/api/v2")
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")
DEMO_MODUS = not bool(KVK_API_KEY)

# Sessie met Connection: close voorkomt reset bij v1 endpoints
_kvk_session = requests.Session()
_kvk_session.headers.update({
    "apikey": KVK_API_KEY,
    "Accept": "application/json",
    "Connection": "close",
})

st.set_page_config(
    page_title="WWFT Check Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1rem !important; }
.stAlert { margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Demo data (werkt zonder API key)
# ──────────────────────────────────────────────

DEMO_KVK_DATA = {
    "kvkNummer": "34220805",
    "naam": "Demo Vastgoed Amsterdam BV",
    "type": "hoofdvestiging",
    "adres": {
        "binnenlandsAdres": {
            "straatnaam": "Herengracht",
            "huisnummer": 182,
            "postcode": "1016BR",
            "plaats": "Amsterdam",
        }
    },
}

DEMO_BASISPROFIEL = {
    "kvkNummer": "34220805",
    "naam": "Demo Vastgoed Amsterdam BV",
    "rechtsvorm": "Besloten Vennootschap",
    "datumOprichting": "20100315",
    "sbiCodes": [
        {"sbiCode": "6810", "sbiOmschrijving": "Handel in eigen onroerend goed"},
        {"sbiCode": "6820", "sbiOmschrijving": "Verhuur van en handel in eigen onroerend goed"},
    ],
    "aantalMedewerkers": "5 tot 9",
}


# ──────────────────────────────────────────────
# KvK API
# ──────────────────────────────────────────────

def zoek_kvk(zoekterm: str, op_naam: bool = False) -> dict:
    if DEMO_MODUS:
        return {"success": True, "resultaten": [DEMO_KVK_DATA]}
    try:
        param = "naam" if op_naam else "kvkNummer"
        resp = _kvk_session.get(f"{KVK_BASE_URL}/zoeken", params={param: zoekterm}, timeout=10)
        resp.raise_for_status()
        # Alleen hoofdvestigingen tonen (geen dubbele rechtspersoon-entries)
        resultaten = [r for r in resp.json().get("resultaten", []) if r.get("type") != "rechtspersoon"]
        if resultaten:
            return {"success": True, "resultaten": resultaten}
        return {"success": False, "error": "Geen resultaten gevonden."}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def haal_basisprofiel(kvk_nummer: str, href: str = None) -> dict:
    if DEMO_MODUS:
        return {"success": True, "data": DEMO_BASISPROFIEL}
    url = href or f"https://api.kvk.nl/api/v1/basisprofielen/{kvk_nummer}"
    try:
        resp = _kvk_session.get(url, timeout=10)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────
# OpenSanctions API
# ──────────────────────────────────────────────

def screen_opensanctions(naam: str, schema: str = "Company") -> dict:
    """OpenSanctions match API – vereist een (gratis) API key."""
    if not OPENSANCTIONS_API_KEY:
        return {
            "success": False,
            "geen_key": True,
            "error": (
                "Geen OpenSanctions API key gevonden. Registreer gratis op "
                "https://www.opensanctions.org/api/ en voeg OPENSANCTIONS_API_KEY toe aan je .env"
            ),
        }
    try:
        payload = {
            "queries": {
                "entity": {
                    "schema": schema,
                    "properties": {"name": [naam]},
                }
            }
        }
        resp = requests.post(
            "https://api.opensanctions.org/match/default",
            headers={"Authorization": f"ApiKey {OPENSANCTIONS_API_KEY}"},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        resultaten = data.get("responses", {}).get("entity", {}).get("results", [])
        hits = [r for r in resultaten if r.get("score", 0) >= 0.70]
        hoog = [r for r in resultaten if r.get("score", 0) >= 0.85]
        return {
            "success": True,
            "resultaten": resultaten[:10],
            "hits": len(hits),
            "hoog_risico": len(hoog),
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────
# Risicobeoordeling
# ──────────────────────────────────────────────

HOOG_RISICO_SBI = {"6810", "6820", "6492", "6491", "9200", "9201", "9202", "6612", "6619"}
MIDDEN_RISICO_SBI = {"5610", "5630", "6411", "6419", "6499", "7711", "7712"}

HOOG_RISICO_RECHTSVORM = {"Stichting", "Coöperatie", "Commanditaire Vennootschap"}


def bereken_risico(basisprofiel: dict, screening: dict) -> tuple[str, int, list[str]]:
    score = 0
    factoren = []

    for sbi in get_sbi_codes(basisprofiel):
        code = str(sbi.get("sbiCode", ""))
        omschrijving = sbi.get("sbiOmschrijving", "")
        if code in HOOG_RISICO_SBI:
            score += 3
            factoren.append(f"Hoog-risico sector: {omschrijving} (SBI {code})")
        elif code in MIDDEN_RISICO_SBI:
            score += 1
            factoren.append(f"Aandachtssector: {omschrijving} (SBI {code})")

    rechtsvorm = basisprofiel.get("rechtsvorm", "")
    if any(rv in rechtsvorm for rv in HOOG_RISICO_RECHTSVORM):
        score += 1
        factoren.append(f"Verhoogde aandacht rechtsvorm: {rechtsvorm}")

    if screening.get("success"):
        hoog = screening.get("hoog_risico", 0)
        hits = screening.get("hits", 0)
        if hoog > 0:
            score += 10
            factoren.append(f"SANCTIELIJST: {hoog} hoge-score treffer(s) gevonden!")
        elif hits > 0:
            score += 5
            factoren.append(f"Sanctielijst: {hits} mogelijke treffer(s) – nader onderzoek vereist")

    if score >= 8:
        return "HOOG", score, factoren
    if score >= 3:
        return "MIDDEN", score, factoren
    return "LAAG", score, factoren


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def adres_str(kvk_data: dict) -> str:
    adres = kvk_data.get("adres", {}).get("binnenlandsAdres", {})
    delen = [
        adres.get("straatnaam", ""),
        str(adres.get("huisnummer", "")),
        adres.get("postcode", ""),
        adres.get("plaats", ""),
    ]
    return " ".join(d for d in delen if d).strip()


# ──────────────────────────────────────────────
# Helpers voor v1 basisprofiel veldstructuur
# ──────────────────────────────────────────────

def get_rechtsvorm(bp: dict) -> str:
    return bp.get("_embedded", {}).get("eigenaar", {}).get("rechtsvorm", "-")

def get_sbi_codes(bp: dict) -> list:
    return bp.get("sbiActiviteiten", [])

def get_oprichtingsdatum(bp: dict) -> str:
    raw = bp.get("formeleRegistratiedatum") or bp.get("materieleRegistratie", {}).get("datumAanvang", "")
    if raw and len(raw) == 8 and raw.isdigit():
        return f"{raw[6:8]}-{raw[4:6]}-{raw[0:4]}"
    return raw or "-"

def get_medewerkers(bp: dict) -> str:
    val = bp.get("totaalWerkzamePersonen")
    return str(val) if val is not None else "-"

def get_websites(bp: dict) -> list:
    return bp.get("_embedded", {}).get("hoofdvestiging", {}).get("websites", [])

def get_volledig_adres(bp: dict) -> str:
    adressen = bp.get("_embedded", {}).get("hoofdvestiging", {}).get("adressen", [])
    if adressen:
        return adressen[0].get("volledigAdres", "")
    return ""

def get_handelsnamen(bp: dict) -> list:
    return [h.get("naam", "") for h in bp.get("handelsnamen", []) if h.get("naam")]


# ──────────────────────────────────────────────
# Adverse media search
# ──────────────────────────────────────────────

def zoek_adverse_media(naam: str) -> dict:
    zoektermen = [
        f'"{naam}" fraude',
        f'"{naam}" oplichting OR witwassen',
        f'"{naam}" sanctie OR faillissement',
    ]
    resultaten = []
    try:
        with DDGS() as ddgs:
            for term in zoektermen:
                for r in ddgs.text(term, max_results=3, region="nl-nl"):
                    resultaten.append({
                        "zoekterm": term,
                        "titel": r.get("title", ""),
                        "url":   r.get("href", ""),
                        "tekst": r.get("body", "")[:200],
                    })
        return {"success": True, "resultaten": resultaten}
    except Exception as e:
        return {"success": False, "error": str(e)}


RISICO_KLEUR = {"HOOG": "🔴", "MIDDEN": "🟡", "LAAG": "🟢"}
RISICO_CSS   = {"HOOG": "error", "MIDDEN": "warning", "LAAG": "success"}


# ──────────────────────────────────────────────
# PDF generatie
# ──────────────────────────────────────────────

def genereer_pdf(kvk_data, basisprofiel, screening, risico_klasse, score, factoren, toelichting, referentie, nu):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    BLAUW  = (26, 58, 92)
    GRIJS  = (90, 90, 90)
    LICHT  = (240, 244, 250)
    ROOD   = (180, 30, 30)
    ORANJE = (180, 100, 0)
    GROEN  = (20, 120, 60)

    risico_kleur_map = {"HOOG": ROOD, "MIDDEN": ORANJE, "LAAG": GROEN}

    # Header balk
    pdf.set_fill_color(*BLAUW)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_xy(10, 7)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "WWFT Cliëntenonderzoek", ln=True)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Wet ter voorkoming van witwassen en financieren van terrorisme", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(34)

    def sectie_titel(tekst):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(*BLAUW)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, f"  {tekst}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def sanitize(tekst: str) -> str:
        return (tekst
            .replace("–", "-").replace("—", "-")
            .replace("’", "'").replace("‘", "'")
            .replace("“", '"').replace("”", '"')
            .encode("latin-1", errors="replace").decode("latin-1"))

    def rij(label, waarde, achtergrond=False):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*LICHT)
        pdf.cell(55, 6, sanitize(label), fill=achtergrond)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(0, 6, sanitize(str(waarde)) if waarde else "-", ln=True, fill=achtergrond)

    # Metagegevens
    sectie_titel("Rapportgegevens")
    rij("Referentie:",     referentie, True)
    rij("Datum/tijd:",     nu.strftime("%d-%m-%Y %H:%M"), False)
    rij("Uitvoerder:",     "[medewerker invullen]", True)
    pdf.ln(4)

    # Cliëntgegevens
    sectie_titel("Cliëntgegevens")
    bedrijfsnaam = kvk_data.get("naam", "–")
    rij("KvK-nummer:",     kvk_data.get("kvkNummer", "–"), True)
    rij("Naam:",           bedrijfsnaam, False)
    rij("Rechtsvorm:",     basisprofiel.get("rechtsvorm", "–"), True)
    rij("Adres:",          adres_str(kvk_data) or "–", False)
    rij("Oprichting:",     basisprofiel.get("datumOprichting", "–"), True)
    rij("Medewerkers:",    basisprofiel.get("aantalMedewerkers", "–"), False)
    pdf.ln(4)

    # SBI codes
    sbi_codes = basisprofiel.get("sbiCodes", [])
    if sbi_codes:
        sectie_titel("Activiteiten (SBI-codes)")
        for i, sbi in enumerate(sbi_codes):
            code = sbi.get("sbiCode", "")
            omschrijving = sbi.get("sbiOmschrijving", "")
            rij(f"SBI {code}:", omschrijving, i % 2 == 0)
        pdf.ln(4)

    # UBO
    sectie_titel("UBO-identificatie")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GRIJS)
    pdf.multi_cell(0, 6, sanitize("Niet gescreend via API - KvK UBO Register API koppeling nog niet beschikbaar.\nHandmatige verificatie via kvk.nl/ubo-register vereist."))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Screening
    sectie_titel("Sanctie- en PEP-screening")
    bron = "OpenSanctions (EU/VN/OFAC/PEP, ~40 databronnen)"
    if screening.get("geen_key"):
        uitkomst = "Niet uitgevoerd – API key niet beschikbaar"
        hits_str = "–"
    elif not screening.get("success"):
        uitkomst = "Mislukt – zie foutmelding"
        hits_str = "–"
    else:
        hits = screening.get("hits", 0)
        hoog = screening.get("hoog_risico", 0)
        uitkomst = f"Treffers gevonden ({hits})" if hits > 0 else "Geen treffers gevonden"
        hits_str = str(hits)
        if hoog > 0:
            uitkomst = f"HOGE SCORE TREFFERS ({hoog}) - direct actie vereist"

    rij("Bron:", bron, True)
    rij("Uitkomst:", uitkomst, False)
    rij("Treffers (>70%):", hits_str, True)
    pdf.ln(4)

    # Risicobeoordeling
    sectie_titel("Risicobeoordeling")
    kleur = risico_kleur_map.get(risico_klasse, GRIJS)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*kleur)
    pdf.cell(0, 9, f"Classificatie: {risico_klasse}  (score: {score})", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Risicobepalende factoren:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    if factoren:
        for f in factoren:
            pdf.cell(5, 5, "")
            pdf.cell(0, 5, sanitize(f"- {f}"), ln=True)
    else:
        pdf.cell(0, 5, "    - Geen bijzondere risicofactoren geidentificeerd", ln=True)
    pdf.ln(2)
    if toelichting.strip():
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "Toelichting medewerker:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, sanitize(toelichting.strip()))
    pdf.ln(4)

    # Conclusie
    sectie_titel("Conclusie en vervolgactie")
    if risico_klasse == "HOOG":
        conclusie = "Verscherpt cliëntenonderzoek vereist conform art. 8 WWFT.\nMelding compliance officer verplicht."
    elif risico_klasse == "MIDDEN":
        conclusie = "Standaard cliëntenonderzoek van toepassing.\nVerhoogde alertheid gedurende de relatie aanbevolen."
    else:
        conclusie = "Standaard cliëntenonderzoek van toepassing."

    hertoetsing = nu.strftime("%d-%m-") + str(nu.year + 1)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 6, sanitize(conclusie))
    pdf.ln(1)
    rij("Volgende hertoetsing:", hertoetsing, True)
    pdf.ln(6)

    # Footer
    pdf.set_y(-18)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRIJS)
    pdf.cell(0, 5, f"Gegenereerd door WWFT Check Tool v0.1  -  {referentie}  -  {nu.strftime('%d-%m-%Y %H:%M')}", align="C")

    return bytes(pdf.output())


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

with st.sidebar:
    st.title("🔍 WWFT Check Tool")
    st.caption("Wet ter voorkoming van witwassen en financieren van terrorisme")
    st.divider()
    if DEMO_MODUS:
        st.warning("**Demo modus actief**\nGeen KVK_API_KEY gevonden. Er worden voorbeeldgegevens gebruikt.")
    else:
        st.success("KvK API verbonden")
    st.divider()
    st.markdown("**Stappen**")
    st.markdown("1. KvK-nummer invoeren\n2. Gegevens ophalen\n3. Screening starten\n4. Risicobeoordeling\n5. Rapport downloaden")
    st.divider()
    st.caption("v0.1 – Concept / Demo")


# ──────────────────────────────────────────────
# Stap 1: KvK-nummer invoeren
# ──────────────────────────────────────────────

st.header("Cliëntenonderzoek starten")

with st.form("kvk_form"):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        zoekterm_input = st.text_input(
            "Zoeken op naam of KvK-nummer",
            placeholder="bijv. Onesti B.V.  of  12345678",
        )
    with col2:
        zoektype = st.radio("Zoeken op", ["Naam", "KvK-nummer"], horizontal=True)
    with col3:
        st.write("")
        st.write("")
        zoeken = st.form_submit_button("Zoeken →", use_container_width=True, type="primary")

if zoeken:
    zoekterm = zoekterm_input.strip()
    if not zoekterm:
        st.error("Voer een naam of KvK-nummer in.")
        st.stop()

    op_naam = (zoektype == "Naam")

    with st.spinner("KvK raadplegen…"):
        zoek_result = zoek_kvk(zoekterm, op_naam=op_naam)

    if not zoek_result["success"]:
        st.error(f"Fout bij KvK-opvraging: {zoek_result['error']}")
        st.stop()

    st.session_state["zoekresultaten"] = zoek_result["resultaten"]
    st.session_state.pop("kvk_data", None)
    st.session_state.pop("basisprofiel", None)
    st.session_state.pop("screening", None)

# Toon zoekresultaten als er meerdere zijn
if "zoekresultaten" in st.session_state and "kvk_data" not in st.session_state:
    resultaten = st.session_state["zoekresultaten"]

    if len(resultaten) == 1:
        # Direct doorgaan met enige resultaat
        gekozen = resultaten[0]
    else:
        st.subheader(f"🔎 {len(resultaten)} resultaten gevonden – kies het juiste bedrijf")
        opties = {
            f"{r.get('naam', '?')} — KvK {r.get('kvkNummer', '?')} — "
            f"{r.get('adres', {}).get('binnenlandsAdres', {}).get('plaats', '')}": r
            for r in resultaten
        }
        keuze_label = st.radio("Selecteer bedrijf", list(opties.keys()))
        if st.button("Dit bedrijf selecteren →", type="primary"):
            gekozen = opties[keuze_label]
        else:
            st.stop()

    # Href's uit de links array van de zoekrespons
    links = {l["rel"]: l["href"] for l in gekozen.get("links", [])}
    kvk_nummer = gekozen.get("kvkNummer", "")

    with st.spinner("Basisprofiel ophalen…"):
        profiel_result = haal_basisprofiel(kvk_nummer, href=links.get("basisprofiel"))

    st.session_state["kvk_data"]    = gekozen
    st.session_state["basisprofiel"] = profiel_result.get("data", {})
    st.session_state["kvk_nummer"]  = kvk_nummer
    st.session_state.pop("screening", None)
    st.rerun()


# ──────────────────────────────────────────────
# Stap 2: Bedrijfsgegevens tonen
# ──────────────────────────────────────────────

if "kvk_data" in st.session_state:
    kvk_data     = st.session_state["kvk_data"]
    basisprofiel = st.session_state["basisprofiel"]
    bedrijfsnaam = kvk_data.get("naam", "Onbekend")

    st.divider()
    st.subheader(f"📋 {bedrijfsnaam}")

    # Waarschuwing als bedrijf uitgeschreven is
    datum_uit = basisprofiel.get("datumUitschrijving")
    if datum_uit:
        st.error(f"⚠️ Dit bedrijf is uitgeschreven uit het handelsregister op {datum_uit}.")

    rechtsvorm    = get_rechtsvorm(basisprofiel)
    oprichting    = get_oprichtingsdatum(basisprofiel)
    medewerkers   = get_medewerkers(basisprofiel)
    volledig_adres = get_volledig_adres(basisprofiel) or adres_str(kvk_data)
    websites      = get_websites(basisprofiel)
    handelsnamen  = get_handelsnamen(basisprofiel)

    col1, col2, col3 = st.columns(3)
    col1.metric("KvK-nummer",       kvk_data.get("kvkNummer", "-"))
    col1.metric("Rechtsvorm",       rechtsvorm)
    col2.metric("Adres",            volledig_adres or "-")
    col2.metric("Oprichtingsdatum", oprichting)
    col3.metric("Medewerkers",      medewerkers)

    if len(handelsnamen) > 1:
        st.info(f"**Handelsnamen:** {', '.join(handelsnamen)}")

    if websites:
        st.write(f"**Website:** {', '.join(websites)}")

    sbi_codes = get_sbi_codes(basisprofiel)
    if sbi_codes:
        st.write("**Activiteiten (SBI-codes):**")
        for sbi in sbi_codes:
            code = str(sbi.get("sbiCode", ""))
            omschrijving = sbi.get("sbiOmschrijving", "")
            label = "🔴 Hoog-risico sector" if code in HOOG_RISICO_SBI else \
                    "🟡 Aandachtssector" if code in MIDDEN_RISICO_SBI else "🟢 Standaard sector"
            st.write(f"- **{code}**: {omschrijving} — {label}")

    st.info(
        "**UBO-register:** UBO-gegevens zijn niet beschikbaar in de huidige API-verbinding. "
        "Aanvraag voor de KvK UBO Register API is vereist, of raadpleeg handmatig via kvk.nl/ubo-register.",
        icon="ℹ️",
    )

    # ──────────────────────────────────────────
    # Stap 3: Screening
    # ──────────────────────────────────────────

    st.divider()
    st.subheader("🔎 Sanctie- en PEP-screening")
    st.caption("Via OpenSanctions – dekt EU, VN, OFAC sanctielijsten (~40 bronnen)")
    st.info(
        "**Reikwijdte screening:** OpenSanctions dekt officiële sanctielijsten (EU, VN, OFAC) en "
        "bekende politiek prominente personen (PEPs) uit publieke registers. "
        "**Niet gedekt:** uitgebreide commerciële PEP-databases (bijv. World-Check). "
        "Voor hoog-risico cliënten is aanvullende PEP-screening via een betaalde databron aanbevolen.",
        icon="ℹ️",
    )

    if st.button("Start screening", type="primary"):
        with st.spinner(f"Screening van '{bedrijfsnaam}' via OpenSanctions…"):
            screening = screen_opensanctions(bedrijfsnaam, "Company")
        st.session_state["screening"] = screening

    if "screening" in st.session_state:
        screening = st.session_state["screening"]

        if not screening["success"]:
            if screening.get("geen_key"):
                st.warning(
                    "**OpenSanctions API key niet ingesteld.**\n\n"
                    "Registreer gratis op [opensanctions.org/api](https://www.opensanctions.org/api/) "
                    "en voeg de key toe aan je `.env` bestand:\n\n"
                    "```\nOPENSANCTIONS_API_KEY=jouw_key_hier\n```\n\n"
                    "Herstart daarna de app. De risicobeoordeling loopt door zonder screeningresultaat."
                )
            else:
                st.error(f"Screening mislukt: {screening.get('error', 'Onbekende fout')}")
        else:
            hits      = screening.get("hits", 0)
            hoog      = screening.get("hoog_risico", 0)
            resultaten = screening.get("resultaten", [])

            if hoog > 0:
                st.error(f"⚠️ {hoog} hoge-score treffer(s) op sanctielijsten!")
            elif hits > 0:
                st.warning(f"⚠️ {hits} mogelijke treffer(s) gevonden – nader onderzoek vereist")
            else:
                st.success("✅ Geen treffers op sanctielijsten (OpenSanctions)")

            if resultaten:
                with st.expander("Screeningresultaten bekijken"):
                    for r in resultaten:
                        score_val  = r.get("score", 0)
                        entity     = r.get("entity", {})
                        props      = entity.get("properties", {})
                        naam       = props.get("name", ["Onbekend"])[0]
                        topics     = ", ".join(props.get("topics", [])) or "–"
                        landen     = ", ".join(props.get("country", [])) or "–"
                        icon = "🔴" if score_val >= 0.85 else "🟡" if score_val >= 0.70 else "⚪"
                        st.write(
                            f"{icon} **{naam}** &nbsp;|&nbsp; Score: {score_val:.0%} "
                            f"&nbsp;|&nbsp; Topics: {topics} &nbsp;|&nbsp; Land: {landen}"
                        )
            else:
                st.write("Geen resultaten teruggegeven door OpenSanctions voor deze naam.")

        # ──────────────────────────────────────
        # Stap 3b: Adverse media search
        # ──────────────────────────────────────

        st.divider()
        st.subheader("📰 Adverse media search")
        st.caption("Zoekt via DuckDuckGo op negatief nieuws (fraude, witwassen, sanctie, faillissement)")

        if st.button("Start media search", type="secondary"):
            with st.spinner(f"Zoeken naar negatief nieuws over '{bedrijfsnaam}'…"):
                media_result = zoek_adverse_media(bedrijfsnaam)
            st.session_state["media"] = media_result

        if "media" in st.session_state:
            media = st.session_state["media"]
            if not media["success"]:
                st.warning(f"Media search mislukt: {media.get('error', '')}")
            else:
                resultaten_media = media.get("resultaten", [])
                if not resultaten_media:
                    st.success("✅ Geen negatief nieuws gevonden")
                else:
                    st.warning(f"⚠️ {len(resultaten_media)} resultaten gevonden – beoordeel handmatig")
                    for r in resultaten_media:
                        with st.expander(r["titel"][:100]):
                            st.write(r["tekst"])
                            st.markdown(f"[Bekijk artikel]({r['url']})")
                            st.caption(f"Zoekopdracht: {r['zoekterm']}")

        # ──────────────────────────────────────
        # Stap 4: Risicobeoordeling
        # ──────────────────────────────────────

        st.divider()
        st.subheader("⚖️ Risicobeoordeling")

        risico_klasse, score, factoren = bereken_risico(basisprofiel, screening)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Risicoclassificatie", f"{RISICO_KLEUR[risico_klasse]} {risico_klasse}")
            st.metric("Totaalscore", score)
        with col2:
            st.write("**Risicobepalende factoren:**")
            if factoren:
                for f in factoren:
                    st.write(f"- {f}")
            else:
                st.write("- Geen bijzondere risicofactoren geïdentificeerd")

        toelichting = st.text_area(
            "Toelichting / motivatie (optioneel)",
            placeholder="Voeg hier eventuele aanvullende informatie of afwijkende beoordeling toe…",
            height=80,
        )

        # ──────────────────────────────────────
        # Stap 5: Rapport
        # ──────────────────────────────────────

        st.divider()
        st.subheader("📄 Rapport genereren")

        nu = datetime.now()
        referentie = f"WWFT-{st.session_state.get('kvk_nummer', '?')}-{nu.strftime('%Y%m%d')}"

        rapport = f"""WWFT CLIËNTENONDERZOEK – RAPPORT
=====================================
Referentie  : {referentie}
Datum/tijd  : {nu.strftime('%d-%m-%Y %H:%M')}
Uitvoerder  : [medewerker invullen]

CLIËNTGEGEVENS
--------------
KvK-nummer   : {kvk_data.get('kvkNummer', '-')}
Naam         : {bedrijfsnaam}
Rechtsvorm   : {basisprofiel.get('rechtsvorm', '-')}
Adres        : {adres_str(kvk_data) or '-'}
Oprichting   : {basisprofiel.get('datumOprichting', '-')}

ACTIVITEITEN (SBI-CODES)
------------------------
{chr(10).join(f"  {s['sbiCode']}: {s['sbiOmschrijving']}" for s in sbi_codes) if sbi_codes else '  Niet beschikbaar'}

UBO-IDENTIFICATIE
-----------------
  Niet gescreend via API – UBO Register API koppeling nog niet beschikbaar.
  Handmatige verificatie via kvk.nl/ubo-register vereist.

SANCTIE- EN PEP-SCREENING
--------------------------
  Bron         : OpenSanctions (EU/VN/OFAC/PEP, ~40 databronnen)
  Uitkomst     : {'TREFFERS GEVONDEN – zie dossier voor details' if screening.get('hits', 0) > 0 else 'Geen treffers gevonden'}
  Score-hits   : {screening.get('hits', 0)} (drempel: 70%)
  Hoge scores  : {screening.get('hoog_risico', 0)} (drempel: 85%)

RISICOBEOORDELING
-----------------
  Classificatie  : {risico_klasse}
  Score          : {score}

  Risicobepalende factoren:
{chr(10).join(f'  - {f}' for f in factoren) if factoren else '  - Geen bijzondere factoren'}

  Toelichting medewerker:
  {toelichting.strip() if toelichting.strip() else '(geen toelichting opgegeven)'}

CONCLUSIE EN VERVOLGACTIE
--------------------------
  {'Verscherpt cliëntenonderzoek vereist conform art. 8 WWFT. Melding compliance officer.' if risico_klasse == 'HOOG' else 'Standaard cliëntenonderzoek van toepassing. Verhoogde alertheid gedurende de relatie.' if risico_klasse == 'MIDDEN' else 'Standaard cliëntenonderzoek van toepassing.'}

  Volgende hertoetsing: {nu.strftime('%d-%m-%Y').replace(str(nu.year), str(nu.year + 1))}

=====================================
Gegenereerd door WWFT Check Tool v0.1
{referentie}
"""

        with st.expander("Tekstversie bekijken"):
            st.text_area("Rapport", rapport, height=300)

        pdf_bytes = genereer_pdf(
            kvk_data, basisprofiel, screening,
            risico_klasse, score, factoren,
            toelichting, referentie, nu,
        )
        bestandsnaam = f"wwft_{st.session_state.get('kvk_nummer', 'check')}_{nu.strftime('%Y%m%d_%H%M')}.pdf"
        st.download_button(
            label="⬇️ Download rapport (PDF)",
            data=pdf_bytes,
            file_name=bestandsnaam,
            mime="application/pdf",
            type="primary",
        )

        st.caption(
            "💡 In de volledige versie: PDF-export, opslag in centraal dossier, "
            "automatische melding compliance officer bij hoog risico."
        )
