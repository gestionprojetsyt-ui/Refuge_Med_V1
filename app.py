import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF
from io import BytesIO

# --- 1. CONFIGURATION ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E"

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except: return None
    return None

logo_b64 = get_base64_image(URL_LOGO_HD)

st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon=f"data:image/png;base64,{logo_b64}" if logo_b64 else "🐾"
)

# --- 2. FONCTION PDF ---
def generer_pdf(row):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 15, f"Fiche d'adoption : {row['Nom']}", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Espece : {row['Espèce']} | Sexe : {row['Sexe']} | Age : {row['Âge']} ans", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "APTITUDES :", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, f"- Ok Chats : {'OUI' if str(row.get('OK_Chat')).upper() == 'TRUE' else 'NON'}", ln=True)
        pdf.cell(0, 8, f"- Ok Chiens : {'OUI' if str(row.get('OK_Chien')).upper() == 'TRUE' else 'NON'}", ln=True)
        pdf.cell(0, 8, f"- Ok Enfants : {'OUI' if str(row.get('OK_Enfant')).upper() == 'TRUE' else 'NON'}", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "HISTOIRE :", ln=True)
        pdf.set_font("Arial", '', 10)
        histoire = str(row['Histoire']).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, histoire)
        return pdf.output(dest='S')
    except: return None

# --- 3. STYLE VISUEL CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: transparent !important; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important; border-radius: 15px !important;
        border: 1px solid #ddd !important; box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
        padding: 20px !important; margin-bottom: 20px !important;
    }}
    .senior-tag {{
        background-color: #fce4ec; color: #c2185b; padding: 10px; border-radius: 8px;
        font-weight: bold; font-size: 0.95em; border: 2px dashed #f06292;
        display: block; text-align: center; margin-top: 10px;
    }}
    .aptitude-box {{
        background-color: #f8f9fa; padding: 12px; border-radius: 8px; 
        border-left: 5px solid #FF0000; margin: 15px 0; border: 1px solid #eee;
    }}
    .btn-contact {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT DATA ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        def cat_age(a):
            try:
                a = float(str(a).replace(',', '.'))
                return "Senior" if a >= 10 else "Autre"
            except: return "Autre"
        df['Tranche_Age'] = df['Âge'].apply(cat_age)
        return df
    except: return pd.DataFrame()

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_data(URL_SHEET)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        df_dispo = df[df['Statut'] != "Adopté"]

        for _, row in df_dispo.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    st.image(str(row['Photo']), use_container_width=True)
                    if row['Tranche_Age'] == "Senior":
                        st.markdown('<div class="senior-tag">🎁 SOS Senior : Don Libre</div>', unsafe_allow_html=True)
                
                with col_txt:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    # Aptitudes avec émojis
                    def check_ok(v): return "✅" if str(v).upper() == "TRUE" else "❌"
                    apt_html = f'''<div class="aptitude-box"><b style="color:#FF0000;">🏠 APTITUDES :</b><br>
                    🐈 Chats : {check_ok(row.get('OK_Chat'))}<br>
                    🐕 Chiens : {check_ok(row.get('OK_Chien'))}<br>
                    🧒 Enfants : {check_ok(row.get('OK_Enfant'))}</div>'''
                    st.markdown(apt_html, unsafe_allow_html=True)

                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                    
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

    st.markdown('<div style="text-align:center; padding:20px; border-top:1px solid #ddd; color:grey;">Version Alpha_1.9 - SOS Senior & PDF</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur technique : {e}")
