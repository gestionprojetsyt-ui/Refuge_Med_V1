import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF
from io import BytesIO

# --- 1. CONFIGURATION DE LA PAGE ---
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
    pdf.multi_cell(0, 6, str(row['Histoire']))
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- 3. STYLE VISUEL CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: transparent !important; }}
    .logo-overlay {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 70vw; opacity: 0.04; z-index: -1; pointer-events: none;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important; border-radius: 15px !important;
        border: 1px solid #ddd !important; box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
        padding: 20px !important; margin-bottom: 20px !important;
    }}
    .senior-tag {{
        background-color: #fce4ec; color: #c2185b; padding: 10px;
        border-radius: 8px; font-weight: bold; font-size: 0.95em; border: 2px dashed #f06292;
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
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="logo-overlay">
    """, unsafe_allow_html=True)

# --- 4. DATA ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        base_url = url.split('/edit')[0]
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        df = pd.read_csv(csv_url, engine='c', low_memory=False)
        def categoriser_age(age):
            try:
                age = float(str(age).replace(',', '.'))
                if age < 1: return "Moins d'un an (Junior)"
                elif 1 <= age <= 5: return "1 à 5 ans (Jeune Adulte)"
                elif 5 < age < 10: return "5 à 10 ans (Adulte)"
                else: return "10 ans et plus (Senior)"
            except: return "Non précisé"
        df['Tranche_Age'] = df['Âge'].apply(categoriser_age)
        return df
    except: return pd.DataFrame()

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        
        choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        df_filtre = df_dispo if choix_espece == "Tous" else df_dispo[df_dispo['Espèce'] == choix_espece]

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    st.image(str(row['Photo']), use_container_width=True)
                    if row['Tranche_Age'] == "10 ans et plus (Senior)":
                        st.markdown('<div class="senior-tag">🎁 SOS Senior : Don Libre</div>', unsafe_allow_html=True)
                
                with col_txt:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")

                    # Bloc Aptitudes
                    def check_ok(val): return "✅" if str(val).upper() == "TRUE" else "❌"
                    apt_html = f"""<div class="aptitude-box"><b style="color:#FF0000;">🏠 APTITUDES :</b><br>
                    🐈 Ok Chats : {check_ok(row.get('OK_Chat'))}<br>
                    🐕 Ok Chiens : {check_ok(row.get('OK_Chien'))}<br>
                    🧒 Ok Enfants : {check_ok(row.get('OK_Enfant'))}</div>"""
                    st.markdown(apt_html, unsafe_allow_html=True)

                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                    
                    # Bouton PDF
                    pdf_bytes = generer_pdf(row)
                    st.download_button(
                        label="📄 Télécharger la fiche PDF",
                        data=pdf_bytes,
                        file_name=f"Fiche_{row['Nom']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

    st.markdown("""<div style="text-align:center; padding:20px; border-top:2px solid #FF0000; margin-top:30px;">
    <b>Refuge Médéric - Version Alpha_1.9</b></div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
