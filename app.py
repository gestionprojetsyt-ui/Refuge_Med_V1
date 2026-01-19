import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Refuge Médéric", layout="centered")

# --- 2. FONCTION LOGO ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E" 

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, timeout=10)
        return base64.b64encode(response.content).decode()
    except: return None

logo_b64 = get_base64_image(URL_LOGO_HD)

# --- 3. STYLE CSS (LISIBILITÉ MAXIMALE) ---
st.markdown(f"""
    <style>
    /* On fixe le fond en gris clair pour éviter le noir */
    .stApp {{ background-color: #F0F2F5 !important; }}
    
    /* Le logo est placé de manière stable en haut à gauche */
    .fixed-logo {{
        position: absolute;
        top: -50px;
        left: -20px;
        width: 150px;
        opacity: 0.6;
        z-index: 0;
    }}

    /* FICHE ANIMAL EN HTML PUR POUR ÉVITER LE MODE SOMBRE */
    .fiche-animal {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #E0E0E0;
        margin-bottom: 25px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }}
    
    .fiche-animal h2 {{ color: #FF0000 !important; margin: 0 0 10px 0; }}
    .fiche-animal p {{ color: #333333 !important; font-size: 16px; line-height: 1.4; }}
    
    /* Badges de statut personnalisés */
    .st-badge {{
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
        color: white !important;
    }}
    
    .btn-call {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    
    .btn-mail {{ 
        text-decoration: none !important; color: white !important; background-color: #1976d2; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}

    /* On cache les éléments parasites de Streamlit */
    #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. CHARGEMENT DATA ---
@st.cache_data(ttl=60)
def load_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        return df.dropna(subset=['Nom'])
    except: return pd.DataFrame()

def format_img(url):
    if "drive.google.com" in str(url):
        m = re.search(r"/d/([^/]+)", str(url))
        if m: return f"https://drive.google.com/uc?export=view&id={m.group(1)}"
    return url

# --- 5. AFFICHAGE ---
try:
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" class="fixed-logo">', unsafe_allow_html=True)

    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_data(URL_SHEET)

    if not df.empty:
        st.markdown("<h1 style='text-align:center; color:#FF0000;'>Refuge Médéric</h1>", unsafe_allow_html=True)
        
        df_filtre = df[df['Statut'] != "Adopté"]

        for _, row in df_filtre.iterrows():
            # Création de la fiche en HTML pour bloquer les couleurs
            statut = str(row['Statut'])
            bg_statut = "#1976d2" # Bleu par défaut
            if "Urgence" in statut: bg_statut = "#d32f2f"
            if "Réservé" in statut: bg_statut = "#f57c00"

            st.markdown(f"""
                <div class="fiche-animal">
                    <h2>{row['Nom']}</h2>
                    <div class="st-badge" style="background-color: {bg_statut};">{statut}</div>
                    <p><b>Espèce :</b> {row['Espèce']} | <b>Sexe :</b> {row['Sexe']} | <b>Âge :</b> {row['Âge']} ans</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Photo et boutons (on garde Streamlit ici pour la gestion des colonnes)
            c1, c2 = st.columns([1, 1])
            with c1:
                st.image(format_img(row['Photo']), use_container_width=True)
            with c2:
                with st.expander("📖 Son histoire"):
                    st.write(row['Histoire'])
                
                if "Réservé" not in statut:
                    st.markdown(f'<a href="tel:0558736882" class="btn-call">📞 Appeler</a>', unsafe_allow_html=True)
                    st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption {row["Nom"]}" class="btn-mail">📩 Mail</a>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

    # FOOTER FIXE
    st.markdown("""
        <div style="background-color:white; padding:20px; border-radius:10px; border:1px solid red; text-align:center; color:black;">
            <b>📍 Refuge Médéric</b><br>182 chemin Lucien Viau, Saint-Paul-lès-Dax<br>📞 05 58 73 68 82
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.info("Chargement des animaux...")
