import streamlit as st
import pandas as pd
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Refuge Médérique (Association Animaux du Grand Dax)", layout="centered", page_icon="🐾")

# Récupération sécurisée du lien
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
except:
    st.error("Lien de la base de données non configuré dans les Secrets.")
    st.stop()

# --- 2. FONCTIONS TECHNIQUES ---

# Convertit les liens Google Drive "partageables" en liens "images directes"
def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        # Recherche l'ID du fichier dans le lien Google Drive
        match = re.search(r"/d/([^/]+)", url)
        if match:
            id_photo = match.group(1)
            return f"https://drive.google.com/uc?export=view&id={id_photo}"
    return url

# Convertit le lien du Sheet en lien de téléchargement CSV
def get_csv_url(url):
    if "docs.google.com" in url:
        return url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
    return url

# --- 3. STYLE CSS (Pour que ce soit joli) ---
st.markdown("""
    <style>
    [data-testid="stImage"] img { border-radius: 15px; object-fit: cover; }
    .footer { text-align: center; color: #888; font-size: 0.8em; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT ET AFFICHAGE ---
try:
    df = pd.read_csv(get_csv_url(URL_SHEET))
    
    st.title("🐾 Nos protégés")

    if not df.empty:
        # Filtre par espèce
        liste_especes = ["Tous"] + sorted(df['Espèce'].dropna().unique().tolist())
        espece_choisie = st.selectbox("Quel animal recherchez-vous ?", liste_especes)
        
        df_filtre = df[df['Espèce'] == espece_choisie] if espece_choisie != "Tous" else df
        st.write(f"Il y a actuellement **{len(df_filtre)}** animal(aux) à l'adoption.")
        st.markdown("---")

        # --- BOUCLE D'AFFICHAGE DES FICHES ---
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1.5, 2])
                
                with col1:
                    # Gestion de la photo (Google Drive ou lien direct)
                    url_photo = format_image_url(row['Photo'])
                    if url_photo.startswith('http'):
                        st.image(url_photo, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/300?text=Photo+à+venir")

                with col2:
                    st.header(row['Nom'])
                    
                    # Affichage du Statut (Urgence, Adopté, etc.)
                    statut = str(row['Statut'])
                    if "Adopté" in statut: st.success(f"✅ {statut}")
                    elif "Urgence" in statut: st.error(f"🚨 {statut}")
                    else: st.warning(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    # Infos détaillées
                    with st.expander("Voir son histoire"):
                        st.write(f"**Description :** {row['Description']}")
                        st.write(f"**Son histoire :** {row['Histoire']}")
                        st.caption(f"Arrivé au refuge le : {row['Date_Entree']}")

    else:
        st.info("Le catalogue est vide pour le moment.")

    # --- PIED DE PAGE ---
    st.markdown('<div class="footer">© 2026 - Application officielle deL’association Animaux du Grand Dax<br>Développé par Firnaeth.</div>', unsafe_allow_html=True)

except Exception as e:
    st.error("Problème de connexion avec le Google Sheet. Vérifiez le lien.")
