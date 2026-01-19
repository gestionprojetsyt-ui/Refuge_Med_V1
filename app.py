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

# --- 2. CONFIGURATION DU LOGO (LIEN DIRECT GOOGLE DRIVE) ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E" 

@st.cache_data
def get_base64_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
        return None
    except:
        return None

logo_b64 = get_base64_image(URL_LOGO_HD)

# --- 3. STYLE CSS (LOGO COUPE / PAS DE CADRE / OPACITE 35%) ---
if logo_b64:
    st.markdown(f"""
        <style>
        /* On retire tout fond blanc forcé sur les containers Streamlit */
        .stApp {{
            background-color: #FFFFFF;
        }}
        
        /* Application du logo en fond avec pseudo-élément pour l'opacité */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: url("data:image/png;base64,{logo_b64}");
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: 70vh;
            background-position: -25vh 30%; /* Coupe le logo à gauche */
            opacity: 0.35; /* 35% d'opacité comme demandé */
            z-index: -1;
        }}

        h1 {{ color: #FF0000 !important; font-weight: 800; }}
        
        /* Style Polaroid pour les photos */
        [data-testid="stImage"] img {{ 
            border: 10px solid white !important; 
            border-radius: 5px !important; 
            box-shadow: 0px 4px 15px rgba(0,0,0,0.1) !important;
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

# --- 4. FONCTIONS TECHNIQUES ---
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

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)", url)
        if match:
            id_photo = match.group(1)
            return f"https://drive.google.com/uc?export=view&id={id_photo}"
    return url

# --- 5. INTERFACE ET AFFICHAGE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()

        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        # Filtres de recherche
        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"])

        # Engagement Santé
        st.success("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés**, **identifiés** (puce électronique) et **stérilisés** avant leur départ du refuge pour une adoption responsable.")
        
        # Application des filtres
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]

        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")
        st.markdown("---")

        # Boucle d'affichage des animaux
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    url_photo = format_image_url(row['Photo'])
                    st.image(url_photo if url_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                with col_txt:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    t_hist, t_carac = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t_hist: st.write(row['Histoire'])
                    with t_carac: st.write(row['Description'])
                    st.markdown(f"""<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>""", unsafe_allow_html=True)

    # --- PIED DE PAGE ---
    st.markdown(f'''
        <div class="footer">
            © 2026 - Application officielle du Refuge Médérique<br>
            <b>Association Animaux du Grand Dax</b><br>
            Développé par Firnaeth. avec passion pour nos amis à quatre pattes
        </div>
    ''', unsafe_allow_html=True)

except Exception as e:
    st.error("Impossible de charger les données. Vérifiez vos Secrets Streamlit.")
