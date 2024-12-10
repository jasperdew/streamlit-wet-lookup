import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO

@st.cache_data
def load_data(file_path):
    """
    Laadt de transponeringstabel vanuit een Excel bestand.
    """
    return pd.read_excel(file_path)

@st.cache_data
def load_new_law_text(file_path):
    """
    Laadt de teksten van het nieuwe wetboek vanuit een Excel bestand.
    Maakt een woordenboek van artikelnummers naar wetteksten voor snelle opzoekacties.
    """
    df = pd.read_excel(file_path)
    # Verwijder 'Artikel ' en strip spaties, inclusief spaties binnen het artikelnummer
    return dict(zip(
        df['Artikelnummer'].str.replace('Artikel ', '').str.replace(' ', '').str.strip(),
        df.iloc[:, 1]
    ))

@st.cache_data
def fetch_and_parse_xml(url):
    """
    Haalt de XML van het huidige wetboek op van de overheidswebsite.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_article_text(xml_content, article_number):
    """
    Extraheert de tekst van een specifiek artikel uit de XML van het huidige wetboek.
    Verwerkt alle onderdelen zoals leden, lijsten en externe verwijzingen.
    """
    tree = ET.parse(StringIO(xml_content))
    root = tree.getroot()
    
    for artikel in root.iter('artikel'):
        nr_element = artikel.find('./kop/nr')
        if nr_element is not None and nr_element.text.strip() == article_number:
            output_lines = [f"Artikel {article_number}", ""]
            
            for lid in artikel.iter('lid'):
                lidnr_el = lid.find('lidnr')
                if lidnr_el is not None and lidnr_el.text:
                    output_lines.append(f"{lidnr_el.text.strip()}. ")
                
                for element in lid.iter():
                    if element.tag == 'al':
                        if element.text and element.text.strip():
                            output_lines.append(element.text.strip())
                    elif element.tag == 'extref':
                        if element.text:
                            output_lines.append(element.text.strip())
                        if element.tail and element.tail.strip():
                            output_lines.append(element.tail.strip())
                    elif element.tail and element.tail.strip():
                        output_lines.append(element.tail.strip())
                
                for lijst in lid.findall('lijst'):
                    for li in lijst.findall('li'):
                        li_nr_el = li.find('li.nr')
                        li_nr = li_nr_el.text.strip() if li_nr_el is not None else ''
                        
                        li_content = []
                        for al_el in li.findall('al'):
                            if al_el.text and al_el.text.strip():
                                li_content.append(al_el.text.strip())
                        
                        if li_nr and li_content:
                            output_lines.append(f"{li_nr} {li_content[0]}")
                            output_lines.extend(li_content[1:])
                
                output_lines.append("")
            
            return "\n".join(line.strip() for line in output_lines if line is not None)
    
    return f"Artikel {article_number} niet gevonden."

def get_available_values(data, artikel, position):
    """
    Bepaalt welke waarden beschikbaar zijn voor een bepaalde positie in de artikelstructuur.
    Wordt gebruikt voor het vullen van de selectievakjes voor lid, sub en graad.
    """
    filtered_data = data[data['Key'].str.startswith(f"{artikel}-")]
    
    if filtered_data.empty:
        return []
    
    values = filtered_data['Key'].str.split('-').str[position].unique()
    values = sorted([v for v in values if v != '0'])
    
    return values

def extract_article_numbers(reference_string):
    """
    Haalt de hoofdartikelnummers uit een reeks verwijzingen.
    Bijvoorbeeld: uit '1.2.9, 1, a' wordt '1.2.9' geëxtraheerd.
    Verwijdert alle spaties uit de artikelnummers.
    """
    references = reference_string.split(';')
    article_numbers = []
    for ref in references:
        main_article = ref.split(',')[0].strip()
        if main_article:
            # Verwijder alle spaties uit het artikelnummer
            main_article = main_article.replace(' ', '')
            article_numbers.append(main_article)
    return article_numbers

def display_new_article_text(new_articles, new_law_text):
    """
    Toont de tekst van de nieuwe artikelen.
    Verwerkt zowel enkele als meerdere artikelverwijzingen.
    """
    articles = extract_article_numbers(new_articles)
    
    for article in articles:
        if article in new_law_text:
            st.write(f"**Artikel {article}**")
            st.write(new_law_text[article])
            st.write("---")
        else:
            st.warning(f"Tekst voor artikel {article} niet gevonden in het nieuwe wetboek")

# Initialisatie van de applicatie
st.set_page_config(layout="wide")  # Gebruik de volledige breedte
st.title("Transponeringstabel nieuw Wetboek van Strafvordering")

# Inladen van de benodigde gegevens
data_path = "data.xlsx"  # Changed from data.csv to data.xlsx
new_law_path = "Wetboek_Strafvordering_Geformatteerd.xlsx"

try:
    data = load_data(data_path)
    new_law_text = load_new_law_text(new_law_path)
except Exception as e:
    st.error(f"Fout bij het laden van de gegevens: {str(e)}")
    st.stop()

# XML van het huidige wetboek ophalen
url = "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0001903/2024-10-01_0/xml/BWBR0001903_2024-10-01_0.xml"
try:
    xml_content = fetch_and_parse_xml(url)
    st.session_state['xml_content'] = xml_content
except Exception as e:
    st.error(f"Fout bij het laden van de XML: {str(e)}")
    st.stop()

# Zoekinterface
st.subheader("Zoek naar een waarde met de key")

artikel = st.text_input("Artikel (verplicht)", "").strip()

if artikel:
    matching_keys = data['Key'].str.startswith(f"{artikel}-")
    
    if matching_keys.any():
        lid = sub = graad = ""
        
        # Dynamische selectievakjes voor lid, sub en graad
        lid_values = get_available_values(data, artikel, 1)
        if lid_values:
            lid = st.selectbox("Lid (optioneel)", options=[''] + lid_values).strip()
        
        if lid or not lid_values:
            sub_values = get_available_values(data[data['Key'].str.startswith(f"{artikel}-{lid if lid else '0'}-")], artikel, 2)
            if sub_values:
                sub = st.selectbox("Sub (optioneel)", options=[''] + sub_values).strip()
        
        if sub or not (lid_values or sub_values):
            graad_values = get_available_values(
                data[data['Key'].str.startswith(f"{artikel}-{lid if lid else '0'}-{sub if sub else '0'}-")], 
                artikel, 
                3
            )
            if graad_values:
                graad = st.selectbox("Graad (optioneel)", options=[''] + graad_values).strip()

        # Zoekactie uitvoeren
        key = f"{artikel}-{lid if lid else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
        
        if st.button("Zoek"):
            resultaten = data[data['Key'] == key]
            if not resultaten.empty:
                st.write("Nieuw artikel:")
                st.table(resultaten['Nieuw Wetboek van Strafvordering'])
                
                # Twee kolommen voor oude en nieuwe tekst
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Huidige wettekst:**")
                    wettekst = extract_article_text(st.session_state['xml_content'], artikel)
                    st.markdown(wettekst)
                
                with col2:
                    st.write("**Tekst nieuwe artikelen:**")
                    new_articles_ref = resultaten['Nieuw Wetboek van Strafvordering'].iloc[0]
                    display_new_article_text(new_articles_ref, new_law_text)
            else:
                st.warning("Geen resultaten gevonden voor huidige zoekopdracht (de combinatie van Artikel/Lid/Sub/Graad bestaat niet)")
    else:
        st.warning(f"Geen resultaten gevonden voor artikel {artikel}")
else:
    st.error("Vul het artikelnummer in. Dit veld is verplicht.")

# Footer met bronvermeldingen
st.markdown("---")
st.markdown("### Bronvermeldingen")

# Twee kolommen voor de bronvermeldingen
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Wetboek van Strafvordering**  
    Geraadpleegd op 09-12-2024  
    Gebruikte datum 'geldig op' 01-10-2024 en zichtdatum 01-10-2024  
    Geldend van 01-10-2024 t/m heden  
    Meerdere toekomstige wijzigingen; eerste op 01-10-2025  
    Wijziging(en) op nader te bepalen datum(s); laatste bekendgemaakt in 2022
    """)

with col2:
    st.markdown("""
    **Bronnen:**
    - [Transponeringstabel nieuw Wetboek van Strafvordering](https://www.strafrechtketen.nl/documenten/kamerstukken/2023/03/21/transponeringstabel-nieuw-wetboek-van-strafvordering-oud-naar-nieuw)
    - [Voor boek 1-5 is steeds gebruik gemaakt van "Ambtelijke versie wetsvoorstel Wetboek van Strafvordering". Deze konden ik met hetzelfde script omzetten naar een gestructureerd format. Andere boeken kon ik nog geen ambtelijke versie van vinden.](https://www.rijksoverheid.nl/binaries/rijksoverheid/documenten/publicaties/2020/12/11/ambtelijke-versie-juli-2020-wetsvoorstel-wetboek-van-strafvordering-boek-1/Vaststelling+van+het+nieuwe+Wetboek+van+Strafvordering+Boek+1.pdf)
    """)

# Voeg wat padding toe aan de onderkant
st.markdown("<br><br>", unsafe_allow_html=True)
