import streamlit as st
import pandas as pd
import os

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Refuge Médéric (Association Animaux du Grand Dax)", layout="centered", page_icon="🐾")

# --- 2. RÉCUPÉRATION DU LIEN SÉCURISÉ ---
# Le lien est caché dans les 'Secrets' de Streamlit pour plus de sécurité
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
except:
    st.error("Lien de la base de données non configuré dans les Secrets.")
    st.stop()

def get_csv_url(url):
    if "docs.google.com" in url:
        return url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
    return url

URL_CSV = get_csv_url(URL_SHEET)

# --- 3. STYLE CSS ---
st.markdown("""
    <style>
    .stAlert { padding: 5px; border-radius: 10px; }
    [data-testid="stImage"] img {
        border-radius: 15px;
        max-height: 350px; 
        object-fit: cover;
    }
    .footer {
        text-align: center;
        color: #888888;
        font-size: 0.9em;
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid #eeeeee;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🐾 Nos protégés")

try:
    # --- 4. CHARGEMENT DES DONNÉES ---
    # On désactive le cache pour voir les modifs du Sheet instantanément pendant les tests
    df = pd.read_csv(URL_CSV)

    # --- 5. FILTRE AUTOMATIQUE ---
    if not df.empty:
        liste_especes = ["Tous"] + sorted(df['Espèce'].dropna().unique().tolist())
        espece_choisie = st.selectbox("Quel animal recherchez-vous ?", liste_especes)
    else:
        espece_choisie = "Tous"

    st.markdown("---")

    # Filtrage
    df_filtre = df[df['Espèce'] == espece_choisie] if espece_choisie != "Tous" else df

    # --- 6. AFFICHAGE DE LA LISTE ---
    for index, row in df_filtre.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1.5, 2])
            
            with col1:
                photo = str(row['Photo']).strip()
                # Test si c'est un lien Web ou un fichier local
                if photo.startswith('http'):
                    st.image(photo, use_container_width=True)
                elif os.path.exists(photo):
                    st.image(photo, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/300?text=Photo+introuvable")

            with col2:
                st.header(row['Nom'])
                
                # Couleurs des statuts
                statut = str(row['Statut'])
                if "Adopté" in statut:
                    st.success(f"✅ {statut}")
                elif "Urgence" in statut:
                    st.error(f"🚨 {statut}")
                else:
                    st.warning(f"🏠 {statut}")

                st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                st.caption(f"📅 Arrivé le : {row['Date_Entree']}")
                
                tab1, tab2 = st.tabs(["📖 Histoire", "📋 Caractère"])
                with tab1:
                    st.write(row['Histoire'])
                with tab2:
                    st.write(row['Description'])

    # --- 7. PIED DE PAGE (DROITS RÉSERVÉS) ---
    st.markdown(
        """
        <div class="footer">
            <p>© 2026 - Application officielle de l’association Animaux du Grand Dax</p>
            <p>Tous droits réservés - Créé par <b>Firnaeth.</b></p>
            <p><i>Reproduction et utilisation interdites sans autorisation</i></p>
        </div>
        """, 
        unsafe_allow_html=True
    )

except Exception as e:
    st.error("Connexion impossible au fichier de données.")
    st.info("Si tu es en local, vérifie 'animaux.csv'. Si tu es sur Sheet, vérifie le lien de partage.")
