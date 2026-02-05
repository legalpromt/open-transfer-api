import streamlit as st
import requests
import pandas as pd
import base64
from datetime import date
import time

st.set_page_config(page_title="Open Transfer V28", layout="wide", page_icon="🦁")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stTextInput > label {font-size:16px; font-weight:bold; color:#1a237e;}
    div[data-testid="stImage"] {border: 1px solid #ddd; border-radius: 12px; padding: 10px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS VIP (INFALIBLE) ---
# Estos equipos cargan al instante, sin depender de internet/API.
VIP_CLUBS = {
    "chelsea": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/200px-Chelsea_FC.svg.png", "iso": "ENG"},
    "chelsea fc": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/200px-Chelsea_FC.svg.png", "iso": "ENG"},
    "manchester city": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/200px-Manchester_City_FC_badge.svg.png", "iso": "ENG"},
    "man city": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/200px-Manchester_City_FC_badge.svg.png", "iso": "ENG"},
    "liverpool": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/Liverpool_FC.svg/200px-Liverpool_FC.svg.png", "iso": "ENG"},
    "arsenal": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Arsenal_FC.svg/200px-Arsenal_FC.svg.png", "iso": "ENG"},
    "manchester united": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7a/Manchester_United_FC_crest.svg/200px-Manchester_United_FC_crest.svg.png", "iso": "ENG"},
    "real madrid": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/200px-Real_Madrid_CF.svg.png", "iso": "ESP"},
    "barcelona": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/200px-FC_Barcelona_%28crest%29.svg.png", "iso": "ESP"},
    "fc barcelona": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/200px-FC_Barcelona_%28crest%29.svg.png", "iso": "ESP"},
    "atletico madrid": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Atletico_Madrid_2017_logo.svg/200px-Atletico_Madrid_2017_logo.svg.png", "iso": "ESP"},
    "bayern munich": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg/200px-FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg.png", "iso": "DEU"},
    "psg": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/200px-Paris_Saint-Germain_F.C..svg.png", "iso": "FRA"},
    "juventus": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Juventus_FC_2017_icon_%28black%29.svg/200px-Juventus_FC_2017_icon_%28black%29.svg.png", "iso": "ITA"},
    "inter": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/FC_Internazionale_Milano_2021.svg/200px-FC_Internazionale_Milano_2021.svg.png", "iso": "ITA"},
    "milan": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Logo_of_AC_Milan.svg/200px-Logo_of_AC_Milan.svg.png", "iso": "ITA"},
    "benfica": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/SL_Benfica_logo.svg/200px-SL_Benfica_logo.svg.png", "iso": "PRT"},
    "porto": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/FC_Porto.svg/200px-FC_Porto.svg.png", "iso": "PRT"},
    "boca juniors": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Club_Atl%C3%A9tico_Boca_Juniors_logo.svg/200px-Club_Atl%C3%A9tico_Boca_Juniors_logo.svg.png", "iso": "ARG"},
    "boca": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Club_Atl%C3%A9tico_Boca_Juniors_logo.svg/200px-Club_Atl%C3%A9tico_Boca_Juniors_logo.svg.png", "iso": "ARG"},
    "river plate": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/200px-Escudo_del_C_A_River_Plate.svg.png", "iso": "ARG"},
    "river": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/200px-Escudo_del_C_A_River_Plate.svg.png", "iso": "ARG"},
    "flamengo": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Flamengo_braz_logo.svg/200px-Flamengo_braz_logo.svg.png", "iso": "BRA"},
    "palmeiras": {"logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Palmeiras_logo.svg/200px-Palmeiras_logo.svg.png", "iso": "BRA"},
    "inter miami": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5c/Inter_Miami_CF_logo.svg/200px-Inter_Miami_CF_logo.svg.png", "iso": "USA"},
    "al nassr": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/8/86/Al_Nassr_FC_Logo_%282020%29.svg/200px-Al_Nassr_FC_Logo_%282020%29.svg.png", "iso": "SAU"}
}

# --- GESTIÓN DE ESTADO ---
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []
if 'logo_url' not in st.session_state: st.session_state['logo_url'] = ""
if 'club_iso' not in st.session_state: st.session_state['club_iso'] = "ENG"
if 'last_search' not in st.session_state: st.session_state['last_search'] = ""

st.title("Open Transfer V28: Hybrid Intelligence 🦁⚡")
st.markdown("---")

# --- MOTOR HÍBRIDO ---
def buscar_escudo_inteligente(nombre):
    if not nombre: return None
    key = nombre.lower().strip()
    
    # 1. BÚSQUEDA VIP (INSTANTÁNEA)
    if key in VIP_CLUBS:
        return VIP_CLUBS[key]
        
    # 2. BÚSQUEDA API GLOBAL (SI FALLA LA VIP)
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={nombre}"
        r = requests.get(url, timeout=3)
        data = r.json()
        if data and data.get('teams'):
            team = data['teams'][0]
            return {"logo": team['strTeamBadge'], "iso": "UNK"} # API no siempre da ISO fiable
    except:
        pass
    
    return None

# --- INTERFAZ ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("👤 Ficha Jugador")
    with st.container(border=True):
        nombre = st.text_input("Nombre Completo", "Enzo Fernandez")
        c1, c2 = st.columns(2)
        with c1: nac = st.text_input("Nacionalidad", "ARG")
        with c2: fnac = st.date_input("Fecha Nacimiento", date(2001, 1, 17))

with col2:
    st.subheader("🛡️ Club Comprador")
    with st.container(border=True):
        # BUSCADOR
        busqueda = st.text_input("Nombre del Club", placeholder="Escribe: Chelsea, Real Madrid, Boca...")
        
        # PROCESADOR AUTOMÁTICO
        if busqueda and busqueda != st.session_state['last_search']:
            with st.spinner("Localizando club..."):
                resultado = buscar_escudo_inteligente(busqueda)
                if resultado:
                    st.session_state['logo_url'] = resultado['logo']
                    if resultado['iso'] != "UNK": st.session_state['club_iso'] = resultado['iso']
                    st.session_state['last_search'] = busqueda
                else:
                    st.warning("Club no detectado automáticamente. Inserte link manual.")
        
        # VISUALIZACIÓN
        ci, cd = st.columns([1, 3])
        with ci:
            if st.session_state['logo_url']:
                st.image(st.session_state['logo_url'], width=100)
            else:
                st.write("❌")
        
        with cd:
            logo_final = st.text_input("URL Logo", value=st.session_state['logo_url'])
            pais_iso = st.text_input("País (ISO)", value=st.session_state['club_iso'])
            cat_fifa = st.selectbox("Categoría FIFA", ["I", "II", "III", "IV"])

    st.write("")
    with st.container(border=True):
        st.write("💰 **Transferencia**")
        cm, cf = st.columns(2)
        with cm: monto = st.number_input("Monto (€)", value=121000000.0)
        with cf: ftrans = st.date_input("Fecha", date(2023, 1, 31))

# --- PASAPORTE ---
st.markdown("---")
st.subheader("📚 Pasaporte Deportivo")
uploaded_file = st.file_uploader("Subir Excel/CSV", type=['csv', 'xlsx'])
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.lower().str.strip() 
        for col in ['inicio', 'fin']:
            if col in df.columns: df[col] = df[col].astype(str)
        st.session_state['pasaporte_data'] = df.to_dict('records')
        st.success(f"{len(df)} registros cargados.")
    except Exception as e: st.error(str(e))

if st.session_state['pasaporte_data']:
    with st.expander("Ver Datos"): st.dataframe(pd.DataFrame(st.session_state['pasaporte_data']))

# --- BOTÓN FINAL ---
st.markdown("---")
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    if st.button("GENERAR AUDITORÍA FINAL 🚀", type="primary", use_container_width=True):
        origen = {"nombre": "Desconocido", "pais_asociacion": "UNK"}
        if st.session_state['pasaporte_data']:
            last = st.session_state['pasaporte_data'][-1]
            origen = {"nombre": last.get('club'), "pais_asociacion": last.get('pais')}

        payload = {
            "meta": {"version": "V28-HYBRID", "id_expediente": f"EXP-{str(time.time())[-4:]}"},
            "jugador": {"nombre_completo": nombre, "fecha_nacimiento": str(fnac), "nacionalidad": nac},
            "acuerdo_transferencia": {
                "club_destino": {"nombre": busqueda or "Destino", "pais_asociacion": pais_iso, "categoria_fifa": cat_fifa, "logo": logo_final},
                "club_origen": origen,
                "fecha_transferencia": str(ftrans),
                "monto_fijo_total": monto
            },
            "historial_formacion": st.session_state['pasaporte_data']
        }
        
        headers = {"X-API-Key": "sk_live_rayovallecano_2026"}
        with st.spinner("Procesando..."):
            try:
                r = requests.post("https://open-transfer-api.onrender.com/validar-operacion", json=payload, headers=headers)
                if r.status_code == 200:
                    st.balloons()
                    b64 = base64.b64encode(r.content).decode()
                    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900"></iframe>', unsafe_allow_html=True)
                else: st.error(r.text)
            except Exception as e: st.error(f"Error: {e}")