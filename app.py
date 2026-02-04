import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION DE LA PAGE ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E"

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except:
        return None
    return None

logo_b64 = get_base64_image(URL_LOGO_HD)

st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon=f"data:image/png;base64,{logo_b64}" if logo_b64 else "🐾"
)

# --- 2. FONCTIONS DE CHARGEMENT ET FORMATAGE ---

def format_image_url(url):
    if not isinstance(url, str): return ""
    url = url.strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            return f"https://drive.google.com/uc?export=view&id={doc_id}"
    return url

@st.cache_data(ttl=60)
def load_data_from_sheets(base_url):
    try:
        clean_url = base_url.split('/edit')[0]
        # Onglet principal (Animaux)
        df_animaux = pd.read_csv(f"{clean_url}/export?format=csv")
        # Onglet Config
        config_url = f"{clean_url}/gviz/tq?tqx=out:csv&sheet=Config"
        df_config = pd.read_csv(config_url)
        return df_animaux, df_config
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- 3. DIALOGUE POP-UP ÉVÉNEMENT ---
@st.dialog("📢 ÉVÉNEMENT AU REFUGE")
def afficher_evenement(url_affiche):
    if url_affiche and url_affiche.startswith('http'):
        st.image(url_affiche, use_container_width=True)
    st.markdown("### 🐾 Événement à ne pas manquer !")
    st.write("Plus d'informations sur notre site ou directement au refuge.")
    if st.button("Fermer"):
        st.rerun()

# --- 4. STYLE VISUEL CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: transparent !important; }}
    .logo-overlay {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 70vw; opacity: 0.04; z-index: -1; pointer-events: none;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important; border-radius: 15px !important;
        border: 1px solid #ddd !important; box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
        padding: 20px !important; margin-bottom: 20px !important;
    }}
    h1 {{ color: #FF0000 !important; font-weight: 800; }}
    .btn-contact {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    [data-testid="stImage"] img {{ 
        border: 8px solid white !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important;
        height: 320px; object-fit: cover;
    }}
    .footer-container {{
        background-color: white; padding: 25px; border-radius: 15px; margin-top: 50px;
        text-align: center; border: 2px solid #FF0000;
    }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="logo-overlay">
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE PRINCIPALE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df, df_config = load_data_from_sheets(URL_SHEET)

    # 1. Gestion de la Pop-up
    url_affiche_trouvee = None
    if not df_config.empty:
        df_config.columns = df_config.columns.str.strip()
        row_affiche = df_config[df_config['Cle'].astype(str).str.contains('Lien_Affiche', na=False)]
        if not row_affiche.empty:
            valeur = str(row_affiche.iloc[0]['Valeur']).strip()
            if valeur.startswith('http'):
                url_affiche_trouvee = format_image_url(valeur)

    if url_affiche_trouvee and "popup_vue" not in st.session_state:
        st.session_state.popup_vue = True
        afficher_evenement(url_affiche_trouvee)

    # 2. Catalogue des Animaux
    if not df.empty:
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        df_dispo = df[df['Statut'] != "Adopté"].copy()
        
        # Filtres
        c1, c2 = st.columns(2)
        with c1:
            especes = ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist())
            choix_espece = st.selectbox("🐶 Choisir une espèce", especes)
        with c2:
            st.write("") 
            if st.button("🔄 Actualiser"):
                st.cache_data.clear()
                st.rerun()

        df_filtre = df_dispo.copy()
        if choix_espece != "Tous":
            df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    u_photo = format_image_url(row['Photo'])
                    st.image(u_photo if u_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                with col2:
                    st.subheader(row['Nom'])
                    st.info(f"🏠 {row['Statut']}")
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    # --- Retour des 3 Onglets ---
                    t1, t2, t3 = st.tabs(["📖 Histoire", "📋 Caractère", "📞 Contact"])
                    with t1:
                        st.write(row['Histoire'])
                    with t2:
                        st.write(row['Description'])
                    with t3:
                        st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row["Nom"]}" class="btn-contact">📩 Envoyer un Mail</a>', unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
        <div class="footer-container">
            <b style="color:#FF0000;">Refuge Médéric - Association Animaux du Grand Dax</b><br>
            🌐 <a href="https://refugedax40.wordpress.com/" target="_blank">Visiter notre site internet</a><br>
            Développé par <b>Firnaeth.</b>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
