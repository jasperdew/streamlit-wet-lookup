import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO

@st.cache_data
def load_data(file_path):
    # laad de data uit t bestand
    return pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')

@st.cache_data
def fetch_and_parse_xml(url):
    # haalt de xml op en geeft m terug
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_article_text(xml_content, article_number):
    # pakt de tekst uit de xml voor n artikel
    tree = ET.parse(StringIO(xml_content))
    root = tree.getroot()
    
    for artikel in root.iter('artikel'):
        nr_element = artikel.find('./kop/nr')
        if nr_element is not None and nr_element.text.strip() == article_number:
            output_lines = [f"Artikel {article_number}\n"]
            
            for lid in artikel.iter('lid'):
                lidnr_el = lid.find('lidnr')
                if lidnr_el is not None and lidnr_el.text:
                    output_lines.append(f"{lidnr_el.text.strip()}. ")
                
                for al in lid.findall('al'):
                    if al.text and al.text.strip():
                        output_lines.append(al.text.strip())
                
                for lijst in lid.findall('lijst'):
                    for li in lijst.findall('li'):
                        li_nr_el = li.find('li.nr')
                        li_nr = li_nr_el.text.strip() if li_nr_el is not None else ''
                        li_al_lines = [al_el.text.strip() for al_el in li.findall('al') 
                                     if al_el.text and al_el.text.strip()]
                        
                        if li_nr and li_al_lines:
                            output_lines.append(f"{li_nr} {li_al_lines[0]}")
                            output_lines.extend(li_al_lines[1:])
            
            return "\n".join(output_lines)
    
    return f"Artikel {article_number} niet gevonden."

def get_available_values(data, artikel, position):
    # ff kijken welke waardes dr zijn voor de dropdown
    # filtert eerst de rows die met t artikel beginnen
    filtered_data = data[data['Key'].str.startswith(f"{artikel}-")]
    
    if filtered_data.empty:
        return []
    
    # splitst de keys en pakt de waardes die we nodig hebben
    values = filtered_data['Key'].str.split('-').str[position].unique()
    
    # gooi de nullen eruit en sorteer t ff netjes
    values = sorted([v for v in values if v != '0'])
    
    return values

# App opstarten
st.title("Transponeringstabel nieuw Wetboek van Strafvordering")

# Data inladen
data_path = "data.csv"
data = load_data(data_path)

# XML ophalen als de app start
url = "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0001903/2024-10-01_0/xml/BWBR0001903_2024-10-01_0.xml"
try:
    xml_content = fetch_and_parse_xml(url)
    st.session_state['xml_content'] = xml_content
except Exception as e:
    st.error(f"Fout bij het laden van de XML: {str(e)}")
    st.stop()

# Input velden
st.subheader("Zoek naar een waarde met de key")

# Artikel blijft een text input
artikel = st.text_input("Artikel (verplicht)", "").strip()

if artikel:
    # kijk of t artikel bestaat in de data
    matching_keys = data['Key'].str.startswith(f"{artikel}-")
    
    if matching_keys.any():
        # eerst ff de variabelen klaarzetten
        lid = sub = graad = ""
        
        # beschikbare lid waardes ophalen
        lid_values = get_available_values(data, artikel, 1)
        if lid_values:
            lid = st.selectbox("Lid (optioneel)", options=[''] + lid_values).strip()
        
        # sub waardes ophalen als er n lid is of als er geen lid waardes zijn
        if lid or not lid_values:
            sub_values = get_available_values(data[data['Key'].str.startswith(f"{artikel}-{lid if lid else '0'}-")], artikel, 2)
            if sub_values:
                sub = st.selectbox("Sub (optioneel)", options=[''] + sub_values).strip()
        
        # graad waardes ophalen als er n sub is of als er geen sub/lid waardes zijn
        if sub or not (lid_values or sub_values):
            graad_values = get_available_values(
                data[data['Key'].str.startswith(f"{artikel}-{lid if lid else '0'}-{sub if sub else '0'}-")], 
                artikel, 
                3
            )
            if graad_values:
                graad = st.selectbox("Graad (optioneel)", options=[''] + graad_values).strip()

        # key maken en zoeken
        key = f"{artikel}-{lid if lid else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
        
        if st.button("Zoek"):
            # kijk wa we kunnen vinden
            resultaten = data[data['Key'] == key]
            if not resultaten.empty:
                st.write("Nieuw artikel:")
                st.table(resultaten['Nieuw Wetboek van Strafvordering'])
                
                # laat de huidige wettekst zien
                st.write("---")
                st.write("**Huidige wettekst:**")
                wettekst = extract_article_text(st.session_state['xml_content'], artikel)
                st.markdown(wettekst)
            else:
                st.warning("Geen resultaten gevonden voor huidige zoekopdracht (de combinatie van Artikel/Lid/Sub/Graad bestaat niet)")
    else:
        st.warning(f"Geen resultaten gevonden voor artikel {artikel}")
else:
    st.error("Vul het artikelnummer in. Dit veld is verplicht.")
