import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# 1. Configuration
st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

def traduire_bool(valeur):
    return "OUI" if str(valeur).upper() == "TRUE" else "NON"

# 2. Fonction PDF avec IMAGE
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # TITRE
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"{row['Nom']}", ln=True, align='C')
        pdf.ln(5)

        # INSERTION DE LA PHOTO
        try:
            response = requests.get(str(row['Photo']), timeout=5)
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            # On force la conversion en RGB pour éviter les erreurs de format
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # On sauvegarde temporairement dans un buffer
            tmp_img = BytesIO()
            img.save(tmp_img, format="JPEG")
            tmp_img.seek(0)
            
            # On place l'image au centre (x=55, largeur=100mm)
            pdf.image(tmp_img, x=55, y=30, w=100)
            pdf.ln(105) # On saute l'espace de la photo
        except:
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(0, 10, "(Photo non disponible sur la fiche)", ln=True, align='C')
            pdf.ln(10)

        # INFOS
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Espece : {row.get('Espèce', 'Non précisé')} | Sexe : {row.get('Sexe', 'Non précisé')} | Age : {row.get('Âge', '?')} ans", ln=True, align='C')
        
        # APTITUDES
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  APTITUDES :", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - Entente Chats : {traduire_bool(row.get('OK_Chat'))}", ln=True)
        pdf.cell(0, 8, f"   - Entente Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - Entente Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=True)
        
        # HISTOIRE
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, " SON HISTOIRE :", ln=True)
        pdf.set_font("Helvetica", '', 10)
        histoire = str(row.get('Histoire', 'Fiche en cours de rédaction.')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, histoire)
        
        return bytes(pdf.output(dest='S'))
    except Exception as e:
        return None

# 3. Affichage Appli
try:
    url_csv = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(url_csv)

    st.title("🐾 Refuge Médéric")

    for _, row in df.iterrows():
        if str(row['Statut']) != "Adopté":
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.5])
                with col1:
                    st.image(str(row['Photo']), use_container_width=True)
                    # SOS Senior
                    try:
                        if float(str(row['Âge']).replace(',', '.')) >= 10:
                            st.error("🎁 SOS Senior : Don Libre")
                    except: pass
                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | {row['Âge']} ans")
                    
                    # Bouton PDF
                    pdf_data = generer_pdf(row)
                    if pdf_data:
                        st.download_button(label="📄 Télécharger la fiche PDF (avec photo)", data=pdf_data, file_name=f"Fiche_{row['Nom']}.pdf", mime="application/pdf", use_container_width=True)
                    
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#2e7d32; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler le refuge</div></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
