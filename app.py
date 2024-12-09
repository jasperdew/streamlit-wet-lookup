import streamlit as st
import pandas as pd

# Functie om de data in te laden
@st.cache
def load_data(file_path):
    return pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')

# Data laden
data_path = "data.csv" 
data = load_data(data_path)

# Titel
st.title("Key Lookup Tool")

# Inputvelden
st.subheader("Zoek naar een waarde met de key")
artikel = st.text_input("Artikel (verplicht)", "")
lit = st.text_input("Lit (optioneel)", "")
sub = st.text_input("Sub (optioneel)", "")
graad = st.text_input("Graad (optioneel)", "")

# Key samenstellen
key = f"{artikel}-{lit or '0'}-{sub or '0'}-{graad or '0'}"

# Resultaten tonen
if st.button("Zoek"):
    resultaten = data[data['Key'] == key]
    if not resultaten.empty:
        st.write("Resultaten:")
        st.table(resultaten['Nieuw Wetboek van Strafvordering'])
    else:
        st.warning("Geen resultaten gevonden voor deze key.")
