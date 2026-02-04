import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION DE LA PAGE ---
# Le logo du refuge est utilisé ici pour l'onglet (Propriété du Refuge)
URL_LOGO_REFUGE = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E"

st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon=URL_LOGO_REFUGE
)

# --- 2. FONCTION POUR LE LOGO EN FOND (PROPRIÉTÉ REFUGE / CODE FIRNAETH) ---
@st.cache_data
def get_base64_logo():
    try:
        r = requests.get(URL_LOGO_REFUGE, timeout=10)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode()
    except:
        return None
    return None

logo_b64 = get_base64_logo()

# --- 3. DESIGN & STYLE CSS ---
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{logo_b64 if logo_b64 else ''}");
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        background-position: center !important;
        background-size: 70% !important;
    }}
    .stApp::before {{
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(240, 242, 246, 0.97); z-index: -1;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important;
        border-radius: 15px !important;
        border: 1px solid #ddd !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1) !important;
        padding: 20px !important;
    }}
    h1 {{ color: #FF0000 !important; font-weight: 800; }}
    .btn-contact {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    .btn-reserve {{ 
        text-decoration: none !important; color: white !important; background-color: #ff8f00; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    .footer {{
        text-align: center; padding: 30px 10px; margin-top: 50px;
        color: #444; border-top: 1px solid #FF0000; line-height: 1.6;
    }}
    .footer a {{ color: #FF0000 !important; text-decoration: none; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. GESTION DE LA POP-UP ÉVÉNEMENT ---
@st.dialog("📢 ÉVÉNEMENT AU REFUGE")
def afficher_evenement():
    # Remplace l'ID par celui de ton affiche sur Google Drive
    ID_AFFICHE = "1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E" # Ici j'ai remis le logo par défaut
    st.image(f"https://drive.google.com/uc?export=view&id={ID_AFFICHE}", use_container_width=True)
    st.markdown("""
    ### 🐾 Prochain Événement !
    Venez nous rencontrer lors de notre prochaine journée spéciale.
    - **Date :** À consulter sur notre site
    - **Lieu :** Refuge Médéric
    """)
    if st.button("Voir les animaux"):
        st.rerun()

# --- 5. CHARGEMENT DES DONNÉES ---
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
        if match: return f"https://drive.google.com/uc?export=view&id={match.group(1)}"
    return url

# --- 6. EXÉCUTION DE L'INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    # Affichage de la Pop-up au premier chargement seulement
    if "popup_vue" not in st.session_state:
        st.session_state.popup_vue = True
        afficher_evenement()

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"])

        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
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
                    t1, t2 = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t1: st.write(row['Histoire'])
                    with t2: st.write(row['Description'])
                    
                    if "Réservé" not in statut:
                        st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row["Nom"]}" class="btn-contact">📩 Envoyer un Mail</a>', unsafe_allow_html=True)

    # --- 7. PIED DE PAGE ---
    st.markdown("""
        <div class="footer">
            © 2026 - Application officielle du Refuge Médéric<br>
            <b>Association Animaux du Grand Dax</b><br>
            🌐 <a href="https://www.animauxdugranddax.fr" target="_blank">Visiter notre site internet</a><br>
            Développé par Firnaeth.
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error("Erreur de connexion aux données.")
