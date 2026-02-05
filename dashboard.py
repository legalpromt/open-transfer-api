import streamlit as st
import requests
import pandas as pd
import base64
from datetime import date

st.set_page_config(page_title="Open Transfer V24", layout="wide")
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []

st.title("Open Transfer V24: Official Branding 🛡️")

# --- BASE DE DATOS LIMITADA (DEMO) ---
# Nota: Para tener "todos los equipos del mundo" automáticamente, necesitarías pagar una API como 'API-Football'.
# Solución Pro: Usamos esta lista para los grandes y el campo "URL Manual" para el resto.
DB_FUTBOL = {
    "Inglaterra (ENG)": {
        "iso": "ENG",
        "ligas": {
            "Premier League": {
                "cat": "I", 
                "clubes": [
                    {"nombre": "Chelsea FC", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/200px-Chelsea_FC.svg.png"},
                    {"nombre": "Man City", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/200px-Manchester_City_FC_badge.svg.png"},
                    {"nombre": "Liverpool", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/Liverpool_FC.svg/200px-Liverpool_FC.svg.png"}
                ]
            }
        }
    },
    "España (ESP)": {
        "iso": "ESP",
        "ligas": {
            "La Liga": {
                "cat": "I", 
                "clubes": [
                    {"nombre": "Real Madrid", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/200px-Real_Madrid_CF.svg.png"},
                    {"nombre": "FC Barcelona", "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/200px-FC_Barcelona_%28crest%29.svg.png"}
                ]
            }
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
    
    # Variables por defecto
    logo_auto = "" 
    club_nombre = ""
    
    pais_seleccionado = st.selectbox("País Destino", list(DB_FUTBOL.keys()))
    
    if pais_seleccionado == "Otro / Manual":
        pais_iso = st.text_input("Código ISO", "BRA")
        club_nombre = st.text_input("Nombre Club", "Flamengo")
        cat_fifa = st.selectbox("Categoría FIFA", ["I", "II", "III", "IV"])
    else:
        datos_pais = DB_FUTBOL[pais_seleccionado]
        pais_iso = datos_pais["iso"]
        liga_seleccionada = st.selectbox("Liga", list(datos_pais["ligas"].keys()))
        datos_liga = datos_pais["ligas"][liga_seleccionada]
        cat_fifa = datos_liga["cat"]
        
        nombres_clubes = [c["nombre"] for c in datos_liga["clubes"]] + ["Otro"]
        club_elegido = st.selectbox("Club", nombres_clubes)
        
        if club_elegido == "Otro":
            club_nombre = st.text_input("Escribe el nombre del club")
        else:
            club_nombre = club_elegido
            for c in datos_liga["clubes"]:
                if c["nombre"] == club_elegido:
                    logo_auto = c["logo"]
                    break

    # --- CAMPO MÁGICO PARA CUALQUIER EQUIPO DEL MUNDO ---
    st.markdown("### 🛡️ Escudo del Club")
    st.caption("Si el logo no aparece o es otro equipo, pega aquí el enlace de la imagen (PNG/JPG).")
    logo_final = st.text_input("URL del Logo", value=logo_auto)
    
    if logo_final:
        st.image(logo_final, width=100, caption="Vista previa")

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
if st.button("GENERAR INFORME OFICIAL 📄"):
    club_origen_auto = {"nombre": "Desconocido", "pais_asociacion": "UNK"}
    if st.session_state['pasaporte_data']:
        ultimo = st.session_state['pasaporte_data'][-1]
        club_origen_auto = {"nombre": ultimo.get('club'), "pais_asociacion": ultimo.get('pais')}

    payload = {
        "meta": {"version": "V24-PRO", "id_expediente": f"EXP-{nombre.split()[0]}"},
        "jugador": {"nombre_completo": nombre, "fecha_nacimiento": str(fecha_nac), "nacionalidad": nacionalidad},
        "acuerdo_transferencia": {
            "club_destino": {
                "nombre": club_nombre, 
                "pais_asociacion": pais_iso, 
                "categoria_fifa": cat_fifa,
                "logo": logo_final # Enviamos el logo que se ve en pantalla
            },
            "club_origen": club_origen_auto,
            "fecha_transferencia": str(fecha_trans),
            "monto_fijo_total": monto
        },
        "historial_formacion": st.session_state['pasaporte_data']
    }
    
    headers = {"X-API-Key": "sk_live_rayovallecano_2026"}
    
    with st.spinner("Conectando con Clearing House..."):
        try:
            r = requests.post("https://open-transfer-api.onrender.com/validar-operacion", json=payload, headers=headers)
            if r.status_code == 200:
                st.balloons()
                st.download_button("Descargar PDF Oficial", r.content, f"Informe_{nombre.replace(' ','_')}.pdf")
                b64 = base64.b64encode(r.content).decode()
                st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
            else:
                st.error(f"Error ({r.status_code}): {r.text}")
        except Exception as e: st.error(f"Conexión: {e}")