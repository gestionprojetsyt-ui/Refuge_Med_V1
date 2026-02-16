import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# --- 1. CONFIGURATION DE LA PAGE ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E"

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except:
        return None
    return None

logo_b64 = get_base64_image(URL_LOGO_HD)

st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon=f"data:image/png;base64,{logo_b64}" if logo_b64 else "🐾"
)

# --- 2. FONCTION PDF AVEC OPACITÉ 5% ---
def traduire_bool(valeur):
    return "OUI" if str(valeur).upper() == "TRUE" else "NON"

def generer_pdf(row):
    try:
        class PDF(FPDF):
            def header(self):
                # Ajout du logo en filigrane avec opacité de 5%
                try:
                    # GState permet de gérer la transparence dans le PDF
                    with self.local_context(fill_opacity=0.05): 
                        self.image(URL_LOGO_HD, x=45, y=80, w=120)
                except:
                    pass

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", 'I', 8)
                self.set_text_color(128)
                self.cell(0, 10, "Refuge Médéric - 182 chemin Lucien Viau, 40990 St-Paul-lès-Dax - 05 58 73 68 82", 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        
        # --- MISE EN PAGE DU PDF ---
        pdf.set_font("Helvetica", 'B', 24)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 20, f"RENCONTREZ {row['Nom'].upper()}", ln=True, align='C')
        
        pdf.set_draw_color(220, 0, 0)
        pdf.line(20, 32, 190, 32)
        pdf.ln(10)

        # Photo de l'animal
        try:
            u_photo = format_image_url(row['Photo'])
            resp = requests.get(u_photo, timeout=5)
            pdf.image(BytesIO(resp.content), x=55, y=40, w=100)
            pdf.ln(110)
        except:
            pdf.ln(10)

        # Infos principales
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} - {row['Sexe']} - {row['Âge']} ans", ln=True, align='C')
        pdf.ln(5)

        # Bloc Aptitudes
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "  MES COMPATIBILITÉS :", ln=True, fill=True)
        
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(60, 8, f"   - OK Chats : {traduire_bool(row.get('OK_Chat'))}", ln=0)
        pdf.cell(60, 8, f"   - OK Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=0)
        pdf.cell(60, 8, f"   - OK Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=1)
        pdf.ln(5)

        # Histoire & Caractère
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 8, "MON HISTOIRE ET MON CARACTÈRE :", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.set_text_color(0, 0, 0)
        description = f"{row.get('Histoire', '')}\n\n{row.get('Description', '')}"
        clean_text = str(description).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_text)

        return bytes(pdf.output())
    except Exception as e:
        print(f"Erreur PDF : {e}")
        return None

# --- 3. RESTE DU CODE (SANS CHANGEMENT) ---
# ... (Tes fonctions afficher_evenement, load_all_data, et l'interface principale restent identiques)
# Copie ici la suite de ton code habituel pour le catalogue et le style CSS.
