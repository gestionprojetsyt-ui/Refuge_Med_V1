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

@st.cache_data(ttl=60)
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
    except:
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
    /* Supprime les bordures grises d'origine de Streamlit */
    div[data-testid="stVerticalBlockBordered"] {
        border: none !important;
        padding: 0 !important;
    }

    /* LE CADRE ROUGE FIN QUI ENGLOBE TOUTE LA FICHE */
    .fiche-complete {
        border: 2px solid #FF0000 !important;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 25px;
        background-color: white;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    /* EFFET POLAROID SUR LA PHOTO */
    .img-polaroid img { 
        border: 5px solid white !important; 
        border-radius: 8px !important; 
        box-shadow: 1px 1px 6px rgba(0,0,0,0.2) !important;
        object-fit: cover;
    }

    /* BOUTONS CONTACT VERTS */
    .btn-contact { 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
    
    /* BOUTON RÉSERVÉ ORANGE */
    .btn-reserve { 
        text-decoration: none !important; color: white !important; background-color: #ff8f00; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }

    /* PIED DE PAGE AVEC CADRE ROUGE */
    .footer-container {
        border: 2px solid #FF0000;
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 15px;
        margin-top: 50px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT ET INTERFACE ---

try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        # On cache les adoptés
        df_dispo = df[df['Statut'] != "Adopté"].copy()

        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        # Filtres
        c1, c2 = st.columns(2)
        with c1:
            liste_especes = ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist())
            choix_espece = st.selectbox("🐶 Espèce", liste_especes)
        with c2:
            liste_ages = ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"]
            choix_age = st.selectbox("🎂 Tranche d'âge", liste_ages)
            
        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        st.write(f"**{len(df_dispo)}** protégé(s) à l'adoption")
        st.markdown("---")

        # --- BOUCLE DES FICHES ---
        for _, row in df_dispo.iterrows():
            # Application des filtres
            if (choix_espece == "Tous" or row['Espèce'] == choix_espece) and \
               (choix_age == "Tous" or row['Tranche_Age'] == choix_age):
                
                # DEBUT DU CADRE ROUGE UNIQUE
                st.markdown('<div class="fiche-complete">', unsafe_allow_html=True)
                
                col_img, col_txt = st.columns([1, 1.2])
                
                with col_img:
                    url_photo = format_image_url(row['Photo'])
                    st.markdown('<div class="img-polaroid">', unsafe_allow_html=True)
                    st.image(url_photo if url_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col_txt:
                    st.subheader(row['Nom'])
                    statut = str(row['Statut']).strip()
                    
                    if "Urgence" in statut: st.error(f"🚨 {statut}")
                    elif "Réservé" in statut: st.warning(f"🟠 {statut}")
                    else: st.info(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    # Onglets
                    t_hist, t_carac = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t_hist: st.write(row['Histoire'])
                    with t_carac: st.write(row['Description'])
                    
                    # Boutons
                    if "Réservé" in statut:
                        st.markdown(f"""<div class="btn-reserve">🧡 Animal déjà réservé</div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>""", unsafe_allow_html=True)
                        st.markdown(f"""<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row['Nom']}" class="btn-contact">📩 Envoyer un Mail</a>""", unsafe_allow_html=True)
                
                # FIN DU CADRE ROUGE UNIQUE
                st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. PIED DE PAGE ---
    st.markdown("""
        <div class="footer-container">
            <div style="color:#222; font-size:0.95em; line-height:1.6;">
                <b>Refuge Médérique - Association Animaux du Grand Dax</b><br>
                182 chemin Lucien Viau, 40990 St-Paul-lès-Dax<br>
                📞 05 58 73 68 82 | ⏰ 14h00 - 18h00 (Mercredi au Dimanche)
            </div>
            <div style="font-size:0.85em; color:#666; margin-top:15px; padding-top:15px; border-top:1px solid #ddd;">
                 © 2026 - Application officielle du Refuge Médérique<br>
                <b>Association Animaux du Grand Dax</b><br>
                Développé par Firnaeth. avec passion pour nos amis à quatre pattes
            </div>
        </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.warning("Veuillez configurer 'public_url' dans les Secrets Streamlit.")
