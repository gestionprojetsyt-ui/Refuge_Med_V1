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

# --- 2. FONCTION DE CONVERSION DRIVE (CORRIGÉE) ---
def preparer_lien_image(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        # Extrait l'ID du fichier peu importe le format du lien (file/d/ ou id=)
        match = re.search(r"(?<=/d/)[^/]+|(?<=id=)[^&]+", url)
        if match:
            doc_id = match.group(0)
            # Utilise le format miniature haute résolution (plus fiable que uc?export)
            return f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1000"
    return url

# --- 3. LA POP-UP ---
@st.dialog("📢 ÉVÉNEMENTS AU REFUGE", width="large")
def afficher_evenement(liens):
    # On inverse pour avoir la plus récente en haut
    for i, url in enumerate(liens[::-1]):
        img_url = preparer_lien_image(url)
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="{img_url}" style="max-height: 70vh; max-width: 100%; border-radius: 10px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1);">
            </div>
        """, unsafe_allow_html=True)
        if i < len(liens) - 1:
            st.markdown("---")
            
    st.markdown("### 🐾 Événements à ne pas manquer !")
    if st.button("Fermer et voir les animaux", use_container_width=True):
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

# --- 5. CHARGEMENT DATA ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        base_url = url.split('/edit')[0]
        df = pd.read_csv(f"{base_url}/export?format=csv")
        df_config = pd.DataFrame()
        try:
            df_config = pd.read_csv(f"{base_url}/gviz/tq?tqx=out:csv&sheet=Config")
        except: pass
        return df, df_config
    except: return pd.DataFrame(), pd.DataFrame()

# --- 6. LOGIQUE PRINCIPALE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df, df_config = load_all_data(URL_SHEET)

    # Gestion de la Pop-up Multi-affiches
    if not df_config.empty:
        # On récupère toutes les lignes qui contiennent "Lien_Affiche"
        mask = df_config.iloc[:, 0].astype(str).str.contains('Lien_Affiche', na=False, case=False)
        lignes_affiches = df_config[mask]
        
        if not lignes_affiches.empty and "popup_vue" not in st.session_state:
            liens_trouves = []
            for _, r in lignes_affiches.iterrows():
                valeur = str(r.iloc[1]).strip()
                if valeur != "nan" and "http" in valeur:
                    liens_trouves.append(valeur)
            
            if liens_trouves:
                st.session_state.popup_vue = True
                afficher_evenement(liens_trouves)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        # Filtres et catalogue
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        c1, c2 = st.columns(2)
        with c1:
            choix_esp = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Âge", ["Tous"] + sorted(df_dispo['Âge'].dropna().unique().tolist()))

        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés** et **identifiés** (puce électronique) avant leur départ du refuge pour une adoption responsable.")
        
        df_filtre = df_dispo.copy()
        if choix_esp != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_esp]
        # (Logique de filtrage simplifiée pour l'exemple)

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    st.image(preparer_lien_image(row['Photo']), use_container_width=True)
                with col_txt:
                    st.subheader(row['Nom'])
                    st.info(f"🏠 {row['Statut']}")
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    t1, t2 = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t1: st.write(row['Histoire'])
                    with t2: st.write(row['Description'])
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                    st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row["Nom"]}" class="btn-contact">📩 Envoyer un Mail</a>', unsafe_allow_html=True)

    # --- 7. PIED DE PAGE ---
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
                Développé par Firnaeth. avec passion pour nos amis à quatre pattes.
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
