import streamlit as st
import pandas as pd

# Configuration pour mobile
st.set_page_config(page_title="Refuge_Med_V1", layout="centered")

# Lien vers ton Google Sheets (le lien .csv copié à l'étape 2)
URL_DONNEES = "https://docs.google.com/spreadsheets/d/1XZXKwCfJ_922HAkAANzpXyyZL97uJzcu84viFWdtgpA/edit?usp=sharing"

# Chargement des données
@st.cache_data
def load_data():
    return pd.read_csv(URL_DONNEES)

df = load_data()

st.title("🐾 Nos animaux à l'adoption")
st.write("Scannez le code pour nous découvrir !")

# Filtres simples
choix = st.segmented_control("Filtrer par :", ["Tous", "Chien", "Chat"], default="Tous")

# Filtrage
if choix != "Tous":
    df_filtre = df[df['Espèce'] == choix]
else:
    df_filtre = df

# Affichage des fiches
for index, row in df_filtre.iterrows():
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(row['Photo'], use_container_width=True)
        with col2:
            st.subheader(row['Nom'])
            st.write(f"**Âge :** {row['Âge']} | **Sexe :** {row['Sexe']}")
            
            # Bouton pour voir les détails
            with st.expander("En savoir plus"):
                st.write(row['Description'])
