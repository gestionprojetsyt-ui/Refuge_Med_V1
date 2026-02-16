import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# 1. Config
st.set_page_config(page_title="Refuge Médéric", layout="centered")

# 2. Fonction PDF simplifiée au maximum
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 10, f"Fiche : {row['Nom']}", ln=True, align='C')
        
        # Tentative Photo
        try:
            resp = requests.get(str(row['Photo']), timeout=5)
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            img_buf = BytesIO()
            img.save(img_buf, format="JPEG")
            img_buf.seek(0)
            pdf.image(img_buf, x=60, y=30, w=90)
            pdf.ln(100)
        except:
            pdf.ln(20)

        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Espece : {row['Espèce']}", ln=True)
        pdf.cell(0, 10, f"Sexe : {row['Sexe']} | Age : {row['Âge']} ans", ln=True)
        
        # Sortie formatée pour Streamlit
        return bytes(pdf.output())
    except:
        return None

# 3. Affichage
try:
    url = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(url)
    
    st.title("🐾 Refuge Médéric")

    for _, row in df.iterrows():
        if str(row['Statut']) != "Adopté":
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.5])
                with col1:
                    st.image(str(row['Photo']))
                with col2:
                    st.subheader(row['Nom'])
                    
                    # Bouton PDF
                    pdf_data = generer_pdf(row)
                    if pdf_data:
                        st.download_button(
                            label=f"📄 Fiche PDF de {row['Nom']}",
                            data=pdf_data,
                            file_name=f"{row['Nom']}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{row['Nom']}"
                        )
                    
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#238636; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler</div></a>', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erreur : {e}")
