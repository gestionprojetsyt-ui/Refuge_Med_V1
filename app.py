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

# --- 2. FONCTIONS DE CHARGEMENT ---

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        # On essaie d'extraire l'ID du fichier
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            # On utilise le lien de téléchargement direct qui fonctionne mieux avec Streamlit
            return f"https://drive.google.com/uc?export=download&id={doc_id}"
    return url

@st.cache_data(ttl=60)
def load_data_from_sheets(base_url):
    try:
        clean_url = base_url.split('/edit')[0]
        # Animaux
        df_animaux = pd.read_csv(f"{clean_url}/export?format=csv")
        # Config (onglet Config)
        config_url = f"{clean_url}/gviz/tq?tqx=out:csv&sheet=Config"
        df_config = pd.read_csv(config_url)
        return df_animaux, df_config
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- 3. POP-UP ÉVÉNEMENT ---
@st.dialog("📢 ÉVÉNEMENT AU REFUGE")
def afficher_evenement(url_affiche):
    st.image(url_affiche, use_container_width=True)
    st.markdown("### 🐾 Événement à ne pas manquer !")
    if st.button("Fermer et voir les animaux"):
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
    
    .btn-reserve {{ 
        text-decoration: none !important; color: white !important; background-color: #ff8f00; 
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

    # Gestion de l'affiche sécurisée
    url_evenement = None
    if not df_config.empty and 'Cle' in df_config.columns:
        ligne = df_config[df_config['Cle'] == 'Lien_Affiche']
        if not ligne.empty:
            val_url = str(ligne.iloc[0]['Valeur']).strip()
            # On n'affiche que si c'est un vrai lien HTTP
            if val_url.startswith('http'):
                url_evenement = format_image_url(val_url)

    if url_evenement and "popup_vue" not in st.session_state:
        st.session_state.popup_vue = True
        try:
            afficher_evenement(url_evenement)
        except:
            pass 

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"])

        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés** et **identifiés**.")
        
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    u_p = format_image_url(row['Photo'])
                    st.image(u_p if u_p.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
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

    # --- 6. PIED DE PAGE ---
    st.markdown("""
        <div class="footer-container">
            <div style="color:#222; font-size:0.95em;">
                <b style="color:#FF0000;">Refuge Médéric - Association Animaux du Grand Dax</b><br>
                182 chemin Lucien Viau, 40990 St-Paul-lès-Dax<br>
                📞 05 58 73 68 82 | ⏰ 14h00 - 18h00 (Mercredi au Dimanche)
            </div>
            <div style="font-size:0.85em; color:#666; margin-top:15px; padding-top:15px; border-top:1px solid #ddd;">
                © 2026 - Application officielle du Refuge Médéric<br>
                🌐 <a href="https://refugedax40.wordpress.com/" target="_blank">Visiter notre site internet</a><br>
                Développé par <b>Firnaeth.</b> avec passion pour nos amis à quatre pattes.
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur de chargement des données.")
