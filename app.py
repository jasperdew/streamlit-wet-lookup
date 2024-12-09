import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from io import StringIO

# Functie om de data in te laden
@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')

# Functie om originele wettekst op te halen met structuur
def extract_article_text_from_url(url, article_number):
    response = requests.get(url)
    response.raise_for_status()  # Fout als de request mislukt
    xml_content = response.text
    
    # Parse de XML content vanuit de string
    tree = ET.parse(StringIO(xml_content))
    root = tree.getroot()
    
    for artikel in root.iter('artikel'):
        nr_element = artikel.find('./kop/nr')
        # Vergelijk direct als string, zodat bv. '67a' ook werkt.
        if nr_element is not None and nr_element.text.strip() == article_number:
            al_texts = []
            for idx, al in enumerate(artikel.findall('al'), start=1):
                al_content = al.text.strip() if al.text else ''
                # Hier kunnen we eventueel ook zoeken naar sub-elementen, zoals lit, sub of graad, als die bestaan
                # Bij gebrek aan voorbeeld-XML met dergelijke elementen, tonen we hier enkel 'Lid'.
                al_texts.append(f"Lid {idx}:\n{al_content}\n")
            full_text = '\n'.join(al_texts)
            return full_text.strip()
    
    return f"Artikel {article_number} niet gevonden."

# Data laden
data_path = "data.csv"  # Naam van je CSV-bestand
data = load_data(data_path)

# Titel
st.title("Transponeringstabel nieuw Wetboek van Strafvordering")

# Inputvelden
st.subheader("Zoek naar een waarde met de key")
artikel = st.text_input("Artikel (verplicht)", "").strip()
lit = st.text_input("Lit (optioneel)", "").strip()
sub = st.text_input("Sub (optioneel)", "").strip()
graad = st.text_input("Graad (optioneel)", "").strip()

if artikel:
    # Key samenstellen met standaardwaarden voor optionele velden
    key = f"{artikel}-{lit if lit else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
    
    if st.button("Zoek"):
        # Zoek de resultaten in de CSV
        resultaten = data[data['Key'] == key]
        if not resultaten.empty:
            st.write("Resultaten voor het nieuwe Wetboek van Strafvordering:")
            st.table(resultaten['Nieuw Wetboek van Strafvordering'])
            
            # Toon ook de originele huidige wet, met gestructureerde breakdown
            url = "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0001903/2002-03-08_0/xml/BWBR0001903_2002-03-08_0.xml"
            originele_tekst = extract_article_text_from_url(url, artikel)
            
            st.subheader(f"Originele huidige wet voor artikel {artikel}:")
            st.write(originele_tekst)
        else:
            st.warning("Geen resultaten gevonden voor deze key.")
else:
    st.error("Vul het artikelnummer in. Dit veld is verplicht.")
    
