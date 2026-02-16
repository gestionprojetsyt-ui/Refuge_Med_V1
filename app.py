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

# --- 2. STYLE CSS (FILIGRANE WEB FIXE 5%) ---
# On utilise une image en position fixed avec un z-index négatif
if logo_b64:
    st.markdown(f"""
        <style>
        .watermark {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 70vw;
            opacity: 0.05; /* OPACITÉ 5% */
            z-index: -1000;
            pointer-events: none;
        }}
        
        .badge-senior {{
            background-color: #FFF9C4 !important;
            color: #856404 !important;
            padding: 10px;
            border-radius: 12px;
            font-weight: bold;
            text-align: center;
            border: 2px dashed #FBC02D;
            margin: 10px 0;
            display: block;
            font-size: 0.9em;
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
        }}
        </style>
        <img src="data:image/png;base64,{logo_b64}" class="watermark">
    """, unsafe_allow_html=True)

# --- 3. FONCTION PDF (OPACITÉ 5% DANS LE PDF) ---
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
        pdf.cell(0, 15, f"FICHE D'ADOPTION : {row['Nom'].upper()}", ln=True, align='C')
        
        try:
            u_photo = format_image_url(row['Photo'])
            pdf.image(u_photo, x=60, y=35, w=90)
            pdf.ln(100)
        except: pdf.ln(10)
        
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        return bytes(pdf.output())
    except: return None

# --- 4. CHARGEMENT ET LOGIQUE ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
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

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        st.write("Association Animaux du Grand Dax")
        
        df_dispo = df[df['Statut'] != "Adopté"]

        for i, row in df_dispo.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    u = format_image_url(row['Photo'])
                    st.image(u if u.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                    # AFFICHAGE DU BADGE SENIOR
                    if row['Tranche_Age'] == "Senior":
                        st.markdown('<div class="badge-senior">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)
                
                with col_txt := c2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | {row['Âge']} ans")
                    
                    pdf = generer_pdf(row)
                    if pdf:
                        st.download_button(f"📄 Fiche de {row['Nom']}", pdf, f"{row['Nom']}.pdf", "application/pdf", key=f"btn_{i}", use_container_width=True)
                    
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
