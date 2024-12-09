import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO

# Custom CSS styling
st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
        }
        .main {
            padding: 2rem;
        }
        .css-1d391kg {  /* Inputs styling */
            background-color: white;
            border-radius: 5px;
            padding: 1px;
        }
        .stButton>button {
            background-color: #0066cc;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 2rem;
            border: none;
        }
        .stButton>button:hover {
            background-color: #0052a3;
        }
        div[data-testid="stTable"] {
            background-color: white;
            padding: 1rem;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .law-text {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

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
            output_lines = [f"**Artikel {article_number}**"]
            
            for lid in artikel.iter('lid'):
                lidnr_el = lid.find('lidnr')
                if lidnr_el is not None and lidnr_el.text:
                    output_lines.append(f"\n**{lidnr_el.text.strip()}.** ")
                
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
                            output_lines.append(f"\n*{li_nr}* {li_al_lines[0]}")
                            output_lines.extend([f"  {line}" for line in li_al_lines[1:]])
            
            return "\n".join(output_lines)
    
    return f"Artikel {article_number} niet gevonden."

# App initialization with custom styling
st.markdown("""
    # Transponeringstabel nieuw Wetboek van Strafvordering
    ---
""")

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

# Create columns for input fields
st.markdown("### Zoek naar een waarde met de key")
col1, col2 = st.columns(2)

with col1:
    artikel = st.text_input("Artikel (verplicht)", "").strip()
    sub = st.text_input("Sub (optioneel)", "").strip()

with col2:
    lit = st.text_input("Lit (optioneel)", "").strip()
    graad = st.text_input("Graad (optioneel)", "").strip()

if artikel:
    key = f"{artikel}-{lit if lit else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
    
    if st.button("Zoek", key="search_button"):
        # Zoek de resultaten
        resultaten = data[data['Key'] == key]
        if not resultaten.empty:
            st.markdown("### Nieuw artikel")
            st.table(resultaten['Nieuw Wetboek van Strafvordering'])
            
            # Toon de originele wettekst in een mooie container
            st.markdown("### Originele wettekst")
            wettekst = extract_article_text(st.session_state['xml_content'], artikel)
            st.markdown(f"""
                <div class="law-text">
                    {wettekst}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Geen resultaten gevonden voor deze key.")
else:
    st.error("Vul het artikelnummer in. Dit veld is verplicht.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        © 2024 Wetboek van Strafvordering Transponeringstabel
    </div>
""", unsafe_allow_html=True)
