import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# Configuration
st.set_page_config(page_title="Refuge Médéric", layout="centered")

# Fonction PDF simplifiée
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Fiche de {row['Nom']}", ln=True, align='C')
        
        # Ajout Photo
        try:
            resp = requests.get(str(row['Photo']), timeout=5)
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            buf = BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            pdf.image(buf, x=60, y=30, w=90)
        except: pass
        
        return pdf.output()
    except: return None

# Affichage
try:
    # On récupère le lien depuis les secrets
    url = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(url)
    
    st.title("🐾 Refuge Médéric")
    
    for _, row in df.iterrows():
        if str(row['Statut']) != "Adopté":
            with st.container(border=True):
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    st.image(str(row['Photo']), use_container_width=True)
                with c2:
                    st.subheader(row['Nom'])
                    st.write(f"{row['Espèce']} | {row['Sexe']}")
                    
                    pdf_data = generer_pdf(row)
                    if pdf_data:
                        st.download_button(f"📄 PDF {row['Nom']}", pdf_data, f"{row['Nom']}.pdf", "application/pdf")
                    
                    st.markdown(f'[📞 Appeler](tel:0558736882)', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erreur de chargement : {e}")
