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

@st.cache_data(ttl=60) # Rafraîchissement rapide (1 min)
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
    except Exception as e:
        st.error("Erreur de connexion aux données.")
        return pd.DataFrame()

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
    /* Design des images */
    [data-testid="stImage"] img { border-radius: 15px; object-fit: cover; height: 280px; }
    
    /* Boutons standards */
    .stButton>button { width: 100%; border-radius: 10px; }
    
    /* Bouton Contact (Vert) */
    .contact-button { 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
    
    /* Bouton Réservé (Orange Ambre) */
    .reserve-button { 
        text-decoration: none !important; color: white !important; background-color: #ff8f00; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }

    /* Encart Pied de page */
    .footer-container {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 15px;
        margin-top: 50px;
        border: 1px solid #eee;
        text-align: center;
    }
    .footer-info { color: #444; font-size: 0.9em; line-height: 1.6; }
    .copyright { font-size: 0.8em; color: #888; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT ET INTERFACE ---

try:
    # Retour au mode SECRET
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        # CONDITION : Supprimer immédiatement les animaux adoptés de l'affichage
        df_dispo = df[df['Statut'] != "Adopté"].copy()

        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        col1, col2 = st.columns(2)
        with col1:
            liste_especes = ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist())
            choix_espece = st.selectbox("🐶 Espèce", liste_especes)
        with col2:
            liste_ages = ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"]
            choix_age = st.selectbox("🎂 Tranche d'âge", liste_ages)
            
        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés** et **identifiés** (puce électronique) avant leur départ du refuge pour une adoption responsable.")
        
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]
            
        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")
        st.markdown("---")

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1.5, 2])
                with c1:
                    url_photo = format_image_url(row['Photo'])
                    st.image(url_photo if url_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                with c2:
                    st.header(row['Nom'])
                    
                    statut = str(row['Statut']).strip()
                    
                    # Affichage visuel du statut
                    if "Urgence" in statut: st.error(f"🚨 {statut}")
                    elif "Réservé" in statut: st.warning(f"🟠 {statut}")
                    else: st.info(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    tab_histoire, tab_caractere = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with tab_histoire: st.write(row['Histoire'])
                    with tab_caractere: st.write(row['Description'])
                    
                    # Logique des boutons
                    if "Réservé" in statut:
                        st.markdown(f"""<div class="reserve-button">🧡 Animal déjà réservé</div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<a href="tel:0558736882" class="contact-button">📞 Appeler le refuge</a>""", unsafe_allow_html=True)
                        st.markdown(f"""<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row['Nom']}" class="contact-button">📩 Mail pour {row['Nom']}</a>""", unsafe_allow_html=True)

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
                Développé par Firnaeth. avec passion pour nos amis à quatre pattes
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error("L'application est en maintenance (Lien Secret non configuré).")
