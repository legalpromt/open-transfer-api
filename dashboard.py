import streamlit as st
import requests
import pandas as pd
import base64
from datetime import date
import time

st.set_page_config(page_title="Open Transfer V27", layout="wide", page_icon="🌍")

# --- ESTILOS CSS PRO ---
st.markdown("""
    <style>
    .stTextInput > label {font-size:16px; font-weight:bold; color:#1a237e;}
    .block-container {padding-top: 2rem;}
    div[data-testid="stImage"] {border: 1px solid #e0e0e0; border-radius: 10px; padding: 10px; background: white;}
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []
if 'logo_url' not in st.session_state: st.session_state['logo_url'] = ""
if 'club_name_confirmed' not in st.session_state: st.session_state['club_name_confirmed'] = ""

st.title("Open Transfer V27: Global Database 🌍⚽")
st.markdown("Acceso a base de datos federativa mundial (FIFA/TheSportsDB API)")
st.markdown("---")

# --- MOTOR DE BÚSQUEDA GLOBAL (API) ---
@st.cache_data(show_spinner=False) # Guardamos en caché para que sea rápido si repites equipo
def buscar_equipo_global(termino_busqueda):
    if not termino_busqueda or len(termino_busqueda) < 2: return None
    
    # 1. Intentamos búsqueda exacta
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={termino_busqueda}"
        r = requests.get(url, timeout=4)
        data = r.json()
        
        if data and data.get('teams'):
            # Devolvemos el primer resultado que tenga escudo
            team = data['teams'][0]
            return {
                "nombre": team['strTeam'],
                "logo": team['strTeamBadge'],
                "liga": team['strLeague'],
                "pais": team['strCountry'] or "Internacional"
            }
    except:
        pass
    return None

# --- INTERFAZ ---
col_izq, col_der = st.columns([1, 1])

with col_izq:
    st.subheader("👤 Ficha del Jugador")
    with st.container(border=True):
        nombre = st.text_input("Nombre del Jugador", "Enzo Fernandez")
        col_nac, col_fecha = st.columns(2)
        with col_nac: nacionalidad = st.text_input("Nacionalidad", "ARG")
        with col_fecha: fecha_nac = st.date_input("Fecha Nacimiento", date(2001, 1, 17))

with col_der:
    st.subheader("🛡️ Club Destino (Buscador Global)")
    
    with st.container(border=True):
        # BUSCADOR TIPO GOOGLE
        busqueda = st.text_input("🔍 Buscar Equipo (Ej: Chelsea, Boca, Al-Hilal...)", placeholder="Escribe el nombre del club...")
        
        # LÓGICA DE BÚSQUEDA AUTOMÁTICA
        if busqueda and busqueda != st.session_state['club_name_confirmed']:
            with st.spinner(f"Conectando con base de datos global para '{busqueda}'..."):
                resultado = buscar_equipo_global(busqueda)
                
                if resultado:
                    st.session_state['logo_url'] = resultado['logo']
                    st.session_state['club_name_confirmed'] = busqueda # Evitamos rebucsar
                    st.success(f"✅ Localizado: {resultado['nombre']} ({resultado['pais']})")
                else:
                    st.session_state['logo_url'] = ""
                    st.warning("No encontrado en la base global. Ingrese URL manual abajo.")

        # VISTA PREVIA Y DATOS
        c_img, c_datos = st.columns([1, 3])
        with c_img:
            if st.session_state['logo_url']:
                st.image(st.session_state['logo_url'], width=100)
            else:
                st.write("🚫")
        
        with c_datos:
            # Permitimos editar el link si el usuario quiere uno diferente
            logo_final = st.text_input("URL Escudo (Link)", value=st.session_state['logo_url'])
            
            # Datos adicionales
            pais_iso = st.text_input("País Asociación (ISO)", "ENG" if "Chelsea" in busqueda else "FIFA")
            cat_fifa = st.selectbox("Categoría FIFA", ["I", "II", "III", "IV"])

    st.write("")
    with st.container(border=True):
        st.write("💰 **Condiciones Financieras**")
        col_m, col_f = st.columns(2)
        with col_m: monto = st.number_input("Monto Fijo (€)", value=121000000.0, format="%.2f")
        with col_f: fecha_trans = st.date_input("Fecha Firma", date(2023, 1, 31))

# --- PASAPORTE ---
st.markdown("---")
st.subheader("📚 Historial Formativo (Pasaporte)")

uploaded_file = st.file_uploader("Arrastra aquí el Excel/CSV del TMS o Transfermarkt", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.lower().str.strip() 
        for col in ['inicio', 'fin']:
            if col in df.columns: df[col] = df[col].astype(str)
        
        st.session_state['pasaporte_data'] = df.to_dict('records')
        st.success(f"✅ Pasaporte cargado: {len(df)} registros procesados.")
    except Exception as e: st.error(f"Error de lectura: {e}")

if st.session_state['pasaporte_data']:
    with st.expander("Ver Datos del Pasaporte", expanded=False):
        st.dataframe(pd.DataFrame(st.session_state['pasaporte_data']), use_container_width=True)

# --- BOTÓN DE ACCIÓN ---
st.markdown("---")
col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
with col_b2:
    if st.button("🚀 AUDITAR OPERACIÓN Y GENERAR INFORME", type="primary", use_container_width=True):
        # Lógica de Origen
        origen_data = {"nombre": "Desconocido", "pais_asociacion": "UNK"}
        if st.session_state['pasaporte_data']:
            ultimo = st.session_state['pasaporte_data'][-1]
            origen_data = {"nombre": ultimo.get('club'), "pais_asociacion": ultimo.get('pais')}

        payload = {
            "meta": {"version": "V27-GLOBAL", "id_expediente": f"EXP-{str(time.time())[-5:]}"},
            "jugador": {"nombre_completo": nombre, "fecha_nacimiento": str(fecha_nac), "nacionalidad": nacionalidad},
            "acuerdo_transferencia": {
                "club_destino": {
                    "nombre": busqueda if busqueda else "Club Destino", 
                    "pais_asociacion": pais_iso, 
                    "categoria_fifa": cat_fifa,
                    "logo": logo_final
                },
                "club_origen": origen_data,
                "fecha_transferencia": str(fecha_trans),
                "monto_fijo_total": monto
            },
            "historial_formacion": st.session_state['pasaporte_data']
        }
        
        headers = {"X-API-Key": "sk_live_rayovallecano_2026"}
        
        with st.spinner("Conectando con el Servidor Pericial..."):
            try:
                r = requests.post("https://open-transfer-api.onrender.com/validar-operacion", json=payload, headers=headers)
                if r.status_code == 200:
                    st.balloons()
                    st.download_button("📥 DESCARGAR INFORME OFICIAL (PDF)", r.content, f"Audit_{nombre}.pdf", "application/pdf")
                    
                    # Visor
                    b64 = base64.b64encode(r.content).decode()
                    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900" style="border: 1px solid #ccc; border-radius: 5px;"></iframe>', unsafe_allow_html=True)
                else:
                    st.error(f"Error del Servidor: {r.text}")
            except Exception as e: st.error(f"Error de conexión: {e}")