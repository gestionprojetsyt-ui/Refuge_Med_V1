import streamlit as st
import pandas as pd
from fpdf import FPDF

# Configuration simple
st.set_page_config(page_title="Refuge Mederic", layout="centered")

# Fonction PDF
def make_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 10, f"Fiche : {row['Nom']}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Espece : {row['Espèce']}", ln=True)
        return pdf.output(dest='S')
    except: return None

# Chargement
try:
    url = st.secrets["gsheets"]["public_url"].replace('/edit?usp=sharing', '/export?format=csv')
    df = pd.read_csv(url)
    
    st.title("🐾 Refuge Médéric")
    
    for _, row in df.iterrows():
        if str(row['Statut']) != "Adopté":
            with st.container(border=True):
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    st.image(str(row['Photo']))
                    # Badge Senior
                    try:
                        age = float(str(row['Âge']).replace(',', '.'))
                        if age >= 10:
                            st.warning("🎁 SOS Senior : Don Libre")
                    except: pass
                
                with c2:
                    st.subheader(row['Nom'])
                    st.write(f"{row['Espèce']} | {row['Sexe']}")
                    
                    # Bouton PDF
                    pdf_out = make_pdf(row)
                    if pdf_out:
                        st.download_button("📄 PDF", data=pdf_out, file_name=f"{row['Nom']}.pdf", mime="application/pdf")
except Exception as e:
    st.error(f"Erreur : {e}")
