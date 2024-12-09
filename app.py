import streamlit as st
import pandas as pd
from typing import Optional
from xml.etree import ElementTree
import requests

# Functie om de data in te laden
@st.cache
def load_data(file_path):
    return pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')

# WetboekParser klasse
class WetboekParser:
    def __init__(self, bwb_id: str = "BWBR0001903", datum: str = "2024-04-09"):
        self.bwb_id = bwb_id
        self.datum = datum
        self.base_url = f"https://repository.officiele-overheidspublicaties.nl/bwb/{bwb_id}/{datum}/xml/{bwb_id}_{datum}.xml"
        self.root = None
        self._load_xml()

    def _load_xml(self) -> None:
        response = requests.get(self.base_url)
        response.raise_for_status()
        self.root = ElementTree.fromstring(response.content)

    def _get_text_from_element(self, element) -> str:
        text_parts = []
        for al in element.findall('al'):
            if al.text:
                text_parts.append(al.text.strip())
        return '\n'.join(filter(None, text_parts))

    def get_artikel(self, artikel_nummer: int, lid_nummer: Optional[int] = None) -> str:
        artikel = self.root.find(f".//artikel[@code='a-{artikel_nummer}']")
        if artikel is None:
            raise ValueError(f"Artikel {artikel_nummer} niet gevonden")

        if lid_nummer is None:
            text_parts = []
            leden = artikel.findall('lid')
            for lid in leden:
                lid_text = self._get_text_from_element(lid)
                if lid_text:
                    text_parts.append(lid_text)
            return '\n\n'.join(text_parts)
        else:
            leden = artikel.findall('lid')
            for lid in leden:
                lidnr = lid.find('lidnr')
                if lidnr is not None and lidnr.text == str(lid_nummer):
                    return self._get_text_from_element(lid)
            raise ValueError(f"Lid {lid_nummer} niet gevonden in artikel {artikel_nummer}")

# Data laden
data_path = "data.csv"
data = load_data(data_path)

# Titel
st.title("Key Lookup Tool")

# Inputvelden
st.subheader("Zoek naar een waarde met de key")
artikel = st.text_input("Artikel (verplicht)", "").strip()
lit = st.text_input("Lit (optioneel)", "").strip()
sub = st.text_input("Sub (optioneel)", "").strip()
graad = st.text_input("Graad (optioneel)", "").strip()

# Resultaten tonen
if artikel:
    try:
        artikel_nummer = int(artikel)
        parser = WetboekParser()

        # Toon volledige artikeltekst
        st.write(f"Volledige tekst van artikel {artikel_nummer}:")
        artikel_tekst = parser.get_artikel(artikel_nummer)
        st.text(artikel_tekst)

        # Key samenstellen
        key = f"{artikel}-{lit if lit else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"

        if st.button("Zoek"):
            resultaten = data[data['Key'] == key]
            if not resultaten.empty:
                st.write("Resultaten:")
                st.table(resultaten['Nieuw Wetboek van Strafvordering'])
            else:
                st.warning("Geen resultaten gevonden voor deze key.")
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Er is een fout opgetreden: {str(e)}")
else:
    st.error("Vul het artikelnummer in. Dit veld is verplicht.")
