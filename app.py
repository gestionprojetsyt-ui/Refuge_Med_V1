import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# --- CONFIGURATION INITIALE ---
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
    page_title="Refuge Médéric", 
    layout="centered", 
    page_icon=f"data:image/png;base64,{logo_b64}" if logo_b64 else "🐾"
)

# --- FONCTION PDF (FILIGRANE 5%) ---
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
                self.cell(0, 10, "Refuge Médéric - 05 58 73 68 82", 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"FICHE : {row['Nom'].upper()}", ln=True, align='C')
        
        try:
            u_photo = format_image_url(row['Photo'])
            pdf.image(u_photo, x=60, y=35, w=90)
            pdf.ln(100)
        except: pdf.ln(10)
        
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        return bytes(pdf.output())
    except: return None

# --- STYLE CSS FIXE ---
# On utilise l'ID "stApp" pour être sûr que le logo reste en fond peu importe les clics
if logo_b64:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{logo_b64}");
            background-attachment: fixed;
            background-size: 60%;
            background-position: center;
            background-repeat: no-repeat;
            opacity: 1;
        }}
        /* On remet le contenu en avant pour que le fond ne gêne pas la lecture */
        .stApp > header, .stApp > .main {{
            background-color: rgba(255, 255, 255, 0.93); 
        }}
        
        .badge-senior {{
            background-color: #FFF9C4 !important;
            color: #856404 !important;
            padding: 12px;
            border-radius: 12px;
            font-weight: bold;
            text-align: center;
            border: 2px dashed #FBC02D;
            margin-top: 10px;
            display: block;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- CHARGEMENT DONNÉES ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        def categoriser(age):
            try:
                a = float(str(age).replace(',', '.'))
                return "Senior" if a >= 10 else "Autre"
            except: return "Autre"
        df['Tranche_Age'] = df['Âge'].apply(categoriser)
        return df
    except: return pd.DataFrame()

def format_image_url(url):
    url = str(url).strip()
    match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
    if match: return f"https://drive.google.com/uc?export=view&id={match.group(1) or match.group(2)}"
    return url

# --- INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        df_dispo = df[df['Statut'] != "Adopté"]

        for i, row in df_dispo.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    u = format_image_url(row['Photo'])
                    st.image(u if u.startswith('http') else "https://via.placeholder.com/300")
                    if row['Tranche_Age'] == "Senior":
                        st.markdown('<div class="badge-senior">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)
                
                with c2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Âge']} ans")
                    
                    pdf = generer_pdf(row)
                    if pdf:
                        st.download_button(f"📄 Fiche de {row['Nom']}", pdf, f"{row['Nom']}.pdf", "application/pdf", key=f"btn_{i}")
                    
                    st.markdown(f'<a href="tel:0558736882" style="text-decoration:none; color:white; background:#2e7d32; padding:10px; border-radius:8px; display:block; text-align:center; font-weight:bold; margin-top:5px;">📞 Appeler le refuge</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
