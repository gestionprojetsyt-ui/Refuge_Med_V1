import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Refuge Médéric", layout="centered", page_icon="🐾")

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

# --- 3. STYLE CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F5F7F9 !important; }}
    
    .custom-bg {{
        position: fixed; top: 20%; left: -15vh; width: 60vh;
        opacity: 0.25; z-index: -1; pointer-events: none;
    }}

    /* LA FICHE ANIMAL (BLANCHE) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important;
        padding: 20px !important;
        border-radius: 15px !important;
        border: 1px solid #ddd !important;
    }}

    /* LE NOUVEAU BADGE BLEU (FORCÉ) */
    .badge-bleu {{
        background-color: #0077b6 !important;
        color: white !important;
        padding: 8px 15px;
        border-radius: 10px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }}
    .badge-rouge {{ background-color: #d32f2f !important; color: white !important; padding: 8px 15px; border-radius: 10px; font-weight: bold; display: inline-block; margin-bottom: 10px; }}
    .badge-orange {{ background-color: #ef6c00 !important; color: white !important; padding: 8px 15px; border-radius: 10px; font-weight: bold; display: inline-block; margin-bottom: 10px; }}

    /* BOUTONS CONTACT */
    .btn-call {{ text-decoration: none !important; color: white !important; background-color: #2e7d32; padding: 10px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
    .btn-mail {{ text-decoration: none !important; color: white !important; background-color: #1976d2; padding: 10px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}

    .footer {{ background-color: white; padding: 25px; border-radius: 15px; margin-top: 50px; text-align: center; border: 2px solid #FF0000; color: #333; }}
    </style>
    
    <img src="data:image/png;base64,{logo_b64}" class="custom-bg">
""", unsafe_allow_html=True)

# --- 4. FONCTIONS ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        df = df.dropna(subset=['Nom'])
        return df
    except: return pd.DataFrame()

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)", url)
        if match: return f"https://drive.google.com/uc?export=view&id={match.group(1)}"
    return url

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        
        df_dispo = df[df['Statut'] != "Adopté"]

        for _, row in df_dispo.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    st.image(format_image_url(row['Photo']), use_container_width=True)
                with col_txt:
                    st.subheader(row['Nom'])
                    
                    # ICI ON UTILISE LE BADGE DESSINÉ À LA MAIN
                    statut = str(row['Statut']).strip()
                    if "Urgence" in statut:
                        st.markdown(f'<div class="badge-rouge">🚨 {statut}</div>', unsafe_allow_html=True)
                    elif "Réservé" in statut:
                        st.markdown(f'<div class="badge-orange">🟠 {statut}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="badge-bleu">🏠 {statut}</div>', unsafe_allow_html=True)

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    with st.expander("📖 Voir son histoire"):
                        st.write(row['Histoire'])
                    
                    if "Réservé" not in statut:
                        st.markdown(f'<a href="tel:0558736882" class="btn-call">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption {row["Nom"]}" class="btn-mail">📩 Mail</a>', unsafe_allow_html=True)

    st.markdown(f'<div class="footer"><b>📍 Refuge Médéric</b><br>182 chemin Lucien Viau, Saint-Paul-lès-Dax</div>', unsafe_allow_html=True)

except Exception as e:
    st.error("Connexion...")
