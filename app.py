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

# --- 2. FONCTION PDF SÉCURISÉE ---
def traduire_bool(valeur):
    return "OUI" if str(valeur).upper() == "TRUE" else "NON"

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            return f"https://drive.google.com/uc?export=view&id={doc_id}"
    return url

def generer_pdf(row):
    try:
        class PDF(FPDF):
            def header(self):
                try:
                    with self.local_context(fill_opacity=0.05):
                        self.image(URL_LOGO_HD, x=45, y=80, w=120)
                except: pass

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", 'I', 8)
                self.set_text_color(128)
                footer_txt = "Refuge Médéric - 182 chemin Lucien Viau, 40990 St-Paul-lès-Dax | 05 58 73 68 82\nSite web : https://refugedax40.wordpress.com/"
                self.multi_cell(0, 4, footer_txt, align='C')

        pdf = PDF()
        pdf.add_page()
        
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"FICHE D'ADOPTION : {str(row['Nom']).upper()}", ln=True, align='C')
        pdf.ln(5)

        is_senior = False
        try:
            age_val = float(str(row['Âge']).replace(',', '.'))
            if age_val >= 10: is_senior = True
        except: pass

        # --- BLOC PHOTO AVEC SÉCURITÉ ---
        try:
            u_photo = format_image_url(row['Photo'])
            if u_photo.startswith('http'):
                resp = requests.get(u_photo, timeout=5)
                img = Image.open(BytesIO(resp.content)).convert('RGB')
                img_buf = BytesIO()
                img.save(img_buf, format="JPEG")
                img_buf.seek(0)
                
                x_img, y_img, w_img = 60, 35, 90
                pdf.image(img_buf, x=x_img, y=y_img, w=w_img)
                
                if is_senior:
                    pdf.set_fill_color(255, 215, 0) 
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.rect(x_img, y_img, 28, 8, 'F')
                    pdf.set_xy(x_img, y_img + 1.5)
                    pdf.cell(28, 5, "SOS SENIOR", 0, 0, 'C')
                
                pdf.ln(100)
            else: pdf.ln(10)
        except Exception:
            # Si l'image échoue, on ne bloque pas le PDF
            pdf.set_font("Helvetica", 'I', 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 10, "(Photo non disponible)", ln=True, align='C')
            pdf.ln(10)

        if is_senior:
            pdf.set_fill_color(255, 249, 196)
            pdf.set_text_color(133, 100, 4)
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 12, "✨ SOS SENIOR : Don Libre ✨", ln=True, align='C', fill=True)
            pdf.ln(5)

        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        
        race_val = str(row.get('Race', 'Race non précisée'))
        pdf.set_font("Helvetica", 'I', 11)
        pdf.cell(0, 6, f"Type / Race : {race_val}", ln=True, align='C')
        pdf.ln(10)

        y_start = pdf.get_y()
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(90, 10, "  SON CARACTÈRE :", ln=0, fill=True)
        pdf.set_x(110)
        pdf.cell(90, 10, "  APTITUDES :", ln=1, fill=True)

        pdf.set_y(y_start + 12)
        pdf.set_font("Helvetica", '', 10)
        caractere = str(row.get('Description', 'À venir')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(90, 5, caractere, align='L')
        
        pdf.set_y(y_start + 12)
        pdf.set_x(110)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(90, 7, f"- OK Chats : {traduire_bool(row.get('OK_Chat'))}", ln=1)
        pdf.set_x(110)
        pdf.cell(90, 7, f"- OK Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=1)
        pdf.set_x(110)
        pdf.cell(90, 7, f"- OK Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=1)

        pdf.set_y(pdf.get_y() + 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  SON HISTOIRE :", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_font("Helvetica", '', 10)
        histoire = str(row.get('Histoire', 'À venir')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, histoire)
        
        return bytes(pdf.output())
    except: return None

# --- [LE RESTE DE TON CODE RESTE IDENTIQUE ICI] ---
# ... (Interface, Style CSS, Chargement Data) ...
