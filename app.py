import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# 1. Configuration initiale
st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

def traduire(v):
    return "OUI" if str(v).upper() == "TRUE" else "NON"

# 2. Fonction PDF avec gestion de l'image
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Titre
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"Fiche d'adoption : {row['Nom']}", ln=True, align='C')
        pdf.ln(5)

        # IMAGE
        try:
            resp = requests.get(str(row['Photo']), timeout=5)
            img = Image.open(BytesIO(resp.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            buf = BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            
            pdf.image(buf, x=60, y=35, w=90)
            pdf.ln(100)
        except:
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(0, 10, "(Image non disponible)", ln=True, align='C')
            pdf.ln(10)

        # Infos & Aptitudes
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  COMPATIBILITÉS :", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - Chats : {traduire(row.get('OK_Chat'))} | Chiens : {traduire(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - Enfants : {traduire(row.get('OK_Enfant'))}", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, " SON HISTOIRE :", ln=True)
        pdf.set_font("Helvetica", '', 10)
        hist = str(row.get('Histoire', 'Non renseignée')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, hist)

        # Conversion finale sécurisée
        return bytes(pdf.output())
    except Exception as e:
        st.error(f"Erreur PDF : {e}")
        return None

# 3. Interface Médéric
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b22 !important; border: 1px solid #30363d !important;
        border-radius: 12px !important; padding: 20px !important;
    }
    .senior-tag {
        background-color: #1b1b1b; color: #ff4b4b; padding: 10px;
        border-radius: 8px; font-weight: bold; text-align: center;
        border: 1px solid #ff4b4b; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    url_csv = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(url_csv)
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
                    
                    # Bouton PDF
                    pdf_out = generer_pdf(row)
                    if pdf_out:
                        st.download_button(
                            label=f"📄 Télécharger la fiche de {row['Nom']}",
                            data=pdf_out,
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#238636; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler le refuge</div></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
