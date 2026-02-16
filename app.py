import streamlit as st
import pandas as pd
import re
import requests
import base64
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# --- 1. CONFIGURATION DE LA PAGE ---
URL_LOGO_HD = "https://drive.google.com/uc?export=view&id=1M8yTjY6tt5YZhPvixn-EoFIiolwXRn7E"

@st.cache_data
def get_base64_image(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
    except:
        return None
    return None

logo_b64 = get_base64_image(URL_LOGO_HD)

st.set_page_config(
    page_title="Refuge Médéric - Association Animaux du Grand Dax", 
    layout="centered", 
    page_icon=f"data:image/png;base64,{logo_b64}" if logo_b64 else "🐾"
)

# --- 2. FONCTION PDF (FILIGRANE 5% & PIED DE PAGE SITE) ---
def traduire_bool(valeur):
    return "OUI" if str(valeur).upper() == "TRUE" else "NON"

def generer_pdf(row):
    try:
        class PDF(FPDF):
            def header(self):
                # FILIGRANE DU PDF (Logo centré à 5% d'opacité)
                try:
                    with self.local_context(fill_opacity=0.05):
                        self.image(URL_LOGO_HD, x=45, y=80, w=120)
                except:
                    pass

            def footer(self):
                # PIED DE PAGE DU PDF
                self.set_y(-15)
                self.set_font("Helvetica", 'I', 8)
                self.set_text_color(128)
                infos_footer = "Refuge Médéric - 182 chemin Lucien Viau, 40990 St-Paul-lès-Dax | 05 58 73 68 82\nSite web : https://refugedax40.wordpress.com/"
                self.multi_cell(0, 4, infos_footer, align='C')

        pdf = PDF()
        pdf.add_page()
        
        # En-tête
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"FICHE D'ADOPTION : {row['Nom']}", ln=True, align='C')
        pdf.ln(5)

        # Insertion Photo
        try:
            u_photo = format_image_url(row['Photo'])
            resp = requests.get(u_photo, timeout=5)
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            img_buf = BytesIO()
            img.save(img_buf, format="JPEG")
            img_buf.seek(0)
            pdf.image(img_buf, x=60, y=35, w=90)
            pdf.ln(100)
        except:
            pdf.ln(10)

        # Infos
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        
        # Aptitudes
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  APTITUDES :", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(0, 8, f"   - OK Chats : {traduire_bool(row.get('OK_Chat'))}", ln=True)
        pdf.cell(0, 8, f"   - OK Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=True)
        pdf.cell(0, 8, f"   - OK Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=True)
        
        # Histoire
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, " SON HISTOIRE :", ln=True)
        pdf.set_font("Helvetica", '', 10)
        histoire = str(row.get('Histoire', '')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, histoire)
        
        return bytes(pdf.output())
    except:
        return None

# --- 3. FONCTION POP-UP ---
@st.dialog("📢 ÉVÉNEMENTS AU REFUGE", width="large")
def afficher_evenement(liens):
    liste_ordonnee = liens[::-1]
    for i, url in enumerate(liste_ordonnee):
        if url:
            if "drive.google.com" in url:
                doc_id = url.split('id=')[-1].split('&')[0].split('/')[-1]
                if "/d/" in url: doc_id = url.split('/d/')[1].split('/')[0]
                display_url = f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1000"
            else:
                display_url = url
                
            st.markdown(f"""
                <div style="text-align: center;">
                    <img src="{display_url}" style="max-height: 70vh; max-width: 100%; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0,0,0,0.15);">
                </div>
            """, unsafe_allow_html=True)
            
            if i < len(liste_ordonnee) - 1:
                st.markdown("""<hr style="border: 0; border-top: 2px solid #ddd; margin: 40px auto; width: 60%;">""", unsafe_allow_html=True)
                
    st.markdown("### 🐾 Événements à ne pas manquer !")
    if st.button("Découvrir nos boules de poils à l'adoption ✨", use_container_width=True):
        st.rerun()

# --- 4. STYLE VISUEL ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: transparent !important; }}
    .logo-overlay {{
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 70vw; opacity: 0.05; z-index: -1000; pointer-events: none;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important; border-radius: 15px !important;
        border: 1px solid #ddd !important; box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
        padding: 20px !important; margin-bottom: 20px !important;
    }}
    h1 {{ color: #FF0000 !important; font-weight: 800; }}
    .btn-contact {{ 
        text-decoration: none !important; color: white !important; background-color: #2e7d32; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    .btn-reserve {{ 
        text-decoration: none !important; color: white !important; background-color: #ff8f00; 
        padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }}
    
    /* STYLE SOS SENIOR SANS POINTILLÉS */
    .senior-badge {{
        background-color: #FFF9C4 !important; 
        color: #856404 !important; 
        padding: 10px 15px !important; 
        border-radius: 20px !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        border: none !important; 
        margin: 15px auto !important;
        display: block !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1) !important;
        font-size: 0.9em !important;
        max-width: 90%;
    }}

    [data-testid="stImage"] img {{ 
        border: 8px solid white !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important;
        height: 320px; object-fit: cover;
    }}
    .footer-container {{
        background-color: white; padding: 25px; border-radius: 15px; margin-top: 50px;
        text-align: center; border: 2px solid #FF0000;
    }}
    .aptitude-box {{
        background-color: #f8f9fa; padding: 12px; border-radius: 8px; 
        border-left: 5px solid #FF0000; margin: 15px 0; border: 1px solid #eee;
    }}
    </style>
    <img src="data:image/png;base64,{logo_b64 if logo_b64 else ''}" class="logo-overlay">
    """, unsafe_allow_html=True)

# --- 5. FONCTIONS DATA ---
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

# --- 6. INTERFACE PRINCIPALE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df, df_config = load_all_data(URL_SHEET)

    # Gestion Pop-up
    if not df_config.empty:
        df_config.columns = [str(c).strip() for c in df_config.columns]
        mask = df_config.iloc[:, 0].astype(str).str.contains('Lien_Affiche', na=False, case=False)
        lignes_ev = df_config[mask]
        
        if not lignes_ev.empty and "popup_vue" not in st.session_state:
            liens_valides = []
            for _, r in lignes_ev.iterrows():
                lien = str(r.iloc[1]).strip()
                if lien != "nan" and "http" in lien:
                    liens_valides.append(lien)
            
            if liens_valides:
                st.session_state.popup_vue = True
                afficher_evenement(liens_valides)

    # Catalogue
    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        st.markdown("#### Association Animaux du Grand Dax")

        c1, c2 = st.columns(2)
        with c1:
            choix_espece = st.selectbox("🐶 Espèce", ["Tous"] + sorted(df_dispo['Espèce'].dropna().unique().tolist()))
        with c2:
            choix_age = st.selectbox("🎂 Tranche d'âge", ["Tous", "Moins d'un an (Junior)", "1 à 5 ans (Jeune Adulte)", "5 à 10 ans (Adulte)", "10 ans et plus (Senior)"])

        if st.button("🔄 Actualiser le catalogue"):
            st.cache_data.clear()
            st.rerun()

        st.info("🛡️ **Engagement Santé :** Tous nos protégés sont **vaccinés** et **identifiés** (puce électronique) avant leur départ du refuge pour une adoption responsable.")
        
        df_filtre = df_dispo.copy()
        if choix_espece != "Tous": df_filtre = df_filtre[df_filtre['Espèce'] == choix_espece]
        if choix_age != "Tous": df_filtre = df_filtre[df_filtre['Tranche_Age'] == choix_age]

        st.write(f"**{len(df_filtre)}** protégé(s) à l'adoption")

        for i, row in df_filtre.iterrows():
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 1.2])
                with col_img:
                    u_photo = format_image_url(row['Photo'])
                    st.image(u_photo if u_photo.startswith('http') else "https://via.placeholder.com/300", use_container_width=True)
                    
                    if row['Tranche_Age'] == "10 ans et plus (Senior)":
                        st.markdown('<div class="senior-badge">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)

                with col_txt:
                    st.subheader(row['Nom'])
                    
                    statut = str(row['Statut']).strip()
                    if "Urgence" in statut: st.error(f"🚨 {statut}")
                    elif "Réservé" in statut: st.warning(f"🟠 {statut}")
                    else: st.info(f"🏠 {statut}")

                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")

                    # Aptitudes Visuelles
                    def check_ok(val): return "✅" if str(val).upper() == "TRUE" else "❌"
                    def check_color(val): return "#2e7d32" if str(val).upper() == "TRUE" else "#c62828"

                    apt_html = f"""
                    <div class="aptitude-box">
                        <b style="color:#FF0000; display:block; margin-bottom:8px; font-size:0.9em;">🏠 APTITUDES :</b>
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                            <span style="margin-right: 10px;">🐱</span>
                            <span style="flex-grow: 1; color: #333; font-size: 0.9em;">Ok Chats</span>
                            <span style="color: {check_color(row.get('OK_Chat'))}; font-weight: bold;">{check_ok(row.get('OK_Chat'))}</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                            <span style="margin-right: 10px;">🐶</span>
                            <span style="flex-grow: 1; color: #333; font-size: 0.9em;">Ok Chiens</span>
                            <span style="color: {check_color(row.get('OK_Chien'))}; font-weight: bold;">{check_ok(row.get('OK_Chien'))}</span>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="margin-right: 10px;">🧒</span>
                            <span style="flex-grow: 1; color: #333; font-size: 0.9em;">Ok Enfants</span>
                            <span style="color: {check_color(row.get('OK_Enfant'))}; font-weight: bold;">{check_ok(row.get('OK_Enfant'))}</span>
                        </div>
                    </div>
                    """
                    st.markdown(apt_html, unsafe_allow_html=True)

                    t1, t2 = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t1: st.write(row['Histoire'])
                    with t2: st.write(row['Description'])
                    
                    pdf_data = generer_pdf(row)
                    if pdf_data:
                        st.download_button(
                            label=f"📄 Télécharger la fiche de {row['Nom']}",
                            data=pdf_data,
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            key=f"pdf_btn_{i}",
                            use_container_width=True
                        )

                    if "Réservé" in statut:
                        st.markdown(f'<div class="btn-reserve">🧡 Animal déjà réservé</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)
                        st.markdown(f'<a href="mailto:animauxdugranddax@gmail.com?subject=Adoption de {row["Nom"]}" class="btn-contact">📩 Envoyer un Mail</a>', unsafe_allow_html=True)

# --- 7. PIED DE PAGE ---
    st.markdown("""
        <div class="footer-container">
            <div style="color:#222; font-size:0.95em;">
                <b style="color:#FF0000;">Refuge Médéric - Association Animaux du Grand Dax</b><br>
                182 chemin Lucien Viau, 40990 St-Paul-lès-Dax<br>
                📞 05 58 73 68 82 | ⏰ 14h00 - 18h00 (Mercredi au Dimanche)
            </div>
            <div style="font-size:0.85em; color:#666; margin-top:15px; padding-top:15px; border-top:1px solid #ddd;">
                © 2026 - Application officielle du Refuge Médéric<br>
                🌐 <a href="https://refugedax40.wordpress.com/" target="_blank">Visiter notre site internet</a><br>
                Développé par Firnaeth. avec passion pour nos amis à quatre pattes.
                <div class="version-note">Version 3.2 - PDF & Photo Integration</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erreur de chargement : {e}")
