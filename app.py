import streamlit as st
import pandas as pd
from fpdf import FPDF

# 1. Configuration de base
st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

# --- FONCTION DE TRADUCTION ---
def traduire_bool(valeur):
    if str(valeur).upper() == "TRUE":
        return "OUI"
    return "NON"

# 2. Fonction PDF avec Traduction
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # En-tête
        pdf.set_font("Helvetica", 'B', 20)
        pdf.set_text_color(220, 0, 0) # Rouge Médéric
        pdf.cell(0, 15, f"FICHE D'ADOPTION : {row['Nom']}", ln=True, align='C')
        
        pdf.ln(10)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Espece : {row.get('Espèce', 'Non précisé')}", ln=True)
        pdf.cell(0, 10, f"Sexe : {row.get('Sexe', 'Non précisé')}", ln=True)
        pdf.cell(0, 10, f"Age : {row.get('Âge', '?')} ans", ln=True)
        
        # Bloc Aptitudes (TRADUIT EN FRANCAIS)
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  APTITUDES :", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 11)
        
        # Utilisation de la fonction traduire_bool
        pdf.cell(0, 8, f"   - Entente Chats : {traduire_bool(row.get('OK_Chat'))}", ln=True)
        pdf.cell(0, 8, f"   - Entente Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - Entente Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=True)
        
        # Description
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, " SON HISTOIRE :", ln=True)
        pdf.set_font("Helvetica", '', 10)
        histoire = str(row.get('Histoire', 'Fiche en cours de rédaction.')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, histoire)
        
        # Pied de page
        pdf.set_y(-20)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.cell(0, 10, "Refuge Médéric - Association Animaux du Grand Dax", 0, 0, 'C')
        
        pdf_output = pdf.output(dest='S')
        return bytes(pdf_output) if isinstance(pdf_output, (bytes, bytearray)) else pdf_output.encode('latin-1')
    except:
        return None

# 3. Style Sombre
st.markdown("""
    <style>
    .stApp { background-color: #111; color: white; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1e1e1e !important; border: 1px solid #333 !important;
        border-radius: 15px !important; padding: 20px !important; margin-bottom: 20px !important;
    }
    .senior-tag {
        background-color: #4a154b; color: #ffccff; padding: 10px;
        border-radius: 8px; font-weight: bold; text-align: center;
        margin-top: 10px; border: 1px dashed #ffccff;
    }
    .aptitude-box {
        background-color: #262626; padding: 12px; border-radius: 8px;
        border-left: 5px solid #FF0000; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. Chargement et Affichage
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
                    try:
                        if float(str(row['Âge']).replace(',', '.')) >= 10:
                            st.markdown('<div class="senior-tag">🎁 SOS Senior : Don Libre</div>', unsafe_allow_html=True)
                    except: pass

                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | {row['Âge']} ans")
                    
                    # Aptitudes visuelles sur l'appli
                    def check_emoji(v): return "✅ OUI" if str(v).upper() == "TRUE" else "❌ NON"
                    st.markdown(f"""<div class="aptitude-box">
                        🐈 Chats : {check_emoji(row.get('OK_Chat'))}<br>
                        🐕 Chiens : {check_emoji(row.get('OK_Chien'))}<br>
                        🧒 Enfants : {check_emoji(row.get('OK_Enfant'))}
                    </div>""", unsafe_allow_html=True)
                    
                    # Bouton PDF
                    pdf_data = generer_pdf(row)
                    if pdf_data:
                        st.download_button(
                            label="📄 Télécharger la fiche PDF",
                            data=pdf_data,
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none;"><div style="background-color:#2e7d32; color:white; padding:12px; border-radius:8px; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler le refuge</div></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
