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

# --- 2. FONCTION PDF (AVEC DON LIBRE) ---
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
        
        # Photo
        try:
            u_photo = format_image_url(row['Photo'])
            resp = requests.get(u_photo, timeout=5)
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            img_buf = BytesIO()
            img.save(img_buf, format="JPEG")
            img_buf.seek(0)
            pdf.image(img_buf, x=60, y=30, w=90)
            pdf.ln(95)
        except:
            pdf.ln(10)

        # MENTION DON LIBRE POUR LES SENIORS (>= 10 ans)
        age_val = 0
        try: age_val = float(str(row['Âge']).replace(',', '.'))
        except: pass

        if age_val >= 10:
            pdf.set_fill_color(255, 249, 196)
            pdf.set_text_color(133, 100, 4)
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 12, "✨ SOS SENIOR : Don Libre ✨", ln=True, align='C', fill=True)
            pdf.ln(5)

        # Infos
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 8, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        pdf.ln(5)
        
        # Aptitudes & Description
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "CARACTÈRE & HISTOIRE :", ln=True)
        pdf.set_font("Helvetica", '', 11)
        txt = f"{row.get('Description', '')}\n\n{row.get('Histoire', '')}"
        pdf.multi_cell(0, 6, txt.encode('latin-1', 'replace').decode('latin-1'))

        return bytes(pdf.output())
    except Exception as e:
        return None

# --- 3. STYLE CSS ---
st.markdown(f"""
    <style>
    .senior-badge {{
        background-color: #FFF9C4; color: #856404; padding: 10px; 
        border-radius: 10px; font-weight: bold; text-align: center; margin: 10px 0;
    }}
    .btn-contact {{
        text-decoration: none; color: white !important; background-color: #2e7d32; 
        padding: 10px; border-radius: 5px; display: block; text-align: center; margin-top: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT DATA ---
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
                    # Affichage Don Libre si Senior
                    try:
                        a = float(str(row['Âge']).replace(',', '.'))
                        if a >= 10:
                            st.markdown('<div class="senior-badge">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)
                    except: pass

                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    t1, t2 = st.tabs(["Histoire", "Caractère"])
                    with t1: st.write(row['Histoire'])
                    with t2: st.write(row['Description'])

                    # --- BOUTON PDF SÉCURISÉ ---
                    pdf_content = generer_pdf(row)
                    if pdf_content:
                        st.download_button(
                            label=f"📄 Télécharger la fiche de {row['Nom']}",
                            data=pdf_content,
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            key=f"dl_{i}",
                            use_container_width=True
                        )
                    
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur technique : {e}")
