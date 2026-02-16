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

# --- 2. FONCTION PDF (FILIGRANE 5% DANS LE DOCUMENT) ---
def traduire_bool(valeur):
    return "OUI" if str(valeur).upper() == "TRUE" else "NON"

def generer_pdf(row):
    try:
        class PDF(FPDF):
            def header(self):
                # FILIGRANE DU PDF A 5%
                try:
                    with self.local_context(fill_opacity=0.05):
                        # Positionné au centre de la page
                        self.image(URL_LOGO_HD, x=45, y=80, w=120)
                except: pass

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", 'I', 8)
                self.set_text_color(128)
                self.cell(0, 10, "Refuge Médéric - 182 chemin Lucien Viau, 40990 St-Paul-lès-Dax - 05 58 73 68 82", 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        
        # Titre
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"RENCONTREZ {str(row['Nom']).upper()}", ln=True, align='C')
        pdf.ln(5)

        # Photo centrale
        try:
            u_photo = format_image_url(row['Photo'])
            resp = requests.get(u_photo, timeout=5)
            pdf.image(BytesIO(resp.content), x=60, y=35, w=90)
            pdf.ln(100)
        except: pdf.ln(10)

        # Infos
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        
        # Bloc Aptitudes
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  SES APTITUDES :", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - OK Chats : {traduire_bool(row.get('OK_Chat'))}", ln=True)
        pdf.cell(0, 8, f"   - OK Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - OK Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=True)
        
        return bytes(pdf.output())
    except: return None

# --- 3. STYLE CSS (APP WEB & BADGE SANS POINTILLÉS) ---
st.markdown(f"""
    <style>
    /* Filigrane Web stable à 5% */
    .watermark {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 75vw;
        opacity: 0.05;
        z-index: -1000;
        pointer-events: none;
    }}
    
    /* Badge Senior SANS pointillés */
    .badge-senior {{
        background-color: #FFF9C4 !important;
        color: #856404 !important;
        padding: 10px;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        border: none !important;
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

    [data-testid="stImage"] img {{ 
        border: 5px solid white !important; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important; 
    }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="watermark">
""", unsafe_allow_html=True)

# --- 4. CHARGEMENT DATA ---
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
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | {row['Âge']} ans")
                    
                    pdf = generer_pdf(row)
                    if pdf:
                        st.download_button(f"📄 Fiche {row['Nom']}", pdf, f"{row['Nom']}.pdf", "application/pdf", key=f"dl_{i}")
                    
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
