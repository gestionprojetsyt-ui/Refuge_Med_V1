import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Refuge Médéric", layout="centered")

# --- 2. LOGO ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E" 

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, timeout=10)
        return base64.b64encode(response.content).decode()
    except: return None

logo_b64 = get_base64_image(URL_LOGO_HD)

# --- 3. STYLE CSS SIMPLE ET SOLIDE ---
st.markdown(f"""
    <style>
    /* On force un fond clair partout */
    .stApp {{ background-color: #FFFFFF !important; }}
    
    /* Logo en arrière-plan */
    .custom-bg {{
        position: fixed; top: 20%; left: -100px; width: 500px;
        opacity: 0.2; z-index: -1; pointer-events: none;
    }}

    /* Style des fiches */
    .fiche {{
        border: 1px solid #EEE;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        background-color: white;
    }}

    /* Boutons */
    .btn {{
        display: block; width: 100%; padding: 12px;
        text-align: center; color: white !important;
        text-decoration: none; font-weight: bold;
        border-radius: 8px; margin-top: 5px;
    }}
    .call {{ background-color: #2e7d32; }}
    .mail {{ background-color: #1976d2; }}
    
    h1 {{ color: #FF0000 !important; }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="custom-bg">
""", unsafe_allow_html=True)

# --- 4. DATA ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        return df.dropna(subset=['Nom'])
    except: return pd.DataFrame()

# --- 5. AFFICHAGE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_data(URL_SHEET)

    if not df.empty:
        st.title("🐾 Refuge Médéric")
        
        # Filtre Espece
        especes = ["Tous"] + sorted([x for x in df['Espèce'].unique() if str(x) != 'nan'])
        choix = st.selectbox("Choisir une espèce", especes)
        
        df_filtre = df[df['Statut'] != "Adopté"]
        if choix != "Tous":
            df_filtre = df_filtre[df_filtre['Espèce'] == choix]

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                st.subheader(row['Nom'])
                
                # Gestion couleur statut (Standard Streamlit pour éviter les bugs)
                statut = str(row['Statut'])
                if "Urgence" in statut: st.error(statut)
                elif "Réservé" in statut: st.warning(statut)
                else: st.info(statut)

                col1, col2 = st.columns([1, 1])
                with col1:
                    # Traitement URL Photo Drive
                    img_url = str(row['Photo'])
                    if "drive.google.com" in img_url:
                        id_img = re.search(r"/d/([^/]+)", img_url).group(1)
                        img_url = f"https://drive.google.com/uc?export=view&id={id_img}"
                    st.image(img_url, use_container_width=True)
                
                with col2:
                    st.write(f"**{row['Espèce']}** | {row['Sexe']}")
                    st.write(f"Âge : {row['Âge']} ans")
                    with st.expander("📖 Son histoire"):
                        st.write(row['Histoire'])
                    
                    if "Réservé" not in statut:
                        st.markdown(f'<a href="tel:0558736882" class="btn call">📞 Appeler</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption {row["Nom"]}" class="btn mail">📩 Mail</a>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("📍 **182 chemin Lucien Viau, Saint-Paul-lès-Dax**")

except Exception as e:
    st.error("Connexion au tableau impossible. Vérifiez le lien Google Sheets.")
