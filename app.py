import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Refuge Médéric", layout="centered")

# --- 2. FONCTION POUR "FORCER" L'IMAGE DANS LE CODE ---
def get_base64_image(url):
    try:
        response = requests.get(url)
        return base64.b64encode(response.content).decode()
    except:
        return None

# URL DE TEST (Une patte de chien) - Remplace par ton lien final après le test
URL_LOGO = "https://cdn-icons-png.flaticon.com/512/620/620851.png" 
img_base64 = get_base64_image(URL_LOGO)

# --- 3. STYLE CSS ULTIME ---
if img_base64:
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{img_base64}");
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: 550px; /* Taille du logo */
            background-position: -200px 20%; /* Coupe à gauche */
            background-color: white; /* Fond de secours */
        }}

        /* On ajoute un voile blanc pour que le texte reste lisible */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(255, 255, 255, 0.7); 
            z-index: -1;
        }}
        
        h1 {{ color: #FF0000 !important; }}
        
        [data-testid="stImage"] img {{ 
            border: 10px solid white !important; 
            box-shadow: 0px 4px 12px rgba(0,0,0,0.15) !important;
            height: 300px;
            object-fit: cover;
        }}

        .btn-contact {{ 
            text-decoration: none !important; color: white !important; background-color: #2e7d32; 
            padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        df = pd.read_csv(csv_url)
        return df
    except: return pd.DataFrame()

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    st.title("🐾 Refuge Médéric")
    st.write("---")

    if not df.empty:
        # On affiche juste un exemple pour tester le visuel
        for _, row in df.head(5).iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    st.image("https://via.placeholder.com/300", use_container_width=True)
                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}**")
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler</a>', unsafe_allow_html=True)

except Exception as e:
    st.error("En attente de configuration...")
