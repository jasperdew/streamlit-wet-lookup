import streamlit as st
import pandas as pd

# Functie om de data in te laden
@st.cache
def load_data(file_path):
    return pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')

# Data laden
data_path = "data.csv"  # Naam van je CSV-bestand
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
    # Key samenstellen met standaardwaarden voor optionele velden
    key = f"{artikel}-{lit if lit else '0'}-{sub if sub else '0'}-{graad if graad else '0'}"
    
    if st.button("Zoek"):
        # Zoek de resultaten
        resultaten = data[data['Key'] == key]
        if not resultaten.empty:
            st.write("Resultaten:")
            st.table(resultaten['Nieuw Wetboek van Strafvordering'])
        else:
            st.warning("Geen resultaten gevonden voor deze key.")
else:
    st.error("Vul het artikelnummer in. Dit veld is verplicht.")
