import streamlit as st
import pandas as pd
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon="🐾"
)

# --- 2. FONCTIONS TECHNIQUES ---

@st.cache_data(ttl=600) # Rafraîchissement toutes les 10 minutes
def load_all_data(url):
    # Transformation automatique du lien pour lecture CSV
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

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)", url)
        if match:
            id_photo = match.group(1)
            return f"https://drive.google.com/uc?export=view&id={id_photo}"
    return url

# --- 3. STYLE VISUEL (CSS) ---
st.markdown("""
    <style>
    [data-testid="stImage"] img { border-radius: 15px; object-fit: cover; height: 280px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #f0f2f6; color: #31333F; border: 1px solid #dcdfe3; }
    
    .contact-button { 
        text-decoration: none !important; 
        color: white !important; 
        background-color: #2e7d32; 
        padding: 12px; 
        border-radius: 8px; 
        display: block; 
        text-align: center; 
        font-weight: bold; 
        margin-top: 10px;
    }
    .contact-button:hover { background-color: #1b5e20; }
    
    .footer-container {
        background-color: #f8f9fa;
        padding: 30px;
        border-radius: 15px;
        margin-top: 50px;
        border-top: 1px solid #eee;
        text-align: center;
    }
    .footer-info { color: #666; font-size: 0.9em; line-height: 1.6; }
    .copyright { font-size: 0.75em; color: #aaa; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT ET INTERFACE ---

# METS TON LIEN GOOGLE SHEETS CI-DESSOUS
URL_SHEET = "https://docs.google.com/spreadsheets/d/1XZXKwCfJ_922HAkAANzpXyyZL97uJzcu84viFWdtgpA/edit?usp=sharing"

try:
    df = load_all_data(URL_SHEET)

    st.title("🐾 Refuge Médéric")
    st.markdown("#### Association Animaux du Grand Dax")

    if not df.empty:
        # --- FILTRES ---
        col1, col2 = st.columns(2)
        with col1:
            liste_especes = ["Tous"] + sorted(df['Espèce'].dropna().unique().tolist())
            choix_espece = st.selectbox("🐶 Espèce", liste_especes)
        with col2:
            liste_ages = ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"]
            choix_age = st.selectbox("🎂 Tranche d'âge", liste_ages)
            
        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés**, **identifiés** et **stérilisés** avant leur départ.")
        
        df_filtre = df.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]
            
        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")
        st.markdown("---")

        # --- FICHES ANIMAUX ---
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1.5, 2])
                with c1:
                    url_photo = format_image_url(row['Photo'])
                    st.image(url_photo if url_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                with c2:
                    st.header(row['Nom'])
                    statut = str(row['Statut'])
                    if "Adopté" in statut: st.success(f"✅ {statut}")
                    elif "Urgence" in statut: st.error(f"🚨 {statut}")
                    else: st.warning(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    st.markdown(f"📅 **Arrivé le :** {row['Date_Entree']}")
                    
                    tab_histoire, tab_caractere = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with tab_histoire: st.write(row['Histoire'])
                    with tab_caractere: st.write(row['Description'])
                    
                    # Boutons de contact (Même vert)
                    st.markdown(f"""<a href="tel:0558736882" class="contact-button">📞 Appeler le refuge</a>""", unsafe_allow_html=True)
                    st.markdown(f"""<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row['Nom']}" class="contact-button">📩 Envoyer un mail pour {row['Nom']}</a>""", unsafe_allow_html=True)

    # --- 5. PIED DE PAGE ---
    st.markdown("""
        <div class="footer-container">
            <div class="footer-info">
                <b>Refuge Médéric - Association Animaux du Grand Dax</b><br>
                182 chemin Lucien Viau, 40990 St-Paul-lès-Dax<br>
                📞 05 58 73 68 82 | ⏰ 14h00 - 18h00 (Mercredi au Dimanche)
            </div>
            <div class="copyright">
                 © 2026 - Application officielle du Refuge Médéric<br>
                <b>Association Animaux du Grand Dax</b><br>
                Développé par Firnaeth. avec passion
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error("⚠️ Erreur de connexion au classeur. Vérifiez que le lien Google Sheets est correct et publié sur le web.")
    st.info(f"Détail technique : {e}")
