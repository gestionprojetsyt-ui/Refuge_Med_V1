import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon="🐾"
)

# --- 2. CONFIGURATION DE TON NOUVEAU LOGO (LIEN DIRECT) ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E" 

@st.cache_data
def get_base64_image(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
        return None
    except:
        return None

logo_b64 = get_base64_image(URL_LOGO_HD)

# --- 3. STYLE CSS (SANS LE VOILE BLANC) ---
if logo_b64:
    st.markdown(f"""
        <style>
        /* CONFIGURATION DU FOND SANS CADRE BLANC */
        .stApp {{
            background-image: url("data:image/png;base64,{logo_b64}");
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: 70vh; /* Ajuste la taille ici */
            background-position: -25vh 30%; /* Coupe de moitié à gauche */
            background-color: #FFFFFF; /* Fond blanc pur derrière le logo */
        }}

        /* On règle l'opacité directement sur l'image via un filtre si besoin, 
           mais ici on va jouer sur le z-index pour que le texte reste lisible */
        .stApp {{
            opacity: 1; 
        }}
        
        /* Pour appliquer l'opacité de 35% uniquement au logo sans affecter le texte */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: url("data:image/png;base64,{logo_b64}");
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: 70vh;
            background-position: -25vh 30%;
            opacity: 0.35; /* TES 35% D'OPACITÉ ICI */
            z-index: -1;
        }}

        h1 {{ color: #FF0000 !important; font-weight: 800; }}
        
        /* Style Photo Polaroid */
        [data-testid="stImage"] img {{ 
            border: 10px solid white !important; 
            border-radius: 5px !important; 
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2) !important;
            height: 320px;
            object-fit: cover;
        }}
        
        .btn-contact {{ 
            text-decoration: none !important; color: white !important; background-color: #2e7d32; 
            padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
        }}
        
        .footer {{
            background-color: rgba(255, 255, 255, 0.8);
            padding: 25px; border-radius: 15px; margin-top: 50px; text-align: center; border: 2px solid #FF0000; color: #444;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. LOGIQUE DES DONNÉES ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
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
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        st.success("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés**, **identifiés** (puce électronique) et **stérilisés** avant leur départ du refuge pour une adoption responsable.")
        
        # Le reste de ton code d'affichage (filtres, boucles...) se place ici
        st.write(f"Catalogue des **{len(df)}** animaux disponibles")

    # --- PIED DE PAGE ---
    st.markdown(f'''
        <div class="footer">
            © 2026 - Application officielle du Refuge Médérique<br>
            <b>Association Animaux du Grand Dax</b><br>
            Développé par Firnaeth. avec passion pour nos amis à quatre pattes
        </div>
    ''', unsafe_allow_html=True)

except Exception as e:
    st.error("Erreur lors du chargement des données.")
