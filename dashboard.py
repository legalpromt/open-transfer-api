import streamlit as st
import requests
import pandas as pd
import base64
from datetime import date

st.set_page_config(page_title="Open Transfer V25", layout="wide")
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []

st.title("Open Transfer V25: Auto-Logo Discovery 🌍⚽")

# --- FUNCIÓN DE BÚSQUEDA AUTOMÁTICA (API) ---
def buscar_escudo_online(nombre_equipo):
    """Busca el logo en TheSportsDB (Base de datos abierta)"""
    if not nombre_equipo or len(nombre_equipo) < 3: return None
    
    try:
        # API Pública gratuita (Test Key: 3)
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={nombre_equipo}"
        r = requests.get(url, timeout=3)
        data = r.json()
        
        if data and data['teams']:
            # Devolvemos el escudo del primer resultado
            return data['teams'][0]['strTeamBadge']
    except:
        return None
    return None

# --- BASE DE DATOS LOCAL (PARA ATAJOS RÁPIDOS) ---
# Usamos esto para categorías y países, pero el logo lo buscaremos online
DB_FUTBOL = {
    "Inglaterra (ENG)": {
        "iso": "ENG",
        "ligas": {
            "Premier League": {"cat": "I", "clubes": ["Chelsea", "Manchester City", "Arsenal", "Liverpool", "Manchester United"]}
        }
    },
    "España (ESP)": {
        "iso": "ESP",
        "ligas": {
            "La Liga": {"cat": "I", "clubes": ["Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla"]}
        }
    },
    "Argentina (ARG)": {
        "iso": "ARG",
        "ligas": {
            "Liga Profesional": {"cat": "II", "clubes": ["River Plate", "Boca Juniors", "Racing Club", "Independiente"]}
        }
    },
    "Brasil (BRA)": {
        "iso": "BRA",
        "ligas": {
            "Brasileirao": {"cat": "II", "clubes": ["Flamengo", "Palmeiras", "Santos", "Sao Paulo"]}
        }
    },
    "Otro / Manual": { "iso": "", "ligas": {} }
}

# --- INTERFAZ ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("👤 Datos del Jugador")
    nombre = st.text_input("Nombre Completo", "Enzo Fernandez")
    nacionalidad = st.text_input("Nacionalidad", "ARG")
    fecha_nac = st.date_input("Fecha Nacimiento", date(2001, 1, 17), min_value=date(1900,1,1))

with col2:
    st.subheader("✈️ Datos de la Transferencia")
    
    # Variables de estado
    club_nombre = ""
    logo_detectado = ""
    
    pais_seleccionado = st.selectbox("País Destino", list(DB_FUTBOL.keys()))
    
    if pais_seleccionado == "Otro / Manual":
        pais_iso = st.text_input("Código ISO", "ITA")
        club_nombre = st.text_input("Nombre Club", "Juventus")
        cat_fifa = st.selectbox("Categoría FIFA", ["I", "II", "III", "IV"])
    else:
        datos_pais = DB_FUTBOL[pais_seleccionado]
        pais_iso = datos_pais["iso"]
        liga_seleccionada = st.selectbox("Liga", list(datos_pais["ligas"].keys()))
        datos_liga = datos_pais["ligas"][liga_seleccionada]
        cat_fifa = datos_liga["cat"]
        
        nombres_clubes = datos_liga["clubes"] + ["Otro"]
        club_elegido = st.selectbox("Club", nombres_clubes)
        
        if club_elegido == "Otro":
            club_nombre = st.text_input("Escribe el nombre del club")
        else:
            club_nombre = club_elegido

    # --- ZONA DE MAGIA AUTOMÁTICA ---
    # Si hay un nombre de club, intentamos buscar su logo
    if club_nombre:
        with st.spinner(f"Buscando escudo de {club_nombre}..."):
            logo_detectado = buscar_escudo_online(club_nombre)
    
    st.markdown("### 🛡️ Escudo Oficial")
    col_img, col_url = st.columns([1, 3])
    
    with col_url:
        # El usuario puede ver la URL detectada o cambiarla si quiere
        logo_final = st.text_input("URL Escudo", value=logo_detectado if logo_detectado else "")
    
    with col_img:
        if logo_final:
            st.image(logo_final, width=80)
        else:
            st.warning("Sin logo")

    st.markdown("---")
    monto = st.number_input("Monto (€)", value=121000000.0)
    fecha_trans = st.date_input("Fecha", date(2023, 1, 31))

# --- PASAPORTE ---
st.subheader("📚 Pasaporte Deportivo")
uploaded_file = st.file_uploader("Sube Excel/CSV", type=['csv', 'xlsx'])

if uploaded_file and st.button("Cargar Historial"):
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.lower().str.strip() 
        for col in ['inicio', 'fin']:
            if col in df.columns: df[col] = df[col].astype(str)
        st.session_state['pasaporte_data'] = df.to_dict('records')
        st.success(f"Cargados {len(df)} registros.")
        st.rerun()
    except Exception as e: st.error(str(e))

if st.session_state['pasaporte_data']:
    st.dataframe(pd.DataFrame(st.session_state['pasaporte_data']), use_container_width=True)

# --- GENERAR ---
if st.button("GENERAR INFORME V25 📄"):
    club_origen_auto = {"nombre": "Desconocido", "pais_asociacion": "UNK"}
    if st.session_state['pasaporte_data']:
        ultimo = st.session_state['pasaporte_data'][-1]
        club_origen_auto = {"nombre": ultimo.get('club'), "pais_asociacion": ultimo.get('pais')}

    payload = {
        "meta": {"version": "V25-AUTO", "id_expediente": f"EXP-{nombre.split()[0]}"},
        "jugador": {"nombre_completo": nombre, "fecha_nacimiento": str(fecha_nac), "nacionalidad": nacionalidad},
        "acuerdo_transferencia": {
            "club_destino": {
                "nombre": club_nombre, 
                "pais_asociacion": pais_iso, 
                "categoria_fifa": cat_fifa,
                "logo": logo_final # Enviamos el logo automático
            },
            "club_origen": club_origen_auto,
            "fecha_transferencia": str(fecha_trans),
            "monto_fijo_total": monto
        },
        "historial_formacion": st.session_state['pasaporte_data']
    }
    
    headers = {"X-API-Key": "sk_live_rayovallecano_2026"}
    
    with st.spinner("Generando Informe..."):
        try:
            r = requests.post("https://open-transfer-api.onrender.com/validar-operacion", json=payload, headers=headers)
            if r.status_code == 200:
                st.balloons()
                st.download_button("Descargar PDF", r.content, f"Informe_{nombre.replace(' ','_')}.pdf")
                b64 = base64.b64encode(r.content).decode()
                st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
            else:
                st.error(f"Error ({r.status_code}): {r.text}")
        except Exception as e: st.error(f"Conexión: {e}")