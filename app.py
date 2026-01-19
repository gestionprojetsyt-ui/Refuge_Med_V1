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

# --- 2. CONFIGURATION DU LOGO (TON LIEN DRIVE) ---
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

# --- 3. STYLE CSS (LOGO FLOTTANT, BOUTONS ET FOOTER) ---
if logo_b64:
    st.markdown(f"""
        <style>
        .stApp, .stMain, [data-testid="stAppViewContainer"] {{
            background-color: transparent !important;
        }}
        
        /* IMAGE DE FOND FIXE COUPEE A GAUCHE */
        .custom-bg {{
            position: fixed;
            top: 20%;
            left: -15vh;
            width: 60vh;
            opacity: 0.35;
            z-index: -1;
            pointer-events: none;
        }}

        h1 {{ color: #FF0000 !important; font-weight: 800; }}
        
        /* Style Polaroid */
        [data-testid="stImage"] img {{ 
            border: 10px solid white !important; 
            border-radius: 5px !important; 
            box-shadow: 0px 4px 15px rgba(0,0,0,0.1) !important;
            height: 320px;
            object-fit: cover;
        }}
        
        /* BOUTONS CONTACT */
        .btn-call {{ 
            text-decoration: none !important; color: white !important; background-color: #2e7d32; 
            padding: 10px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
        }}
        .btn-mail {{ 
            text-decoration: none !important; color: white !important; background-color: #1976d2; 
            padding: 10px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
        }}
        .btn-reserved {{ 
            text-decoration: none !important; color: white !important; background-color: #ff8f00; 
            padding: 10px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
        }}

        /* FOOTER */
        .footer {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 25px; border-radius: 15px; margin-top: 50px; text-align: center; border: 2px solid #FF0000; color: #333;
        }}
        </style>
        
        <img src="data:image/png;base64,{logo_b64}" class="custom-bg">
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

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"])

        # BLOC INFO BLEU
        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés** et **identifiés** (puce électronique) avant leur départ du refuge pour une adoption responsable.")
        
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
                    
                    # GESTION DES COULEURS DE STATUT (COMME AVANT)
                    statut = str(row['Statut']).strip()
                    if "Urgence" in statut:
                        st.error(f"🚨 {statut}")
                    elif "Réservé" in statut:
                        st.warning(f"🟠 {statut}")
                    else:
                        st.info(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    t_hist, t_carac = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t_hist: st.write(row['Histoire'])
                    with t_carac: st.write(row['Description'])
                    
                    if "Réservé" in statut:
                        st.markdown('<div class="btn-reserved">Animal déjà réservé</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<a href="tel:0558736882" class="btn-call">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Demande d\'adoption pour {row["Nom"]}" class="btn-mail">📩 Envoyer un Mail</a>', unsafe_allow_html=True)

    # PIED DE PAGE
    st.markdown(f'''
        <div class="footer">
            <b>📍 Adresse :</b> 182 chemin Lucien Viau, 40990 Saint-Paul-lès-Dax<br>
            <b>📞 Téléphone :</b> 05 58 73 68 82 | <b>⏰ Horaires :</b> 14h00 - 18h00 (Mercredi au Dimanche)<br>
            <hr style="border:0; border-top:1px solid #eee; margin:15px 0;">
            © 2026 - Application officielle du <b>Refuge Médéric</b><br>
            <b>Association Animaux du Grand Dax</b><br>
            Développé par <i>Firnaeth.</i> avec passion pour nos amis à quatre pattes
        </div>
    ''', unsafe_allow_html=True)

except Exception as e:
    st.error("Erreur de chargement.")
