import streamlit as st
import requests
import pandas as pd
import base64
from datetime import date
import time

st.set_page_config(page_title="Open Transfer V32", layout="wide", page_icon="🌍")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stTextInput > label {font-size:14px; font-weight:bold; color:#1565C0;}
    div[data-testid="stImage"] {border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# --- 1. BASE DE DATOS LOCAL (SOLO PARA VELOCIDAD EN DEMOS) ---
# Estos cargan al instante. Para el resto, usaremos la API.
VIP_CACHE = {
    "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg",
    "Barcelona": "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Man City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Boca Juniors": "https://upload.wikimedia.org/wikipedia/commons/4/41/Club_Atl%C3%A9tico_Boca_Juniors_logo.svg",
    "River Plate": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Escudo_del_C_A_River_Plate.svg"
}

# --- 2. MOTOR DE BÚSQUEDA INTELIGENTE (LA SOLUCIÓN) ---
def buscar_logo_automatico(nombre_club):
    """
    Busca el logo en la base de datos mundial TheSportsDB.
    """
    if not nombre_club: return ""

    # A. Revisar Caché VIP (Instantáneo)
    if nombre_club in VIP_CACHE:
        url = VIP_CACHE[nombre_club]
        # Truco para convertir SVG a PNG para el PDF
        if url.endswith(".svg"): return url + "/200px-" + url.split("/")[-1] + ".png"
        return url

    # B. Buscar en API Mundial (TheSportsDB)
    try:
        # Limpiamos el nombre (Ej: "Valencia CF" -> "Valencia") para mejorar la búsqueda
        clean_name = nombre_club.replace(" FC", "").replace(" CF", "").replace(" UD", "")
        
        url_api = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={clean_name}"
        r = requests.get(url_api, timeout=3)
        data = r.json()
        
        if data and data['teams']:
            # Devolvemos el escudo del primer resultado encontrado
            return data['teams'][0]['strTeamBadge']
    except Exception as e:
        print(f"Error API: {e}")
        pass

    return "" # Si no encuentra nada

# --- GESTIÓN DE ESTADO ---
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []
if 'logo_autodetected' not in st.session_state: st.session_state['logo_autodetected'] = ""
if 'last_search_term' not in st.session_state: st.session_state['last_search_term'] = ""

st.title("Open Transfer V32: Auto-Discovery 🌍🔎")
st.markdown("---")

# --- INTERFAZ ---
col_izq, col_der = st.columns([1, 1.3])

with col_izq:
    st.subheader("👤 Ficha Jugador")
    with st.container(border=True):
        nombre = st.text_input("Nombre", "Enzo Fernandez")
        c1, c2 = st.columns(2)
        with c1: nac = st.text_input("Nacionalidad", "ARG")
        with c2: fnac = st.date_input("Nacimiento", date(2001, 1, 17))

with col_der:
    st.subheader("🛡️ Club Destino (Buscador Global)")
    with st.container(border=True):
        # CAMPO DE BÚSQUEDA LIBRE
        club_input = st.text_input("Escribe el nombre del Club (Ej: 'Galatasaray', 'Luton', 'Flamengo')", placeholder="Nombre del equipo...")
        
        # LOGICA DE BÚSQUEDA AUTOMÁTICA
        if club_input and club_input != st.session_state['last_search_term']:
            with st.spinner(f"🔍 Buscando escudo oficial de '{club_input}' en la base de datos mundial..."):
                found_url = buscar_logo_automatico(club_input)
                st.session_state['logo_autodetected'] = found_url
                st.session_state['last_search_term'] = club_input
        
        # VISUALIZACIÓN
        logo_final_url = st.session_state['logo_autodetected']

        ci, cd = st.columns([1, 3])
        with ci:
            if logo_final_url: st.image(logo_final_url, width=90)
            else: st.warning("Sin Logo")
        
        with cd:
            # Permitimos que el usuario lo cambie si la API se equivoca
            url_editable = st.text_input("URL Escudo (Detectado)", value=logo_final_url)
            
            # Datos Financieros
            iso_input = st.text_input("País (ISO)", "ENG" if "Chelsea" in club_input else "FIFA")
            cat_fifa = st.selectbox("Categoría FIFA", ["I", "II", "III", "IV"])

    st.write("")
    with st.container(border=True):
        st.write("💰 **Transferencia**")
        c_m, c_f = st.columns(2)
        with c_m: monto = st.number_input("Monto (€)", value=121000000.0)
        with c_f: ftrans = st.date_input("Fecha", date(2023, 1, 31))

# --- PASAPORTE ---
st.markdown("---")
st.subheader("📚 Historial Formativo")
uploaded_file = st.file_uploader("Sube Excel", type=['csv', 'xlsx'])
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.lower().str.strip() 
        for col in ['inicio', 'fin']:
            if col in df.columns: df[col] = df[col].astype(str)
        st.session_state['pasaporte_data'] = df.to_dict('records')
    except: pass

if st.session_state['pasaporte_data']:
    with st.expander("Ver Datos"): st.dataframe(pd.DataFrame(st.session_state['pasaporte_data']))

# --- GENERAR ---
st.markdown("---")
if st.button("GENERAR PDF OFICIAL 🚀", type="primary", use_container_width=True):
    origen = {"nombre": "Desconocido", "pais_asociacion": "UNK"}
    if st.session_state['pasaporte_data']:
        last = st.session_state['pasaporte_data'][-1]
        origen = {"nombre": last.get('club'), "pais_asociacion": last.get('pais')}

    payload = {
        "meta": {"version": "V32-AUTO-API", "id_expediente": f"EXP-{str(time.time())[-4:]}"},
        "jugador": {"nombre_completo": nombre, "fecha_nacimiento": str(fnac), "nacionalidad": nac},
        "acuerdo_transferencia": {
            "club_destino": {"nombre": club_input, "pais_asociacion": iso_input, "categoria_fifa": cat_fifa, "logo": url_editable},
            "club_origen": origen,
            "fecha_transferencia": str(ftrans),
            "monto_fijo_total": monto
        },
        "historial_formacion": st.session_state['pasaporte_data']
    }
    
    headers = {"X-API-Key": "sk_live_rayovallecano_2026"}
    with st.spinner("Generando..."):
        try:
            r = requests.post("https://open-transfer-api.onrender.com/validar-operacion", json=payload, headers=headers)
            if r.status_code == 200:
                st.balloons()
                b64 = base64.b64encode(r.content).decode()
                st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900"></iframe>', unsafe_allow_html=True)
            else: st.error(r.text)
        except Exception as e: st.error(f"Error: {e}")