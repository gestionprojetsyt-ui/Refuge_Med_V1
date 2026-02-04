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

# --- 2. FONCTIONS DE FORMATAGE ET CHARGEMENT ---

def format_image_url(url):
    if not isinstance(url, str) or url == "0" or url == "": return None
    url = url.strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            # Utilisation du lien thumbnail pour une compatibilité maximale
            return f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1200"
    return url if url.startswith('http') else None

@st.cache_data(ttl=60)
def load_all_data(base_url):
    try:
        clean_url = base_url.split('/edit')[0]
        # Chargement onglet principal
        df_animaux = pd.read_csv(f"{clean_url}/export?format=csv")
        
        # Chargement onglet Config (pour la pop-up)
        df_config = pd.DataFrame()
        try:
            config_url = f"{clean_url}/gviz/tq?tqx=out:csv&sheet=Config"
            df_config = pd.read_csv(config_url)
        except:
            pass
            
        return df_animaux, df_config
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- 3. DIALOGUE POP-UP (IMAGE EN GRAND) ---
@st.dialog("📢 ÉVÉNEMENT AU REFUGE", width="large")
def afficher_evenement(url_affiche):
    if url_affiche:
        # Affichage sans bordure pour un effet "affiche"
        st.image(url_affiche, use_container_width=True)
    st.markdown("---")
    st.markdown("### 🐾 Événement à ne pas manquer !")
    if st.button("Voir les animaux du refuge", use_container_width=True):
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
        max-height: 550px; width: 100%; object-fit: cover; border-radius: 10px;
    }}
    .footer-container {{
        background-color: white; padding: 25px; border-radius: 15px; margin-top: 50px;
        text-align: center; border: 2px solid #FF0000;
    }}
    .version-note {{ font-size: 0.75em; color: #999; margin-top: 10px; font-style: italic; }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="logo-overlay">
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE PRINCIPALE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df, df_config = load_all_data(URL_SHEET)

    # Gestion de la Pop-up
    if not df_config.empty:
        df_config.columns = df_config.columns.str.strip()
        row_config = df_config[df_config['Cle'].astype(str).str.contains('Lien_Affiche', na=False)]
        if not row_config.empty:
            url_ev = format_image_url(str(row_config.iloc[0]['Valeur']))
            if url_ev and "popup_vue" not in st.session_state:
                st.session_state.popup_vue = True
                afficher_evenement(url_ev)

    # Affichage Catalogue
    if not df.empty:
        # Nettoyage et préparation des données
        def categoriser_age(age):
            try:
                age = float(str(age).replace(',', '.'))
                if age < 1: return "Moins d'un an (Junior)"
                elif 1 <= age <= 5: return "1 à 5 ans (Jeune Adulte)"
                elif 5 < age < 10: return "5 à 10 ans (Adulte)"
                else: return "10 ans et plus (Senior)"
            except: return "Non précisé"
        
        df['Tranche_Age'] = df['Âge'].apply(categoriser_age)
        df_dispo = df[df['Statut'] != "Adopté"].copy()

        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        # Filtres
        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"])

        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés** et **identifiés** (puce électronique) avant leur départ.")

        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]

        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")

        # Boucle d'affichage Plein Format
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                # Photo en grand (Haut)
                url_p = format_image_url(row['Photo'])
                st.image(url_p if url_p else "https://via.placeholder.com/600x400", use_container_width=True)
                
                # Infos
                st.subheader(row['Nom'])
                statut = str(row['Statut']).strip()
                if "Urgence" in statut: st.error(f"🚨 {statut}")
                elif "Réservé" in statut: st.warning(f"🟠 {statut}")
                else: st.info(f"🏠 {statut}")

                st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                
                # Les 3 Onglets
                t1, t2, t3 = st.tabs(["📖 Histoire", "📋 Caractère", "📞 Contact"])
                with t1: st.write(row['Histoire'])
                with t2: st.write(row['Description'])
                with t3:
                    if "Réservé" in statut:
                        st.markdown(f'<div class="btn-reserve">🧡 Animal déjà réservé</div>', unsafe_allow_html=True)
                    else:
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
                Développé par Firnaeth.<br>
                <div class="version-note">Version 2.4 - Pop-up Image Large & Fiches Plein Format</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur de chargement : {e}")
