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

# --- 2. CONFIGURATION DU LOGO (OPACITÉ 0.03) ---
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

# --- 3. STYLE VISUEL (TOTALEMENT TRANSPARENT) ---
st.markdown(f"""
    <style>
    /* SUPPRESSION DE TOUS LES FONDS */
    .stApp {{
        background-color: transparent !important;
    }}

    /* LOGO À 0.03 D'OPACITÉ */
    .logo-bg {{
        position: fixed;
        top: 25%;
        left: -10vh;
        width: 60vh;
        opacity: 0.03;
        z-index: -1;
        pointer-events: none;
    }}
    
    /* SUPPRESSION DES CADRES ET DES FONDS BLANCS */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0px !important;
    }}

    /* TEXTE NOIR POUR ÊTRE LISIBLE */
    h1, h2, h3, p, span, li, label, .stExpander {{
        color: #000000 !important;
    }}

    h1 {{ color: #FF0000 !important; font-weight: 800; }}
    
    /* POLAROID AVEC BORD BLANC POUR LES PHOTOS */
    [data-testid="stImage"] img {{ 
        border: 8px solid white !important; 
        border-radius: 4px !important; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
        height: 300px;
        object-fit: cover;
    }}
    
    /* BOUTONS CONTACT VERT */
    .btn-contact {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    
    /* BOUTON RÉSERVÉ ORANGE */
    .btn-reserve {{ 
        text-decoration: none !important; color: white !important; background-color: #ff8f00; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}

    /* STYLE DU PIED DE PAGE */
    .footer-container {{
        text-align: center;
        margin-top: 50px;
        padding: 25px;
        border-top: 1px solid #FF0000;
    }}
    </style>
    
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="logo-bg">
    """, unsafe_allow_html=True)

# --- 4. DATA ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        df = pd.read_csv(csv_url, engine='c', low_memory=False)
        def categoriser_age(age):
            try:
                age = float(str(age).replace(',', '.'))
                if age < 1: return "Junior"
                elif 1 <= age <= 5: return "Jeune Adulte"
                elif 5 < age < 10: return "Adulte"
                else: return "Senior"
            except: return "Non précisé"
        df['Tranche_Age'] = df['Âge'].apply(categoriser_age)
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
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        
        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Âge", ["Tous", "Junior", "Jeune Adulte", "Adulte", "Senior"])

        # ENGAGEMENT SANTÉ RÉINTÉGRÉ
        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés**, **identifiés** (puce électronique) et **stérilisés** avant leur départ du refuge pour une adoption responsable.")
        
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]

        for _, row in df_filtre.iterrows():
            with st.container():
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    url_photo = format_image_url(row['Photo'])
                    st.image(url_photo if url_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                with col_txt:
                    st.subheader(row['Nom'])
                    statut = str(row['Statut']).strip()
                    if "Urgence" in statut: st.error(f"🚨 {statut}")
                    elif "Réservé" in statut: st.warning(f"🟠 {statut}")
                    else: st.info(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    t_hist, t_carac = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t_hist: st.write(row['Histoire'])
                    with t_carac: st.write(row['Description'])
                    
                    if "Réservé" in statut:
                        st.markdown(f'<div class="btn-reserve">🧡 Réservé</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption {row["Nom"]}" class="btn-contact">📩 Envoyer un Mail</a>', unsafe_allow_html=True)
            st.markdown("---")

    # --- PIED DE PAGE PERSONNALISÉ RÉINTÉGRÉ ---
    st.markdown("""
        <div class="footer-container">
            <div style="color:#222; font-size:0.95em; line-height:1.6;">
                <b style="color:#FF0000;">Refuge Médéric - Association Animaux du Grand Dax</b><br>
                182 chemin Lucien Viau, 40990 St-Paul-lès-Dax<br>
                📞 05 58 73 68 82 | ⏰ 14h00 - 18h00 (Mercredi au Dimanche)
            </div>
            <div style="font-size:0.85em; color:#666; margin-top:15px; padding-top:15px; border-top:1px solid #ddd;">
                Développé par Firnaeth avec passion pour nos amis à quatre pattes.
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error("Connexion au tableau impossible.")
