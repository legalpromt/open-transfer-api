import streamlit as st
import requests
import pandas as pd
import base64
from datetime import date

st.set_page_config(page_title="Open Transfer V20", layout="wide")
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []

st.title("Open Transfer V20: Smart Selectors 🧠⚽")

# --- BASE DE DATOS INTELIGENTE (PAÍS -> LIGA -> CATEGORÍA) ---
DB_FUTBOL = {
    "Inglaterra (ENG)": {
        "iso": "ENG",
        "ligas": {
            "Premier League": {"cat": "I", "clubes": ["Chelsea FC", "Manchester City", "Manchester United", "Liverpool", "Arsenal"]},
            "EFL Championship": {"cat": "II", "clubes": ["Leeds United", "Leicester City", "Southampton"]}
        }
    },
    "España (ESP)": {
        "iso": "ESP",
        "ligas": {
            "La Liga (1ª División)": {"cat": "I", "clubes": ["Real Madrid", "FC Barcelona", "Atlético de Madrid", "Sevilla FC"]},
            "La Liga 2": {"cat": "II", "clubes": ["RCD Espanyol", "Real Zaragoza"]}
        }
    },
    "Portugal (PRT)": {
        "iso": "PRT",
        "ligas": {
            "Primeira Liga": {"cat": "I", "clubes": ["Benfica", "FC Porto", "Sporting CP", "Braga"]}
        }
    },
    "Francia (FRA)": {
        "iso": "FRA",
        "ligas": {
            "Ligue 1": {"cat": "I", "clubes": ["PSG", "Monaco", "Lyon", "Marseille"]}
        }
    },
    "Italia (ITA)": {
        "iso": "ITA",
        "ligas": {
            "Serie A": {"cat": "I", "clubes": ["Juventus", "AC Milan", "Inter", "Napoli", "Roma"]}
        }
    },
    "Alemania (DEU)": {
        "iso": "DEU",
        "ligas": {
            "Bundesliga": {"cat": "I", "clubes": ["Bayern Munich", "Bayer Leverkusen", "Dortmund"]}
        }
    },
    "Argentina (ARG)": {
        "iso": "ARG",
        "ligas": {
            "Liga Profesional": {"cat": "II", "clubes": ["River Plate", "Boca Juniors", "Racing", "Independiente", "Defensa y Justicia"]}
        }
    },
    "Estados Unidos (USA)": {
        "iso": "USA",
        "ligas": {
            "MLS": {"cat": "II", "clubes": ["Inter Miami", "LA Galaxy", "Atlanta United"]}
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
    st.subheader("✈️ Datos de la Transferencia (Destino)")
    
    # 1. SELECTOR DE PAÍS
    pais_seleccionado = st.selectbox("Selecciona País Destino", list(DB_FUTBOL.keys()))
    
    if pais_seleccionado == "Otro / Manual":
        # Modo Manual si no está en la lista
        pais_iso = st.text_input("Código País (ISO 3 letras)", "BRA")
        club_nombre = st.text_input("Nombre Club", "Flamengo")
        cat_fifa = st.selectbox("Categoría FIFA", ["I", "II", "III", "IV"])
    else:
        # Modo Automático
        datos_pais = DB_FUTBOL[pais_seleccionado]
        pais_iso = datos_pais["iso"]
        
        # 2. SELECTOR DE LIGA
        liga_seleccionada = st.selectbox("Selecciona Liga", list(datos_pais["ligas"].keys()))
        datos_liga = datos_pais["ligas"][liga_seleccionada]
        
        # 3. AUTO-DETECTAR CATEGORÍA
        cat_fifa = datos_liga["cat"]
        st.info(f"✅ Categoría Detectada: {cat_fifa} ({liga_seleccionada})")
        
        # 4. SELECTOR DE CLUB
        lista_clubes = datos_liga["clubes"] + ["Otro (Escribir manual)"]
        club_elegido = st.selectbox("Selecciona Club", lista_clubes)
        
        if club_elegido == "Otro (Escribir manual)":
            club_nombre = st.text_input("Escribe el nombre del club")
        else:
            club_nombre = club_elegido

    st.markdown("---")
    monto = st.number_input("Monto Transferencia (€)", value=121000000.0)
    fecha_trans = st.date_input("Fecha Operación", date(2023, 1, 31), min_value=date(1900,1,1))

# --- PASAPORTE ---
st.subheader("📚 Pasaporte Deportivo (Excel)")
uploaded_file = st.file_uploader("Sube Excel/CSV", type=['csv', 'xlsx'])

if uploaded_file and st.button("Cargar Historial"):
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        
        df.columns = df.columns.str.lower().str.strip() # Limpieza de columnas
        
        # Validación mínima
        if 'club' in df.columns and 'inicio' in df.columns:
            # Convertir fechas a str
            for col in ['inicio', 'fin']:
                if col in df.columns: df[col] = df[col].astype(str)
            
            st.session_state['pasaporte_data'] = df.to_dict('records')
            st.success(f"Cargados {len(df)} registros.")
            st.rerun()
        else:
            st.error("El Excel debe tener columnas: Club, Inicio, Fin")
    except Exception as e: st.error(str(e))

if st.session_state['pasaporte_data']:
    st.dataframe(pd.DataFrame(st.session_state['pasaporte_data']), use_container_width=True)
    if st.button("Borrar Tabla"): st.session_state['pasaporte_data'] = []; st.rerun()

# --- GENERAR ---
if st.button("GENERAR INFORME V20 📄"):
    # AUTODETECCIÓN DEL ORIGEN PARA EVITAR ERROR 422
    # Si hay historial, cogemos el último club como Origen
    club_origen_auto = {"nombre": "Desconocido", "pais_asociacion": "UNK"}
    
    if st.session_state['pasaporte_data']:
        ultimo = st.session_state['pasaporte_data'][-1]
        club_origen_auto = {
            "nombre": ultimo.get('club', 'Desconocido'),
            "pais_asociacion": ultimo.get('pais', 'UNK')
        }

    payload = {
        "meta": {"version": "V20-SMART", "id_expediente": f"EXP-{nombre.split()[0]}"},
        "jugador": {"nombre_completo": nombre, "fecha_nacimiento": str(fecha_nac), "nacionalidad": nacionalidad},
        "acuerdo_transferencia": {
            "club_destino": {"nombre": club_nombre, "pais_asociacion": pais_iso, "categoria_fifa": cat_fifa},
            "club_origen": club_origen_auto, # <--- AQUÍ ESTÁ EL ARREGLO DEL 422
            "fecha_transferencia": str(fecha_trans),
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
                st.download_button("Descargar PDF", r.content, f"Informe_{nombre.replace(' ','_')}.pdf")
                b64 = base64.b64encode(r.content).decode()
                st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
            else:
                st.error(f"Error ({r.status_code}): {r.text}")
        except Exception as e: st.error(f"Conexión: {e}")