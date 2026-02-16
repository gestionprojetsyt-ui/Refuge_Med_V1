import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# --- 1. CONFIGURATION ET LOGO ---
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

# --- 2. FONCTION PDF AVEC FILIGRANE 5% ---
def traduire_bool(valeur):
    return "OUI" if str(valeur).upper() == "TRUE" else "NON"

def generer_pdf(row):
    try:
        class PDF(FPDF):
            def header(self):
                try:
                    with self.local_context(fill_opacity=0.05):
                        self.image(URL_LOGO_HD, x=45, y=80, w=120)
                except: pass
            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", 'I', 8)
                self.set_text_color(128)
                self.cell(0, 10, "Refuge Médéric - 05 58 73 68 82", 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"FICHE D'ADOPTION : {row['Nom']}", ln=True, align='C')
        pdf.ln(5)
        try:
            u_photo = format_image_url(row['Photo'])
            pdf.image(u_photo, x=60, y=35, w=90)
            pdf.ln(100)
        except: pdf.ln(10)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  APTITUDES :", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - OK Chats : {traduire_bool(row.get('OK_Chat'))}", ln=True)
        pdf.cell(0, 8, f"   - OK Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - OK Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=True)
        return bytes(pdf.output())
    except: return None

# --- 3. CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        df = pd.read_csv(csv_url)
        def categoriser(age):
            try:
                a = float(str(age).replace(',', '.'))
                if a < 1: return "Moins d'un an (Junior)"
                elif 1 <= a <= 5: return "1 à 5 ans (Jeune Adulte)"
                elif 5 < a < 10: return "5 à 10 ans (Adulte)"
                else: return "10 ans et plus (Senior)"
            except: return "Non précisé"
        df['Tranche_Age'] = df['Âge'].apply(categoriser)
        return df
    except: return pd.DataFrame()

def format_image_url(url):
    url = str(url).strip()
    match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
    if match: return f"https://drive.google.com/uc?export=view&id={match.group(1) or match.group(2)}"
    return url

# --- 4. STYLE CSS (CORRIGÉ) ---
st.markdown(f"""
    <style>
    /* Style du badge Senior */
    .badge-don-libre {{
        background-color: #FFF9C4 !important;
        color: #856404 !important;
        padding: 10px !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        text-align: center !important;
        border: 2px dashed #FBC02D !important;
        margin-top: 15px !important;
        display: block !important;
        font-size: 0.9em !important;
    }}
    
    .btn-contact {{ 
        text-decoration: none !important; 
        color: white !important; 
        background-color: #2e7d32; 
        padding: 12px; 
        border-radius: 8px; 
        display: block; 
        text-align: center; 
        font-weight: bold; 
        margin-top: 10px; 
    }}

    [data-testid="stImage"] img {{ 
        border: 5px solid white !important; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important; 
        height: 300px; 
        object-fit: cover; 
    }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 70vw; opacity: 0.04; z-index: -1; pointer-events: none;">
    """, unsafe_allow_html=True)

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        
        esp = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        
        df_f = df_dispo.copy()
        if esp != "Tous": df_f = df_f[df_f['Espèce'] == esp]

        for i, row in df_f.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    img_url = format_image_url(row['Photo'])
                    st.image(img_url if img_url.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                    
                    # C'EST ICI QUE LE BADGE S'AFFICHE DANS L'APPLI
                    if row['Tranche_Age'] == "10 ans et plus (Senior)":
                        st.markdown('<div class="badge-don-libre">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)
                
                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | {row['Âge']} ans")
                    
                    pdf = generer_pdf(row)
                    if pdf:
                        st.download_button(f"📄 Fiche de {row['Nom']}", pdf, f"{row['Nom']}.pdf", "application/pdf", key=f"btn_{i}", use_container_width=True)
                    
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
