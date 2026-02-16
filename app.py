import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# 1. Configuration de la page
st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

# --- FONCTION TRADUCTION ---
def traduire(v):
    return "OUI" if str(v).upper() == "TRUE" else "NON"

# 2. Fonction PDF avec Photo
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Titre
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"Fiche d'adoption : {row['Nom']}", ln=True, align='C')
        pdf.ln(5)

        # TENTATIVE D'INSERTION DE LA PHOTO
        try:
            response = requests.get(str(row['Photo']), timeout=5)
            img = Image.open(BytesIO(response.content))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # On sauve l'image en mémoire pour le PDF
            img_buffer = BytesIO()
            img.save(img_buffer, format="JPEG")
            img_buffer.seek(0)
            
            # Positionnement de la photo au centre
            pdf.image(img_buffer, x=60, y=35, w=90)
            pdf.ln(100) # On laisse la place pour l'image
        except:
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(0, 10, "(Image non disponible sur ce document)", ln=True, align='C')
            pdf.ln(10)

        # Informations
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        
        # Aptitudes (Traduites)
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  COMPATIBILITÉS :", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - Avec les chats : {traduire(row.get('OK_Chat'))}", ln=True)
        pdf.cell(0, 8, f"   - Avec les chiens : {traduire(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - Avec les enfants : {traduire(row.get('OK_Enfant'))}", ln=True)
        
        # Histoire
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, " SON HISTOIRE :", ln=True)
        pdf.set_font("Helvetica", '', 10)
        histoire = str(row.get('Histoire', 'En attente de description.')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, histoire)

        # On retourne le fichier prêt à télécharger
        return bytes(pdf.output())
    except:
        return None

# 3. Style Sombre Médéric
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b22 !important; border: 1px solid #30363d !important;
        border-radius: 12px !important; padding: 20px !important; margin-bottom: 20px !important;
    }
    .senior-tag {
        background-color: #21262d; color: #f85149; padding: 10px;
        border-radius: 6px; font-weight: bold; text-align: center;
        margin-top: 10px; border: 1px solid #f85149;
    }
    .apt-box {
        background-color: #0d1117; padding: 10px; border-radius: 8px;
        border-left: 4px solid #f85149; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. Affichage
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
                    
                    # Aptitudes traduites sur l'appli
                    st.markdown(f"""<div class="apt-box">
                        🐈 Chats : {traduire(row.get('OK_Chat'))}<br>
                        🐕 Chiens : {traduire(row.get('OK_Chien'))}<br>
                        🧒 Enfants : {traduire(row.get('OK_Enfant'))}
                    </div>""", unsafe_allow_html=True)
                    
                    # Bouton PDF
                    pdf_bytes = generer_pdf(row)
                    if pdf_bytes:
                        st.download_button(
                            label="📄 Télécharger la fiche PDF",
                            data=pdf_bytes,
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#238636; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler le refuge</div></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur de chargement : {e}")
