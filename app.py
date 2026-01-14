import streamlit as st
import pandas as pd
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Refuge Médéric - Grand Dax", 
    layout="centered", 
    page_icon="🐾"
)

# --- 2. FONCTIONS TECHNIQUES ---

@st.cache_data(ttl=3600)
def load_all_data(url):
    csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
    df = pd.read_csv(csv_url, engine='c', low_memory=False)
    
    # Classification automatique par âge
    def categoriser_age(age):
        try:
            age = float(str(age).replace(',', '.'))
            if age < 1: return "Moins d'un an (Junior)"
            elif 1 <= age <= 5: return "1 à 5 ans (Adulte)"
            elif 5 < age < 10: return "5 à 10 ans (Adulte)"
            else: return "10 ans et plus (Senior)"
        except:
            return "Non précisé"
            
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
    [data-testid="stImage"] img { border-radius: 15px; object-fit: cover; height: 260px; }
    .footer { text-align: center; color: #888; font-size: 0.85em; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    /* Style pour le bouton actualiser en pleine largeur */
    .stButton>button { width: 100%; border-radius: 10px; background-color: #f0f2f6; border: 1px solid #dcdfe3; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT ET INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    st.title("🐾 Refuge Médérique")
    st.markdown("#### Association Animaux du Grand Dax")

    if not df.empty:
        # --- ZONE DE FILTRES ---
        col1, col2 = st.columns(2)
        
        with col1:
            liste_especes = ["Tous"] + sorted(df['Espèce'].dropna().unique().tolist())
            choix_espece = st.selectbox("🐶 Espèce", liste_especes)
        
        with col2:
            liste_ages = ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"]
            choix_age = st.selectbox("🎂 Tranche d'âge", liste_ages)
            
        # Bouton actualiser placé juste en dessous des deux colonnes
        if st.button("🔄 Actualiser les données du refuge"):
            st.cache_data.clear()
            st.rerun()
        
        # --- LOGIQUE DE FILTRAGE ---
        df_filtre = df.copy()
        if choix_espece != "Tous":
            df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous":
            df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]
            
        st.write(f"Résultat : **{len(df_filtre)}** protégé(s) trouvé(s).")
        st.markdown("---")

        # --- AFFICHAGE DES FICHES ---
        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1.5, 2])
                with c1:
                    url_photo = format_image_url(row['Photo'])
                    if url_photo.startswith('http'):
                        st.image(url_photo, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/300?text=Photo+à+venir")

                with c2:
                    st.header(row['Nom'])
                    statut = str(row['Statut'])
                    if "Adopté" in statut: st.success(f"✅ {statut}")
                    elif "Urgence" in statut: st.error(f"🚨 {statut}")
                    else: st.warning(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    st.markdown(f"📅 **Arrivé le :** {row['Date_Entree']}")
                    st.write(f"**Description :** {row['Description']}")
                    with st.expander("Son histoire"):
                        st.write(row['Histoire'])

    # --- PIED DE PAGE ---
   st.markdown(f'''
       <div class="footer">
            © 2026 - Application officielle du Refuge Médéric<br>
            <b>Association Animaux du Grand Dax</b><br>
            Développé par Firnaeth. avec passion pour nos amis à quatre pattes
        </div>
    ''', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur de connexion : {e}")
