import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO

# Force light theme and override dark mode
st.markdown("""
    <style>
        /* Force light theme */
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important;
        }
        
        [data-testid="stHeader"] {
            background-color: #ffffff !important;
        }
        
        [data-testid="stToolbar"] {
            background-color: #ffffff !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
        }
        
        /* Text colors for dark mode compatibility */
        .stMarkdown, p, h1, h2, h3 {
            color: #31333F !important;
        }
        
        /* Input styling */
        .stTextInput > div > div > input {
            background-color: #ffffff;
            color: #31333F;
            border: 1px solid #ddd;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #1f77b4;
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 4px;
            font-weight: 500;
        }
        
        .stButton > button:hover {
            background-color: #145c8e;
        }
        
        /* Table styling */
        [data-testid="stTable"] {
            background-color: #ffffff;
            color: #31333F;
        }
        
        /* Container styling */
        .law-text {
            background-color: #ffffff;
            color: #31333F;
            padding: 1.5rem;
            border-radius: 4px;
            border: 1px solid #ddd;
            margin: 1rem 0;
            line-height: 1.6;
        }
        
        /* Warning and error messages */
        .stAlert {
            background-color: #ffffff;
            color: #31333F;
            border: 1px solid #ddd;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: #666;
            padding: 2rem 0;
            margin-top: 2rem;
            border-top: 1px solid #ddd;
        }
    </style>
""", unsafe_allow_html=True)

# Configure page
st.set_page_config(
    page_title="Wetboek van Strafvordering Transponeringstabel",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

# App content with padding
st.markdown('<div style="padding: 1rem;">', unsafe_allow_html=True)

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

# Input fields with better spacing
st.markdown("### Zoek naar een waarde met de key")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    artikel = st.text_input("Artikel (verplicht)", "").strip()
    sub = st.text_input("Sub (optioneel)", "").strip()

with col2:
    lit = st.text_input("Lit (optioneel)", "").strip()
    graad = st.text_input("Graad (optioneel)", "").strip()

# Center the search button
st.markdown("<div style='text-align: center; padding: 1rem 0;'>", unsafe_allow_html=True)

if artikel:
    key = f"{artikel}-{lit if lit else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
    
    if st.button("Zoek", key="search_button"):
        resultaten = data[data['Key'] == key]
        if not resultaten.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Nieuw artikel")
            st.table(resultaten['Nieuw Wetboek van Strafvordering'])
            
            st.markdown("<br>", unsafe_allow_html=True)
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

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class="footer">
        © 2024 Wetboek van Strafvordering Transponeringstabel
    </div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
