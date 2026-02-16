import streamlit as st
import pandas as pd
import re
import requests
import base64

# --- 1. CONFIGURATION DE LA PAGE ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E"

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except: return None
    return None

logo_b64 = get_base64_image(URL_LOGO_HD)

st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon=f"data:image/png;base64,{logo_b64}" if logo_b64 else "🐾"
)

# --- 2. POP-UP ÉVÉNEMENTS ---
@st.dialog("📢 ÉVÉNEMENTS AU REFUGE", width="large")
def afficher_evenement(liens):
    liste_ordonnee = liens[::-1]
    for i, url in enumerate(liste_ordonnee):
        if url:
            if "drive.google.com" in url:
                doc_id = url.split('id=')[-1].split('&')[0].split('/')[-1]
                if "/d/" in url: doc_id = url.split('/d/')[1].split('/')[0]
                display_url = f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1000"
            else: display_url = url
            st.markdown(f"""<div style="text-align: center;"><img src="{display_url}" style="max-height: 70vh; max-width: 100%; border-radius: 10px; margin-bottom:10px;"></div>""", unsafe_allow_html=True)
            if i < len(liste_ordonnee) - 1:
                st.markdown("""<hr style="border: 0; border-top: 2px solid #ddd; margin: 30px auto; width: 60%;">""", unsafe_allow_html=True)
    if st.button("✨ Découvrir nos boules de poils à l'adoption", use_container_width=True):
        st.rerun()

# --- 3. STYLE VISUEL CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: transparent !important; }}
    .logo-overlay {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 70vw; opacity: 0.04; z-index: -1; pointer-events: none;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important; border-radius: 15px !important;
        border: 1px solid #ddd !important; box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
        padding: 20px !important; margin-bottom: 20px !important;
    }}
    .senior-tag {{
        background-color: #E3F2FD; color: #0D47A1; padding: 5px 10px;
        border-radius: 5px; font-weight: bold; font-size: 0.9em; border: 1px solid #BBDEFB;
        display: inline-block; margin-bottom: 10px;
    }}
    .btn-contact {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32 !important; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    h1 {{ color: #FF0000 !important; font-weight: 800; }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="logo-overlay">
    """, unsafe_allow_html=True)

# --- 4. CHARGEMENT DATA ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        base_url = url.split('/edit')[0]
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        df = pd.read_csv(csv_url, engine='c', low_memory=False)
        df_config = pd.DataFrame()
        try:
            df_config = pd.read_csv(f"{base_url}/gviz/tq?tqx=out:csv&sheet=Config")
        except: pass

        def categoriser_age(age):
            try:
                age = float(str(age).replace(',', '.'))
                if age < 1: return "Moins d'un an (Junior)"
                elif 1 <= age <= 5: return "1 à 5 ans (Jeune Adulte)"
                elif 5 < age < 10: return "5 à 10 ans (Adulte)"
                else: return "10 ans et plus (Senior)"
            except: return "Non précisé"
        df['Tranche_Age'] = df['Âge'].apply(categoriser_age)
        return df, df_config
    except: return pd.DataFrame(), pd.DataFrame()

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            return f"https://drive.google.com/uc?export=view&id={doc_id}"
    return url

# --- 5. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df, df_config = load_all_data(URL_SHEET)

    if not df_config.empty:
        mask = df_config.iloc[:, 0].astype(str).str.contains('Lien_Affiche', na=False, case=False)
        lignes_ev = df_config[mask]
        if not lignes_ev.empty and "popup_vue" not in st.session_state:
            liens = [str(r.iloc[1]).strip() for _, r in lignes_ev.iterrows() if "http" in str(r.iloc[1])]
            if liens:
                st.session_state.popup_vue = True
                afficher_evenement(liens)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        
        c1, c2 = st.columns(2)
        with c1: choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2: choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"])

        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]

        for _, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    u_photo = format_image_url(row['Photo'])
                    st.image(u_photo if u_photo and u_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                with col_txt:
                    st.subheader(row['Nom'])
                    
                    if row['Tranche_Age'] == "10 ans et plus (Senior)":
                        st.markdown('<div class="senior-tag">🎁 SOS Senior : Don Libre</div>', unsafe_allow_html=True)
                    
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    
                    # --- PRÉPARATION DES APTITUDES ---
                    def check_ok(val): return "✅" if str(val).upper() == "TRUE" else "❌"
                    def check_color(val): return "#2e7d32" if str(val).upper() == "TRUE" else "#c62828"
                    
                    icon_cat = "https://cdn-icons-png.flaticon.com/512/620/620851.png"
                    icon_dog = "https://cdn-icons-png.flaticon.com/512/620/620885.png"
                    icon_kid = "https://cdn-icons-png.flaticon.com/512/167/167750.png"

                    # BOITE APTITUDE AVEC LISERÉ ROUGE
                    apt_html = f"""
                    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #FF0000; margin: 15px 0; border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;">
                        <b style="color:#FF0000; display:block; margin-bottom:10px; font-size:0.9em;">🏠 APTITUDES :</b>
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <img src="{icon_cat}" width="20" style="margin-right: 10px;">
                            <span style="flex-grow: 1; color: #333; font-size: 0.9em;">Ok Chats</span>
                            <span style="color: {check_color(row.get('OK_Chat'))}; font-weight: bold;">{check_ok(row.get('OK_Chat'))}</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <img src="{icon_dog}" width="20" style="margin-right: 10px;">
                            <span style="flex-grow: 1; color: #333; font-size: 0.9em;">Ok Chiens</span>
                            <span style="color: {check_color(row.get('OK_Chien'))}; font-weight: bold;">{check_ok(row.get('OK_Chien'))}</span>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <img src="{icon_kid}" width="20" style="margin-right: 10px;">
                            <span style="flex-grow: 1; color: #333; font-size: 0.9em;">Ok Enfants</span>
                            <span style="color: {check_color(row.get('OK_Enfant'))}; font-weight: bold;">{check_ok(row.get('OK_Enfant'))}</span>
                        </div>
                    </div>
                    """
                    st.markdown(apt_html, unsafe_allow_html=True)

                    t1, t2 = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t1: st.write(row['Histoire'])
                    with t2: st.write(row['Description'])
                    
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)

    # PIED DE PAGE AVEC LISERÉ ROUGE
    st.markdown("""<div style="text-align:center; padding:20px; border-top:5px solid #FF0000; margin-top:30px; background-color:white; border-radius:10px; border-bottom: 1px solid #eee; border-left: 1px solid #eee; border-right: 1px solid #eee;">
    <b style="color:#FF0000;">Refuge Médéric - Association Animaux du Grand Dax</b><br>
    182 chemin Lucien Viau, 40990 St-Paul-lès-Dax</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
