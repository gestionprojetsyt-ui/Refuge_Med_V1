import streamlit as st
import pandas as pd
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Refuge Médérique - Grand Dax", 
    layout="centered", 
    page_icon="🐾"
)

# --- 2. FONCTIONS TECHNIQUES ---

# Cache pour éviter les chargements inutiles et assurer la fluidité
@st.cache_data(ttl=3600)
def load_all_data(url):
    # Transformation du lien Google Sheet en CSV
    csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
    return pd.read_csv(csv_url, engine='c', low_memory=False)

# Transformation des liens Google Drive pour affichage direct
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
    [data-testid="stImage"] img { border-radius: 15px; object-fit: cover; height: 260px; }
    .footer { text-align: center; color: #888; font-size: 0.85em; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    /* Alignement du bouton avec le menu de sélection */
    div[data-testid="stColumn"] > div > div > div > button {
        margin-top: 28px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT ET INTERFACE ---
try:
    # URL récupérée dans les Secrets de Streamlit
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    
    # Chargement initial
    df = load_all_data(URL_SHEET)

    st.title("🐾 Refuge Médérique")
    st.markdown("#### Association Animaux du Grand Dax")

    if not df.empty:
        # --- BLOC DE CONTRÔLE : FILTRE + ACTUALISATION ---
        col_filtre, col_refresh = st.columns([3, 1])
        
        with col_filtre:
            liste_especes = ["Tous"] + sorted(df['Espèce'].dropna().unique().tolist())
            choix = st.selectbox("Quel animal recherchez-vous ?", liste_especes)
        
        with col_refresh:
            # Le bouton vide le cache et relance l'appli pour voir les modifs du Sheet
            if st.button("🔄 Actualiser"):
                st.cache_data.clear()
                st.rerun()
        
        # Filtrage des données
        df_filtre = df[df['Espèce'] == choix] if choix != "Tous" else df
        st.write(f"Nous avons actuellement **{len(df_filtre)}** protégés à vous présenter.")
        st.markdown("---")

        # --- BOUCLE D'AFFICHAGE DES ANIMAUX ---
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1.5, 2])
                
                with col1:
                    # Affichage de la photo (Google Drive ou Placeholder si vide)
                    url_photo = format_image_url(row['Photo'])
                    if url_photo.startswith('http'):
                        st.image(url_photo, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/300?text=Photo+à+venir")

                with col2:
                    st.header(row['Nom'])
                    
                    # Statut avec code couleur
                    statut = str(row['Statut'])
                    if "Adopté" in statut: st.success(f"✅ {statut}")
                    elif "Urgence" in statut: st.error(f"🚨 {statut}")
                    else: st.warning(f"🏠 {statut}")

                    # Carte d'identité
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    # Date d'arrivée (Placée sous l'âge comme demandé)
                    st.markdown(f"📅 **Arrivé le :** {row['Date_Entree']}")
                    
                    st.write(f"**Description :** {row['Description']}")
                    
                    # Histoire complète masquée pour gagner de la place
                    with st.expander("En savoir plus sur son histoire"):
                        st.write(row['Histoire'])

    else:
        st.info("Le catalogue est en cours de préparation.")

    # --- PIED DE PAGE ---
    st.markdown(f'''
       <div class="footer">
            © 2026 - Application officielle du Refuge Médérique<br>
            <b>Association Animaux du Grand Dax</b><br>
            Développé par Firnaeth. avec passion pour nos amis à quatre pattes
        </div>
    ''', unsafe_allow_html=True)

except Exception as e:
    st.error("Une erreur est survenue lors de la connexion aux données.")
