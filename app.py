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

# --- 2. FONCTION PDF ---
def traduire_bool(valeur):
    return "OUI" if str(valeur).upper() == "TRUE" else "NON"

def format_image_url(url):
    url = str(url).strip()
    if "drive.google.com" in url:
        match = re.search(r"/d/([^/]+)|id=([^&]+)", url)
        if match:
            doc_id = match.group(1) or match.group(2)
            return f"https://drive.google.com/uc?export=view&id={doc_id}"
    return url

def generer_pdf(row):
    try:
        class PDF(FPDF):
            def header(self):
                try:
                    with self.local_context(fill_opacity=0.05):
                        self.image(URL_LOGO_HD, x=45, y=80, w=120)
                except: pass
            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", 'I', 8)
                self.set_text_color(128)
                self.multi_cell(0, 4, "Refuge Médéric - 182 chemin Lucien Viau, 40990 St-Paul-lès-Dax | 05 58 73 68 82\nSite web : https://refugedax40.wordpress.com/", align='C')

        pdf = PDF()
        pdf.add_page()
        
        # Titre
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 15, f"FICHE D'ADOPTION : {str(row['Nom']).upper()}", ln=True, align='C')
        pdf.ln(5)

        # Photo
        y_photo = pdf.get_y()
        try:
            u_photo = format_image_url(row['Photo'])
            resp = requests.get(u_photo, timeout=5)
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            img_buf = BytesIO()
            img.save(img_buf, format="JPEG")
            img_buf.seek(0)
            pdf.image(img_buf, x=60, y=y_photo, w=90)
            pdf.set_y(y_photo + 95)
        except:
            pdf.ln(10)

        # Mention SOS Senior dans le PDF
        if "Senior" in str(row['Tranche_Age']):
            pdf.set_fill_color(255, 249, 196)
            pdf.set_text_color(133, 100, 4)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(0, 10, "✨ SOS SENIOR : Don Libre", ln=True, align='C', fill=True)
            pdf.ln(5)
        else:
            pdf.ln(5)

        # Identité
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"{row['Espèce']} | {row['Sexe']} | {row['Âge']} ans", ln=True, align='C')
        pdf.set_font("Helvetica", 'I', 11)
        pdf.cell(0, 6, f"Type / Race : {row.get('Race', 'Non précisée')}", ln=True, align='C')
        pdf.ln(10)

        # Mise en page Colonnes
        y_start = pdf.get_y()
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(90, 10, "  SON CARACTERE :", ln=0, fill=True)
        pdf.set_x(110)
        pdf.cell(90, 10, "  APTITUDES :", ln=1, fill=True)

        pdf.set_y(y_start + 12)
        pdf.set_font("Helvetica", '', 10)
        pdf.multi_cell(90, 5, str(row.get('Description', 'À venir')).encode('latin-1', 'replace').decode('latin-1'))
        y_car_end = pdf.get_y()
        
        pdf.set_y(y_start + 12)
        pdf.set_x(110)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(90, 7, f"- OK Chats : {traduire_bool(row.get('OK_Chat'))}", ln=1)
        pdf.set_x(110)
        pdf.cell(90, 7, f"- OK Chiens : {traduire_bool(row.get('OK_Chien'))}", ln=1)
        pdf.set_x(110)
        pdf.cell(90, 7, f"- OK Enfants : {traduire_bool(row.get('OK_Enfant'))}", ln=1)
        y_apt_end = pdf.get_y()

        # Histoire
        pdf.set_y(max(y_car_end, y_apt_end) + 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "  SON HISTOIRE :", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_font("Helvetica", '', 10)
        pdf.multi_cell(0, 5, str(row.get('Histoire', 'À venir')).encode('latin-1', 'replace').decode('latin-1'))
        
        return bytes(pdf.output())
    except:
        return None

# --- 3. FONCTION POP-UP ---
@st.dialog("📢 ÉVÉNEMENTS AU REFUGE", width="large")
def afficher_evenement(liens):
    for url in liens[::-1]:
        if url:
            if "drive.google.com" in url:
                doc_id = url.split('id=')[-1].split('&')[0].split('/')[-1]
                if "/d/" in url: doc_id = url.split('/d/')[1].split('/')[0]
                display_url = f"https://drive.google.com/thumbnail?id={doc_id}&sz=w1000"
            else: display_url = url
            st.markdown(f'<div style="text-align: center;"><img src="{display_url}" style="max-height: 70vh; max-width: 100%; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0,0,0,0.15);"></div>', unsafe_allow_html=True)
            st.markdown('<hr style="border: 0; border-top: 2px solid #ddd; margin: 40px auto; width: 60%;">', unsafe_allow_html=True)
    if st.button("Découvrir nos boules de poils ✨", use_container_width=True): st.rerun()

# --- 4. STYLE VISUEL ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: transparent !important; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white !important; border-radius: 15px !important;
        border: 1px solid #ddd !important; box-shadow: 0px 4px 12px rgba(0,0,0,0.08) !important;
        padding: 20px !important; margin-bottom: 20px !important;
    }}
    .btn-contact {{ text-decoration: none !important; color: white !important; background-color: #2e7d32; padding: 12px; border-radius: 8px; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
    .senior-badge {{ background-color: #FFF9C4 !important; color: #856404 !important; padding: 10px 15px !important; border-radius: 20px !important; font-weight: bold !important; text-align: center !important; margin: 15px auto !important; display: block !important; max-width: 90%; }}
    [data-testid="stImage"] img {{ border: 8px solid white !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important; height: 320px; object-fit: cover; }}
    .aptitude-box {{ background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 5px solid #FF0000; margin: 15px 0; border: 1px solid #eee; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. DATA ---
@st.cache_data(ttl=60)
def load_all_data(url):
    try:
        csv_url = url.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        def cat_age(age):
            try:
                a = float(str(age).replace(',', '.'))
                if a >= 10: return "10 ans et plus (Senior)"
                return "Autre"
            except: return "Non précisé"
        df['Tranche_Age'] = df['Âge'].apply(cat_age)
        return df
    except: return pd.DataFrame()

# --- 6. INTERFACE ---
try:
    URL_SHEET = st.secrets["gsheets"]["public_url"]
    df = load_all_data(URL_SHEET)

    if not df.empty:
        df_dispo = df[df['Statut'] != "Adopté"].copy()
        st.title("🐾 Refuge Médéric")
        
        for i, row in df_dispo.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    st.image(format_image_url(row['Photo']), use_container_width=True)
                    if "Senior" in str(row['Tranche_Age']):
                        st.markdown('<div class="senior-badge">✨ SOS SENIOR : Don Libre</div>', unsafe_allow_html=True)
                with col2:
                    st.subheader(row['Nom'])
                    st.write(f"**{row['Espèce']}** | {row['Sexe']} | **{row['Âge']} ans**")
                    st.markdown(f'<div class="aptitude-box"><b>🏠 APTITUDES :</b><br>🐱 Chats : {"✅" if str(row.get("OK_Chat")).upper()=="TRUE" else "❌"}<br>🐶 Chiens : {"✅" if str(row.get("OK_Chien")).upper()=="TRUE" else "❌"}</div>', unsafe_allow_html=True)

                    t1, t2 = st.tabs(["📖 Histoire", "📋 Caractère"])
                    with t1: st.write(row['Histoire'])
                    with t2: st.write(row['Description'])
                    
                    # BOUTON PDF (Sorti de toute condition pour être sûr qu'il s'affiche)
                    pdf_bytes = generer_pdf(row)
                    if pdf_bytes:
                        st.download_button(
                            label=f"📄 Télécharger la fiche de {row['Nom']}",
                            data=pdf_bytes,
                            file_name=f"Fiche_{row['Nom']}.pdf",
                            mime="application/pdf",
                            key=f"pdf_fin_{i}",
                            use_container_width=True
                        )
                    
                    st.markdown(f'<a href="tel:0558736882" class="btn-contact">📞 Appeler le refuge</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erreur : {e}")
