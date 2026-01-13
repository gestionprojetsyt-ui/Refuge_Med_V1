import streamlit as st
import pandas as pd
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Refuge Médérique - Grand Dax", 
    layout="centered", 
    page_icon="🐾"
)

# --- 2. RÉCUPÉRATION DU LIEN SÉCURISÉ ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
except:
    st.error("Lien de la base de données non configuré dans les Secrets Streamlit.")
    st.stop()

# --- 3. FONCTIONS TECHNIQUES ---

# Convertit les liens Google Drive en images directes
def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)", url)
        if match:
            id_photo = match.group(1)
            return f"https://drive.google.com/uc?export=view&id={id_photo}"
    return url

# Prépare l'URL du Google Sheet pour la lecture
def get_csv_url(url):
    if "docs.google.com" in url:
        return url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
    return url

# SYSTÈME DE CACHE : Télécharge les données une fois et les garde 10 min en mémoire
# Cela rend les filtres instantanés pour vos 60 animaux.
@st.cache_data(ttl=600)
def load_data(url):
    return pd.read_csv(url)

# --- 4. STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    [data-testid="stImage"] img { border-radius: 15px; object-fit: cover; }
    .footer { text-align: center; color: #888; font-size: 0.85em; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    .stHeader { color: #2c3e50; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. CHARGEMENT ET AFFICHAGE ---
try:
    # On utilise la fonction avec cache ici
    df = load_data(get_csv_url(URL_SHEET))
    
    st.title("🐾 Refuge Médérique")
    st.markdown("### Association Animaux du Grand Dax")

    if not df.empty:
        # Barre de sélection (devenue ultra-rapide grâce au cache)
        liste_especes = ["Tous"] + sorted(df['Espèce'].dropna().unique().tolist())
        espece_choisie = st.selectbox("Quel animal recherchez-vous ?", liste_especes)
        
        df_filtre = df[df['Espèce'] == espece_choisie] if espece_choisie != "Tous" else df
        st.info(f"Nous avons actuellement **{len(df_filtre)}** protégés à vous présenter.")
        st.markdown("---")

        # --- BOUCLE D'AFFICHAGE ---
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1.5, 2])
                
                with col1:
                    # Photo optimisée
                    url_photo = format_image_url(row['Photo'])
                    if url_photo.startswith('http'):
                        st.image(url_photo, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/300?text=Photo+à+venir")

                with col2:
                    st.header(row['Nom'])
                    
                    # Statut visuel
                    statut = str(row['Statut'])
                    if "Adopté" in statut: st.success(f"✅ {statut}")
                    elif "Urgence" in statut: st.error(f"🚨 {statut}")
                    else: st.warning(f"🏠 {statut}")

                    # Carte d'identité
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    st.markdown(f"📅 **Arrivé le :** {row['Date_Entree']}")
                    
                    st.write(f"**Description :** {row['Description']}")
                    
                    # Histoire détaillée
                    with st.expander("En savoir plus sur son parcours"):
                        st.write(row['Histoire'])

    else:
        st.warning("Le catalogue est actuellement en cours de mise à jour.")

    # --- PIED DE PAGE ---
    st.markdown(f'''
        <div class="footer">
            © 2026 - Application officielle du Refuge Médérique<br>
            <b>Association Animaux du Grand Dax</b><br>
            Développé par [Firnaeth.]
        </div>
    ''', unsafe_allow_html=True)

except Exception as e:
    st.error("Connexion impossible au catalogue. Veuillez vérifier votre connexion internet.")

except Exception as e:
    st.error("Erreur de connexion aux données.")
