import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Refuge Médéric", 
    layout="centered", 
    page_icon="🐾"
)

# --- 2. LOGO ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E" 

@st.cache_data
def get_base64_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        return base64.b64encode(response.content).decode()
    except: return None

logo_b64 = get_base64_image(URL_LOGO_HD)

# --- 3. STYLE CSS (COUCHES + OPACITÉ 11%) ---
st.markdown(f"""
    <style>
    /* COUCHE 1 : LE FOND DE L'APPLI */
    .stApp {{
        background-color: #F8F9FA !important;
    }}
    
    /* COUCHE 2 : LE LOGO À 11% D'OPACITÉ */
    .logo-couche {{
        position: fixed;
        top: 20%;
        left: -15vh;
        width: 65vh;
        opacity: 0.11; /* OPACITÉ RÉDUITE À 11% */
        z-index: 0;
        pointer-events: none;
    }}

    /* COUCHE 3 : LES FICHES BLANCHES TOTALEMENT OPAQUES */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: #FFFFFF !important;
        opacity: 1 !important;
        padding: 20px !important;
        border-radius: 15px !important;
        border: 1px solid #EAEAEA !important;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.08) !important;
        position: relative;
        z-index: 10;
        margin-bottom: 25px !important;
    }}

    /* TEXTE NOIR POUR LISIBILITÉ MAXIMALE */
    h1, h2, h3, p, span, li, label, .stExpander {{
        color: #111111 !important;
    }}

    h1 {{ color: #FF0000 !important; font-weight: 800; }}

    /* PHOTO STYLE POLAROID */
    [data-testid="stImage"] img {{ 
        border: 8px solid white !important; 
        border-radius: 4px !important; 
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1) !important;
        height: 320px;
        object-fit: cover;
    }}
    
    /* BOUTONS CONTACT */
    .btn-call {{ text-decoration: none !important; color: white !important; background-color: #2e7d32; padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
    .btn-mail {{ text-decoration: none !important; color: white !important; background-color: #1976d2; padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}

    .footer {{
        background-color: white; padding: 25px; border-radius: 15px; margin-top: 50px; text-align: center; border: 2px solid #FF0000; position: relative; z-index: 10;
    }}
    </style>
    
    <img src="data:image/png;base64,{logo_b64}" class="logo-couche">
""", unsafe_allow_html=True)

# --- 4. DATA ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        return df.dropna(subset=['Nom'])
    except: return pd.DataFrame()

def format_image_url(url):
    if "drive.google.com" in str(url):
        match = re.search(r"/d/([^/]+)", str(url))
        if match: return f"https://drive.google.com/uc?export=view&id={match.group(1)}"
    return url

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        df_filtre = df[df['Statut'] != "Adopté"]

        for _, row in df_filtre.iterrows():
            with st.container(border=True): 
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    st.image(format_image_url(row['Photo']), use_container_width=True)
                with col_txt:
                    st.subheader(row['Nom'])
                    
                    statut = str(row['Statut']).strip()
                    if "Urgence" in statut: st.error(f"🚨 {statut}")
                    elif "Réservé" in statut: st.warning(f"🟠 {statut}")
                    else: st.info(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    with st.expander("📖 Voir son histoire"):
                        st.write(row['Histoire'])
                    
                    if "Réservé" not in statut:
                        st.markdown(f'<a href="tel:0558736882" class="btn-call">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption {row["Nom"]}" class="btn-mail">📩 Envoyer un Mail</a>', unsafe_allow_html=True)

    st.markdown(f'''<div class="footer"><b>📍 Refuge Médéric</b><br>182 chemin Lucien Viau, Saint-Paul-lès-Dax</div>''', unsafe_allow_html=True)

except Exception as e:
    st.error("Données en cours de chargement...")
