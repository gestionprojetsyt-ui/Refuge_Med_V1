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

@st.cache_data(ttl=3600)
def load_all_data(url):
    # Conversion du lien Google Sheets en lien CSV direct
    csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
    df = pd.read_csv(csv_url, engine='c', low_memory=False)
    
    # Classification automatique par tranche d'âge
    def categoriser_age(age):
        try:
            # Gestion des virgules et conversion en nombre
            age = float(str(age).replace(',', '.'))
            if age < 1: return "Moins d'un an (Junior)"
            elif 1 <= age <= 5: return "1 à 5 ans (Jeune Adulte)"
            elif 5 < age < 10: return "5 à 10 ans (Adulte)"
            else: return "10 ans et plus (Senior)"
        except:
            return "Non précisé"
            
    df['Tranche_Age'] = df['Âge'].apply(categoriser_age)
    return df

def format_image_url(url):
    # Conversion des liens Google Drive pour affichage direct
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
    /* Images arrondies et cadrées */
    [data-testid="stImage"] img { border-radius: 15px; object-fit: cover; height: 280px; }
    
    /* Bouton Actualiser neutre */
    .stButton>button { width: 100%; border-radius: 10px; background-color: #f0f2f6; color: #31333F; border: 1px solid #dcdfe3; }
    
    /* Bouton Contact Vert */
    .contact-link { text-decoration: none; color: white !important; background-color: #28a745; padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 15px; }
    .contact-link:hover { background-color: #218838; }

    /* Style du pied de page */
    .footer-container {
        background-color: #f8f9fa;
        padding: 30px;
        border-radius: 15px;
        margin-top: 50px;
        border-top: 1px solid #eee;
        text-align: center;
    }
    .footer-info { color: #666; font-size: 0.9em; line-height: 1.6; }
    .copyright { 
        font-size: 0.75em; 
        color: #aaa; 
        margin-top: 20px; 
        border-top: 1px solid #eee; 
        padding-top: 10px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT ET INTERFACE ---
try:
    # Récupération de l'URL dans les secrets Streamlit
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    st.title("🐾 Refuge Médéric")
    st.markdown("#### Association Animaux du Grand Dax")

    if not df.empty:
        # --- BLOC DE FILTRES ---
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
        
        # --- FILTRAGE DES DONNÉES ---
        df_filtre = df.copy()
        if choix_espece != "Tous":
            df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous":
            df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]
            
        st.write(f"**{len(df_filtre)}** protégé(s) correspond(ent) à vos critères")
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
                    
                    # Badge de statut
                    statut = str(row['Statut'])
                    if "Adopté" in statut: st.success(f"✅ {statut}")
                    elif "Urgence" in statut: st.error(f"🚨 {statut}")
                    else: st.warning(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    st.markdown(f"📅 **Arrivé le :** {row['Date_Entree']}")
                    
                    # Onglets pour l'histoire et le caractère
                    tab_histoire, tab_caractere = st.tabs(["📖 Histoire", "📋 Caractère"])
                    
                    with tab_histoire:
                        st.write(row['Histoire'])
                        
                    with tab_caractere:
                        st.write(row['Description'])
                    
                    # Bouton de contact par email
                    st.markdown(f"""
                        <a href="mailto:animauxdugranddax@gmail.com?subject=Demande d'adoption pour {row['Nom']}" class="contact-link">
                            📩 Contacter le refuge pour {row['Nom']}
                        </a>
                    """, unsafe_allow_html=True)

    # --- 5. PIED DE PAGE ---
    st.markdown("""
        <div class="footer-container">
            <div class="footer-info">
                <b>Refuge Médéric - Association Animaux du Grand Dax</b><br>
                182 chemin Lucien Viau, 40990 St-Paul-lès-Dax<br>
                📞 05 58 73 68 82 | ⏰ 14h00 - 18h00 (Mercredi au Dimanche)
            </div>
            <div class="copyright">
                 © 2026 - Application officielle du Refuge Médérique<br>
                <b>Association Animaux du Grand Dax</b><br>
                Développé par Firnaeth. avec passion pour nos amis à quatre pattes
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error("Une erreur est survenue lors de la connexion aux données.")
