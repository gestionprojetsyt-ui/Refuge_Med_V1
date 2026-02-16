import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# --- 1. CONFIGURATION ---
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
st.set_page_config(page_title="Refuge Médéric", layout="centered")

# --- 2. FONCTION PDF AVEC BADGE SUR LA PHOTO ---
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
        pdf = FPDF()
        pdf.add_page()
        
        # En-tête
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"FICHE D'ADOPTION : {str(row['Nom']).upper()}", ln=True, align='C')
        
        # Gestion de l'âge
        age_val = 0
        try: age_val = float(str(row['Âge']).replace(',', '.'))
        except: pass

        # Photo avec Badge
        y_photo = 35
        x_photo = 60
        w_photo = 90
        
        photo_a_reussi = False
        try:
            u_photo = format_image_url(row['Photo'])
            if u_photo.startswith('http'):
                resp = requests.get(u_photo, timeout=5)
                img = Image.open(BytesIO(resp.content)).convert('RGB')
                img_buf = BytesIO()
                img.save(img_buf, format="JPEG")
                img_buf.seek(0)
                pdf.image(img_buf, x=x_photo, y=y_photo, w=w_photo)
                
                # RAJOUT DU BADGE DANS LE COIN DE LA PHOTO
                if age_val >= 10:
                    pdf.set_fill_color(255, 215, 0) # Or
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", 'B', 10)
                    # Petit rectangle en haut à gauche de la photo
                    pdf.rect(x_photo, y_photo, 25, 8, 'F')
                    pdf.set_xy(x_photo, y_photo + 1.5)
                    pdf.cell(25, 5, "SOS SENIOR", 0, 0, 'C')
                
                photo_a_reussi = True
        except: pass

        pdf.ln(100 if photo_a_reussi else 15)

        # Mention Don Libre sous la photo
        if age_val >= 10:
            pdf.set_fill_color(255, 249, 196)
            pdf.set_text_color(133, 100, 4)
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 12, "✨ SOS SENIOR : Don Libre ✨", ln=True, align='C', fill=True)
            pdf.ln(5)

        # Infos & Texte
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 8, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, "PRÉSENTATION :", ln=True)
        pdf.set_font("Helvetica", '', 11)
        
        texte = f"{str(row.get('Description',''))}\n\n{str(row.get('Histoire',''))}"
        pdf.multi_cell(0, 6, texte.encode('latin-1', 'replace').decode('latin-1'))

        return bytes(pdf.output())
    except: return None

# --- 3. STYLE CSS ---
st.markdown(f"""
    <style>
    .senior-badge {{ background-color: #FFF9C4; color: #856404; padding: 10px; border-radius: 10px; font-weight: bold; text-align: center; margin: 10px 0; border: 1px solid #e6db55; }}
    .btn-contact {{ text-decoration: none; color: white !important; background-color: #2e7d32; padding: 10px; border-radius: 5px; display: block; text-align: center; margin-top: 5px; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT & AFFICHAGE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    csv_url = URL_SHEET.replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(csv_url)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"]
        for i, row in df_dispo.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    st.image(format_image_url(row['Photo']), use_container_width=True)
                    try:
                        a = float(str(row['Âge']).replace(',', '.'))
                        if a >= 10: st.markdown('<div class="senior-badge">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)
                    except: pass
                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    t1, t2 = st.tabs(["Histoire", "Caractère"])
                    with t1: st.write(row['Histoire'])
                    with t2: st.write(row['Description'])

                    pdf_content = generer_pdf(row)
                    if pdf_content:
                        st.download_button(label=f"📄 Fiche PDF de {row['Nom']}", data=pdf_content, file_name=f"Fiche_{row['Nom']}.pdf", mime="application/pdf", key=f"dl_{i}", use_container_width=True)
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erreur : {e}")
