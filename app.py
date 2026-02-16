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
    page_title="Refuge Médéric", 
    layout="centered", 
    page_icon=f"data:image/png;base64,{logo_b64}" if logo_b64 else "🐾"
)

# --- 2. STYLE CSS FORCE (LOGO EN FOND FIXE 5%) ---
# Cette partie utilise le fond de l'application elle-même pour éviter qu'il disparaisse
if logo_b64:
    st.markdown(f"""
        <style>
        /* On injecte le logo directement dans le conteneur principal de Streamlit */
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80vw;
            height: 80vh;
            background-image: url("data:image/png;base64,{logo_b64}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: contain;
            opacity: 0.05; /* 5% d'opacité */
            z-index: -1;
            pointer-events: none;
        }}

        /* Suppression des pointillés du badge senior */
        .badge-senior {{
            background-color: #FFF9C4 !important;
            color: #856404 !important;
            padding: 10px;
            border-radius: 12px;
            font-weight: bold;
            text-align: center;
            border: none !important; /* AUCUN POINTILLÉ */
            margin-top: 10px;
            display: block;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
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
        </style>
    """, unsafe_allow_html=True)

# --- 3. FONCTION PDF ---
def generer_pdf(row):
    try:
        class PDF(FPDF):
            def header(self):
                try:
                    with self.local_context(fill_opacity=0.05):
                        self.image(URL_LOGO_HD, x=45, y=80, w=120)
                except: pass
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"FICHE : {str(row['Nom']).upper()}", ln=True, align='C')
        return bytes(pdf.output())
    except: return None

# --- 4. CHARGEMENT DONNÉES ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        df = pd.read_csv(csv_url)
        def cat(a):
            try: return "Senior" if float(str(a).replace(',','.')) >= 10 else "Autre"
            except: return "Autre"
        df['Tranche_Age'] = df['Âge'].apply(cat)
        return df
    except: return pd.DataFrame()

def format_image_url(url):
    url = str(url).strip()
    match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
    if match: return f"https://drive.google.com/uc?export=view&id={match.group(1) or match.group(2)}"
    return url

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        for i, row in df[df['Statut'] != "Adopté"].iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    u = format_image_url(row['Photo'])
                    st.image(u if u.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                    if row['Tranche_Age'] == "Senior":
                        st.markdown('<div class="badge-senior">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)
                with c2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Âge']} ans")
                    pdf = generer_pdf(row)
                    if pdf:
                        st.download_button(f"📄 Fiche {row['Nom']}", pdf, f"{row['Nom']}.pdf", "application/pdf", key=f"b_{i}")
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erreur : {e}")
