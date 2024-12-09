import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO

@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')

@st.cache_data
def fetch_and_parse_xml(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_article_text(xml_content, article_number):
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

def get_available_values(data, column, filters=None):
    if filters:
        for key, value in filters.items():
            if value:
                data = data[data[key] == value]
    
    # Split the 'Key' column and get unique values for the specified position
    values = data['Key'].str.split('-').str[column].unique()
    # Remove '0' values and sort
    values = sorted([v for v in values if v != '0'])
    return [''] + values if values is not None else ['']

# App initialization
st.title("Transponeringstabel nieuw Wetboek van Strafvordering")

# Load data
data_path = "data.csv"
data = load_data(data_path)

# Load XML content once at startup
url = "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0001903/2002-03-08_0/xml/BWBR0001903_2002-03-08_0.xml"
try:
    xml_content = fetch_and_parse_xml(url)
    st.session_state['xml_content'] = xml_content
except Exception as e:
    st.error(f"Fout bij het laden van de XML: {str(e)}")
    st.stop()

# Input fields
st.subheader("Zoek naar een waarde met de key")

# Artikel blijft een text input
artikel = st.text_input("Artikel (verplicht)", "").strip()

if artikel:
    # Check if artikel exists in the data
    matching_keys = data['Key'].str.startswith(f"{artikel}-")
    
    if matching_keys.any():
        # Get available lit values based on selected artikel
        lit_options = get_available_values(data, 1, {'Key': lambda x: x.startswith(f"{artikel}-")})
        lit = st.selectbox("Lit (optioneel)", options=lit_options).strip()
        
        # Get available sub values based on selected artikel and lit
        filters = {'Key': lambda x: x.startswith(f"{artikel}-{lit if lit else '0'}-")}
        sub_options = get_available_values(data, 2, filters)
        sub = st.selectbox("Sub (optioneel)", options=sub_options).strip()
        
        # Get available graad values based on selected artikel, lit, and sub
        filters = {'Key': lambda x: x.startswith(f"{artikel}-{lit if lit else '0'}-{sub if sub else '0'}-")}
        graad_options = get_available_values(data, 3, filters)
        graad = st.selectbox("Graad (optioneel)", options=graad_options).strip()

        # Create key and search
        key = f"{artikel}-{lit if lit else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
        
        if st.button("Zoek"):
            # Zoek de resultaten
            resultaten = data[data['Key'] == key]
            if not resultaten.empty:
                st.write("Nieuw artikel:")
                st.table(resultaten['Nieuw Wetboek van Strafvordering'])
                
                # Toon de huidige wettekst
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
