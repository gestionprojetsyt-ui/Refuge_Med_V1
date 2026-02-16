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

# 2. Fonction PDF simplifiée et sécurisée
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Titre
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"Fiche : {row['Nom']}", ln=True, align='C')
        pdf.ln(5)

        # TENTATIVE PHOTO
        try:
            # On récupère l'image
            resp = requests.get(str(row['Photo']), timeout=5)
            img = Image.open(BytesIO(resp.content))
            
            # Conversion forcée pour éviter les bugs de transparence
            img = img.convert('RGB')
            
            # On prépare l'image pour le PDF
            img_buf = BytesIO()
            img.save(img_buf, format="JPEG")
            img_buf.seek(0)
            
            # Placement au centre
            pdf.image(img_buf, x=60, y=35, w=90)
            pdf.ln(100)
        except Exception as e:
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(0, 10, f"(Photo non disponible)", ln=True, align='C')
            pdf.ln(10)

        # Infos de l'animal
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  COMPATIBILITES :", ln=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - Chats : {traduire(row.get('OK_Chat'))} | Chiens : {traduire(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - Enfants : {traduire(row.get('OK_Enfant'))}", ln=True)
        
        # Sortie finale en format "bytes" (important pour Streamlit !)
        return pdf.output()
    except Exception as e:
        return None

# 3. Design de l'application (Sombre)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b22 !important; border: 1px solid #30363d !important;
        border-radius: 12px !important; padding: 20px !important; margin-bottom: 20px !important;
    }
    .senior-badge {
        background-color: #1b1b1b; color: #ff4b4b; padding: 10px;
        border-radius: 8px; font-weight: bold; text-align: center;
        border: 1px solid #ff4b4b; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. Affichage du catalogue
try:
    # Récupération GSheets
    url_csv = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(url_csv)
    
    st.title("🐾 Refuge Médéric")

    for _, row in df.iterrows():
        if str(row['Statut']) != "Adopté":
            with st.container(border=True):
                c1, c2 = st.columns([1, 1.5])
                
                with c1:
                    st.image(str(row['Photo']), use_container_width=True)
                    # SOS Senior
                    try:
                        if float(str(row['Âge']).replace(',', '.')) >= 10:
                            st.markdown('<div class="senior-badge">🎁 SOS Senior : Don Libre</div>', unsafe_allow_html=True)
                    except: pass
                
                with c2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | {row['Âge']} ans")
                    
                    # Bouton PDF
                    pdf_data = generer_pdf(row)
                    if pdf_data:
                        st.download_button(
                            label=f"📄 PDF de {row['Nom']}",
                            data=pdf_data, # Ici le format est maintenant correct
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            key=f"btn_{row['Nom']}",
                            use_container_width=True
                        )
                    
                    # Appel
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#238636; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler le refuge</div></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur technique : {e}")
