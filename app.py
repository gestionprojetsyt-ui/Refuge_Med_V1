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

# --- 2. CONFIGURATION DU LOGO (MÉTHODE BASE64 POUR LE FOND) ---
URL_LOGO_HD = "https://drive.google.com/file/d/1-xx9Lw9fbw1ILGKgWEkhXfOfrsGhTcum/view?usp=sharing" 

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url)
        return base64.b64encode(response.content).decode()
    except:
        return None

logo_b64 = get_base64_image(URL_LOGO_HD)

# --- 3. STYLE CSS (LOGO BACK + PIED DE PAGE + BOUTONS) ---
if logo_b64:
    st.markdown(f"""
        <style>
        /* LOGO EN BACKGROUND COUPE A GAUCHE */
        .stApp {{
            background-image: url("data:image/png;base64,{logo_b64}");
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-size: 60vh; 
            background-position: -20vh 30%; 
        }}

        /* Voile pour la lisibilité du texte */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(255, 255, 255, 0.65);
            z-index: -1;
        }}

        h1 {{ color: #FF0000 !important; font-weight: 800; }}
        
        /* Style Photo Polaroid */
        [data-testid="stImage"] img {{ 
            border: 10px solid white !important; 
            border-radius: 5px !important; 
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2) !important;
            object-fit: cover;
            height: 320px;
        }}
        
        .btn-contact {{ 
            text-decoration: none !important; color: white !important; background-color: #2e7d32; 
            padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
        }}

        .footer {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 25px;
            border-radius: 15px;
            margin-top: 50px;
            text-align: center;
            border: 2px solid #FF0000;
            color: #444;
            line-height: 1.6;
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

# --- 5. INTERFACE ET LOGIQUE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()

        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        # Filtres
        c1, c2 = st.columns(2)
        with c1:
            liste_especes = ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist())
            choix_espece = st.selectbox("🐶 Espèce", liste_especes)
        with c2:
            liste_ages = ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"]
            choix_age = st.selectbox("🎂 Tranche d'âge", liste_ages)

        # --- BLOC ENGAGEMENT SANTÉ RÉTABLI ---
        st.success("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés**, **identifiés** (puce électronique) et **stérilisés** avant leur départ du refuge pour une adoption responsable.")
        
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]

        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")
        st.markdown("---")

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

    # --- PIED DE PAGE PERSONNALISÉ ---
    st.markdown(f'''
        <div class="footer">
            © 2026 - Application officielle du Refuge Médérique<br>
            <b>Association Animaux du Grand Dax</b><br>
            Développé par Firnaeth. avec passion pour nos amis à quatre pattes
        </div>
    ''', unsafe_allow_html=True)

except Exception as e:
    st.error("Lien 'public_url' non configuré dans les secrets.")
