import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF # <--- Nouvelle bibliothèque à ajouter dans requirements.txt
from io import BytesIO

# --- 1. CONFIGURATION & LOGO ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E"

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except: return None
    return None

logo_b64 = get_base64_image(URL_LOGO_HD)

st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

# --- FONCTION GÉNÉRATION PDF ---
def generer_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    
    # Titre
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(255, 0, 0) # Rouge Médéric
    pdf.cell(0, 20, f"Fiche d'adoption : {row['Nom']}", ln=True, align='C')
    
    # Infos de base
    pdf.set_font("Arial", '', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(0, 10, f"Espece : {row['Espèce']} | Sexe : {row['Sexe']} | Age : {row['Âge']} ans", ln=True, align='C')
    
    # Aptitudes
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "  APTITUDES :", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    
    ok_chat = "OUI" if str(row.get('OK_Chat')).upper() == "TRUE" else "NON"
    ok_chien = "OUI" if str(row.get('OK_Chien')).upper() == "TRUE" else "NON"
    ok_enfant = "OUI" if str(row.get('OK_Enfant')).upper() == "TRUE" else "NON"
    
    pdf.cell(0, 8, f"   - Entente Chats : {ok_chat}", ln=True)
    pdf.cell(0, 8, f"   - Entente Chiens : {ok_chien}", ln=True)
    pdf.cell(0, 8, f"   - Entente Enfants : {ok_enfant}", ln=True)
    
    # Histoire
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, " SON HISTOIRE :", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, str(row['Histoire']))

    # Pied de page
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Refuge Mederic - Association Animaux du Grand Dax - 05 58 73 68 82", 0, 0, 'C')
    
    return pdf.output()

# --- (Le reste du code reste identique à la version précédente) ---
# ... (Style CSS, Chargement Data, Interface) ...

# --- DANS LA BOUCLE D'AFFICHAGE DES ANIMAUX ---
# (Cherche l'endroit où il y a les boutons de contact et ajoute ceci :)

                with col_txt:
                    # ... (tes autres boutons : Appeler, Mail) ...
                    
                    # Bouton PDF
                    pdf_data = generer_pdf(row)
                    st.download_button(
                        label="📄 Télécharger la fiche PDF",
                        data=pdf_data,
                        file_name=f"Fiche_{row['Nom']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

# --- MISE À JOUR VERSION ---
# Version Alpha_1.9 - Ajout Export PDF
