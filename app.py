import streamlit as st
import pandas as pd
from fpdf import FPDF

# 1. Configuration de base
st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

# 2. Fonction PDF (Format de sortie corrigé pour Streamlit)
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        # Titre
        pdf.set_font("Helvetica", 'B', 18)
        pdf.cell(0, 10, f"Fiche Animal : {row['Nom']}", ln=True, align='C')
        pdf.ln(10)
        # Détails
        pdf.set_font("Helvetica", '', 12)
        pdf.cell(0, 10, f"Espece : {row.get('Espèce', 'Non précisé')}", ln=True)
        pdf.cell(0, 10, f"Sexe : {row.get('Sexe', 'Non précisé')}", ln=True)
        pdf.cell(0, 10, f"Age : {row.get('Âge', '?')} ans", ln=True)
        # Sortie en format bytes
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            return pdf_output.encode('latin-1')
        return bytes(pdf_output)
    except Exception as e:
        return None

# 3. Style CSS (pour le badge SOS et l'interface)
st.markdown("""
    <style>
    .stApp { background-color: #111; color: white; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1e1e1e !important; border: 1px solid #333 !important;
        border-radius: 15px !important; padding: 20px !important;
    }
    .senior-tag {
        background-color: #3e3d23; color: #d4af37; padding: 12px;
        border-radius: 8px; font-weight: bold; text-align: center;
        margin-top: 10px; border: 1px solid #555;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. Chargement et Affichage
try:
    url = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(url)

    st.title("🐾 Refuge Médéric")

    for _, row in df.iterrows():
        if str(row['Statut']) != "Adopté":
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.5])
                
                with col1:
                    st.image(str(row['Photo']), use_container_width=True)
                    # Badge SOS Senior sous la photo
                    try:
                        age_val = float(str(row['Âge']).replace(',', '.'))
                        if age_val >= 10:
                            st.markdown('<div class="senior-tag">🎁 SOS Senior : Don Libre</div>', unsafe_allow_html=True)
                    except:
                        pass

                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']}")
                    
                    # Bouton d'appel (Style vert)
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#2e7d32; color:white; padding:10px; border-radius:8px; text-align:center; font-weight:bold;">📞 Appeler le refuge</div></a>', unsafe_allow_html=True)
                    
                    st.write("") # Espace
                    
                    # Bouton PDF corrigé
                    pdf_data = generer_pdf(row)
                    if pdf_data:
                        st.download_button(
                            label="📄 Télécharger la fiche PDF",
                            data=pdf_data,
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

except Exception as e:
    st.error(f"Oups, une erreur : {e}")
