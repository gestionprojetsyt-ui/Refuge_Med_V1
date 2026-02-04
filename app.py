import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION ---
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
    page_title="Refuge Médéric", 
    layout="centered", 
    page_icon="🐾"
)

# --- 2. LA POP-UP (RESTE COMME TU VEUX) ---
@st.dialog("📢 ÉVÉNEMENT AU REFUGE", width="large")
def afficher_evenement(url_affiche):
    if url_affiche:
        if "id=" in url_affiche or "drive.google.com" in url_affiche:
            doc_id = url_affiche.split('id=')[-1].split('&')[0].split('/')[-1]
            url_affiche = f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1000"
        
        st.markdown(f"""
            <div style="text-align: center;">
                <img src="{url_affiche}" style="max-height: 65vh; max-width: 100%; border-radius: 10px; object-fit: contain;">
            </div>
        """, unsafe_allow_html=True)
    st.markdown("### 🐾 Événement à ne pas manquer !")
    if st.button("Fermer", use_container_width=True):
        st.rerun()

# --- 3. STYLE CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: transparent !important; }}
    .logo-overlay {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 70vw; opacity: 0.04; z-index: -1; pointer-events: none;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important; border-radius: 15px !important;
        border: 1px solid #ddd !important; padding: 20px !important; margin-bottom: 20px !important;
    }}
    h1 {{ color: #FF0000 !important; }}
    .btn-contact {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stImage"] img {{ 
        height: 350px !important; object-fit: cover !important; border-radius: 10px;
    }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="logo-overlay">
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT SÉCURISÉ ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        base_url = url.split('/edit')[0]
        # Onglet Principal
        df = pd.read_csv(f"{base_url}/export?format=csv")
        # Onglet Config
        df_config = pd.DataFrame()
        try:
            config_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet=Config"
            df_config = pd.read_csv(config_url)
        except: pass
        return df, df_config
    except: return pd.DataFrame(), pd.DataFrame()

def format_image_url(url):
    if not isinstance(url, str) or url == "nan": return None
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            return f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1000"
    return url

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df, df_config = load_all_data(URL_SHEET)

    # Affichage Pop-up
    if not df_config.empty:
        df_config.columns = [str(c).strip() for c in df_config.columns]
        row_ev = df_config[df_config.iloc[:, 0].astype(str).str.contains('Lien_Affiche', na=False, case=False)]
        if not row_ev.empty and "popup_vue" not in st.session_state:
            st.session_state.popup_vue = True
            afficher_evenement(format_image_url(str(row_ev.iloc[0, 1])))

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        # Filtres
        c1, c2 = st.columns(2)
        with c1:
            especes = ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist())
            choix_espece = st.selectbox("🐶 Espèce", especes)
        with c2:
            choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Junior", "Adulte", "Senior"])

        # Filtrage
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": 
            df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]

        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")

        # AFFICHAGE DE TOUS LES ANIMAUX
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    img_url = format_image_url(row['Photo'])
                    st.image(img_url if img_url else "https://via.placeholder.com/300")
                with col_txt:
                    st.subheader(row['Nom'])
                    st.info(f"🏠 {row['Statut']}")
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    t1, t2 = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t1: st.write(row['Histoire'] if pd.notna(row['Histoire']) else "À venir...")
                    with t2: st.write(row['Description'] if pd.notna(row['Description']) else "À venir...")
                    
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)

except Exception as e:
    st.error("Erreur de connexion aux données. Vérifiez votre lien Google Sheets.")
