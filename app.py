import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# Configuration
st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

def traduire(v):
    return "OUI" if str(v).upper() == "TRUE" else "NON"

def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"Fiche de {row['Nom']}", ln=True, align='C')
        
        # Gestion Photo dans le PDF
        try:
            resp = requests.get(str(row['Photo']), timeout=5)
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            buf = BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            pdf.image(buf, x=60, y=30, w=90)
            pdf.ln(100)
        except:
            pdf.ln(20)

        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  COMPATIBILITES :", ln=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - Chats : {traduire(row.get('OK_Chat'))} | Chiens : {traduire(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - Enfants : {traduire(row.get('OK_Enfant'))}", ln=True)
        
        # Important : bytes(pdf.output()) pour éviter l'erreur "bytearray"
        return bytes(pdf.output())
    except:
        return None

# Design
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b22 !important; border: 1px solid #30363d !important;
        border-radius: 12px !important; padding: 20px !important; margin-bottom: 20px !important;
    }
    .senior-tag {
        background-color: #21262d; color: #ff4b4b; padding: 8px;
        border-radius: 6px; font-weight: bold; text-align: center; border: 1px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

# Affichage
try:
    if "gsheets" in st.secrets:
        url = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(url)
        
        st.title("🐾 Refuge Médéric")

        for _, row in df.iterrows():
            if str(row['Statut']) != "Adopté":
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1.5])
                    with c1:
                        st.image(str(row['Photo']), use_container_width=True)
                        try:
                            if float(str(row['Âge']).replace(',', '.')) >= 10:
                                st.markdown('<div class="senior-tag">🎁 SOS Senior : Don Libre</div>', unsafe_allow_html=True)
                        except: pass
                    with c2:
                        st.subheader(row['Nom'])
                        st.write(f"**{row['Espèce']}** | {row['Sexe']} | {row['Âge']} ans")
                        
                        pdf_data = generer_pdf(row)
                        if pdf_data:
                            st.download_button(f"📄 Télécharger PDF de {row['Nom']}", pdf_data, f"{row['Nom']}.pdf", "application/pdf", key=f"pdf_{row['Nom']}", use_container_width=True)
                        
                        st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#238636; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler le refuge</div></a>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Configuration manquante : Veuillez ajouter le lien Google Sheets dans les Secrets Streamlit.")

except Exception as e:
    st.error(f"Erreur : {e}")
