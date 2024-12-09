import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO

@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')

@st.cache_data
def load_new_law_text(file_path):
    """
    Load the new law text from Excel file with additional error checking
    """
    try:
        # Add debug output
        st.write(f"Attempting to load Excel file: {file_path}")
        
        df = pd.read_excel(file_path)
        
        # Debug output to see the structure
        st.write("Excel file structure:")
        st.write(df.head())
        
        # Convert to dictionary for faster lookups
        # Clean up article numbers by removing 'Artikel ' prefix and any whitespace
        article_dict = dict(zip(
            df['Artikelnummer'].str.replace('Artikel ', '').str.strip(),
            df.iloc[:, 1]
        ))
        
        # Debug output for the dictionary
        st.write("First few entries in the article dictionary:")
        first_few = dict(list(article_dict.items())[:3])
        st.write(first_few)
        
        return article_dict
        
    except FileNotFoundError:
        st.error(f"Excel bestand niet gevonden: {file_path}")
        return {}
    except Exception as e:
        st.error(f"Fout bij laden van Excel bestand: {str(e)}")
        return {}

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
    filtered_data = data[data['Key'].str.startswith(f"{artikel}-")]
    
    if filtered_data.empty:
        return []
    
    values = filtered_data['Key'].str.split('-').str[position].unique()
    values = sorted([v for v in values if v != '0'])
    
    return values

def extract_article_numbers(reference_string):
    """
    Extract the main article numbers from reference strings
    """
    # Split on semicolon for multiple references
    references = reference_string.split(';')
    
    # Extract main article numbers
    article_numbers = []
    for ref in references:
        # Split by comma and take the first part
        main_article = ref.split(',')[0].strip()
        if main_article:
            article_numbers.append(main_article)
    
    return article_numbers

def display_new_article_text(new_articles, new_law_text):
    """
    Display the text of new articles, handling multiple article references
    """
    # Debug output
    st.write("Processing article references:", new_articles)
    
    # Get main article numbers
    articles = extract_article_numbers(new_articles)
    st.write("Extracted article numbers:", articles)
    
    # Debug output for new_law_text
    st.write("Available articles in new law text:", list(new_law_text.keys())[:5])
    
    for article in articles:
        if article in new_law_text:
            st.write(f"**Artikel {article}**")
            st.write(new_law_text[article])
            st.write("---")
        else:
            st.warning(f"Tekst voor artikel {article} niet gevonden in het nieuwe wetboek")
            st.write(f"Gezocht artikel: '{article}'")

# App opstarten
st.title("Transponeringstabel nieuw Wetboek van Strafvordering")

# Data inladen
data_path = "data.csv"
new_law_path = "Wetboek_Strafvordering_Geformatteerd.xlsx"

try:
    data = load_data(data_path)
except Exception as e:
    st.error(f"Fout bij laden van data.csv: {str(e)}")
    st.stop()

try:
    new_law_text = load_new_law_text(new_law_path)
except Exception as e:
    st.error(f"Fout bij laden van Excel bestand: {str(e)}")
    st.stop()

# XML ophalen bij het starten van de app
url = "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0001903/2024-10-01_0/xml/BWBR0001903_2024-10-01_0.xml"
try:
    xml_content = fetch_and_parse_xml(url)
    st.session_state['xml_content'] = xml_content
except Exception as e:
    st.error(f"Fout bij het laden van de XML: {str(e)}")
    st.stop()

# Input velden
st.subheader("Zoek naar een waarde met de key")

artikel = st.text_input("Artikel (verplicht)", "").strip()

if artikel:
    matching_keys = data['Key'].str.startswith(f"{artikel}-")
    
    if matching_keys.any():
        lid = sub = graad = ""
        
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

        key = f"{artikel}-{lid if lid else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
        
        if st.button("Zoek"):
            resultaten = data[data['Key'] == key]
            if not resultaten.empty:
                st.write("Nieuw artikel:")
                st.table(resultaten['Nieuw Wetboek van Strafvordering'])
                
                # Display the text of the new articles with more debug info
                st.write("---")
                st.write("**Tekst nieuwe artikelen:**")
                new_articles_ref = resultaten['Nieuw Wetboek van Strafvordering'].iloc[0]
                st.write("Gevonden verwijzingen:", new_articles_ref)
                display_new_article_text(new_articles_ref, new_law_text)
                
                # Display current law text
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
