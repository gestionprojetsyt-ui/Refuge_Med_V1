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

# --- 2. LA POP-UP (MULTI-ÉVÉNEMENTS : RÉCENT EN HAUT, VIEUX EN BAS) ---
@st.dialog("📢 ÉVÉNEMENTS AU REFUGE", width="large")
def afficher_evenements(liste_urls):
    # On inverse pour que la dernière ligne du Excel soit la 1ère affiche en haut
    liste_ordonnee = liste_urls[::-1]
    
    for i, url in enumerate(liste_ordonnee):
        if "id=" in url or "drive.google.com" in url:
            doc_id = url.split('id=')[-1].split('&')[0].split('/')[-1]
            url = f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1000"
        
        st.markdown(f"""
            <div style="text-align: center;">
                <img src="{url}" style="max-height: 65vh; max-width: 100%; border-radius: 10px; object-fit: contain; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">
            </div>
        """, unsafe_allow_html=True)
        
        # Séparateur entre les affiches
        if i < len(liste_ordonnee) - 1:
            st.markdown("""<hr style="border: 0; border-top: 2px solid #ddd; margin: 40px auto; width: 80%;">""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Fermer et voir les animaux", use_container_width=True):
        st.rerun()

# --- 3. STYLE VISUEL CSS ---
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

# --- 4. CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        base_url = url.split('/edit')[0]
        df = pd.read_csv(f"{base_url}/export?format=csv")
        df_config = pd.DataFrame()
        try:
            config_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet=Config"
            df_config = pd.read_csv(config_url)
        except: pass
        return df, df_config
    except: return pd.DataFrame(), pd.DataFrame()

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            return f"https://drive.google.com/uc?export=view&id={doc_id}"
    return url

# --- 5. INTERFACE ET LOGIQUE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df, df_config = load_all_data(URL_SHEET)

    # Affichage Pop-up
    if not df_config.empty:
        df_config.columns = [str(c).strip() for c in df_config.columns]
        lignes_ev = df_config[df_config.iloc[:, 0].astype(str).str.contains('Lien_Affiche', na=False, case=False)]
        if not lignes_ev.empty and "popup_vue" not in st.session_state:
            st.session_state.popup_vue = True
            liens = [format_image_url(str(r.iloc[1])) for _, r in lignes_ev.iterrows() if str(r.iloc[1]) != "nan"]
            if liens:
                afficher_evenements(liens)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()

        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Âge", ["Tous"] + sorted(df_dispo['Âge'].dropna().unique().tolist()))

        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        # --- RETOUR DU MESSAGE VACCIN ---
        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés** et **identifiés** (puce électronique) avant leur départ du refuge pour une adoption responsable.")
        
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Âge'] == choix_age]

        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    u_photo = format_image_url(row['Photo'])
                    st.image(u_photo if u_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
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
                    
                    if "Réservé" in statut:
                        st.markdown(f'<div class="btn-reserve">🧡 Animal déjà réservé</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row["Nom"]}" class="btn-contact">📩 Envoyer un Mail</a>', unsafe_allow_html=True)

    # --- 6. RETOUR DU PIED DE PAGE COMPLET ---
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
    st.error("Erreur de chargement des données.")

