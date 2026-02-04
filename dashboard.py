import streamlit as st
import requests
from datetime import date
# Importamos el nuevo robot de BeSoccer
from scraper import obtener_datos_besoccer

# ==============================================
# 🎨 CONFIGURACIÓN VISUAL
# ==============================================
st.set_page_config(page_title="Open Transfer | Dashboard", page_icon="⚽", layout="centered")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stButton>button {width: 100%; border-radius: 5px; font-weight: bold;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==============================================
# 🧠 MEMORIA DE LA APP
# ==============================================
if 'nombre_jug' not in st.session_state: st.session_state['nombre_jug'] = ""
if 'nac_jug' not in st.session_state: st.session_state['nac_jug'] = ""
if 'club_origen_jug' not in st.session_state: st.session_state['club_origen_jug'] = ""

# ==============================================
# 🏠 ENCABEZADO
# ==============================================
st.title("Open Transfer API ⚽")
st.markdown("### Plataforma de Validación de Compliance FIFA")

# --- ZONA DEL ROBOT BESOCCER ---
st.info("⚡ **AUTOCOMPLETADO:** Pega un enlace de BeSoccer")
col_url, col_btn = st.columns([3, 1])

with col_url:
    url_tm = st.text_input("Enlace del Jugador (BeSoccer):", placeholder="https://es.besoccer.com/jugador/lamine-yamal...")

with col_btn:
    st.write("") 
    st.write("") 
    if st.button("🔍 Buscar"):
        if url_tm and "besoccer" in url_tm:
            with st.spinner("Leyendo BeSoccer..."):
                datos_robot = obtener_datos_besoccer(url_tm)
                if datos_robot:
                    st.session_state['nombre_jug'] = datos_robot['nombre']
                    # A veces la nacionalidad viene con ciudad, cogemos lo principal
                    st.session_state['nac_jug'] = datos_robot['nacionalidad'].split('(')[0].strip()
                    st.session_state['club_origen_jug'] = datos_robot['club']
                    st.success("¡Datos encontrados!")
                else:
                    st.error("No se pudo leer. Intenta con otro enlace.")
        else:
            st.warning("Por favor, usa un enlace de besoccer.com")

st.markdown("---")

# ==============================================
# ⚙️ SIDEBAR
# ==============================================
with st.sidebar:
    st.header("🔐 Acceso Seguro")
    api_key = st.text_input("Tu API Key", value="sk_live_rayovallecano_2026", type="password")

# ==============================================
# 📝 FORMULARIO
# ==============================================
tipo_operacion = st.radio("Tipo de operación", ["Transferencia Internacional", "Primer Contrato"], horizontal=True)

st.markdown("#### 1. Datos del Jugador")
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre Completo", value=st.session_state['nombre_jug'])
    nacionalidad = st.text_input("Nacionalidad", value=st.session_state['nac_jug'])
with col2:
    fecha_nac = st.date_input("Fecha de Nacimiento", date(2002, 9, 9))
    pasaporte = st.text_input("ID Pasaporte FIFA", "HRV-LM10")

st.markdown("#### 2. Datos de la Transferencia")
col3, col4 = st.columns(2)
with col3:
    club_origen = st.text_input("Club Origen", value=st.session_state['club_origen_jug'])
    pais_origen = st.text_input("País Origen", "HRV")
with col4:
    club_destino = st.text_input("Club Destino", "Rayo Vallecano")
    pais_destino = st.text_input("País Destino", "ESP")
    cat_destino = st.selectbox("Categoría FIFA Destino", ["I", "II", "III", "IV"])

col5, col6 = st.columns(2)
with col5:
    monto = st.number_input("Monto (EUR)", value=1000000)
with col6:
    fecha_trans = st.date_input("Fecha Transferencia", date(2026, 7, 1))

# ==============================================
# 🚀 BOTÓN GENERAR
# ==============================================
st.markdown("---")
if st.button("GENERAR CERTIFICADO OFICIAL 📄"):
    
    tipo_calc_api = "transferencia_internacional" if "Internacional" in tipo_operacion else "primer_contrato"
    payload = {
        "meta": { "version": "Web-BeSoccer-1.0", "id_expediente": f"WEB-{nombre.split()[0].upper()}", "tipo_calculo": tipo_calc_api },
        "jugador": { "nombre_completo": nombre, "fecha_nacimiento": str(fecha_nac), "nacionalidad": nacionalidad, "pasaporte_fifa_id": pasaporte },
        "acuerdo_transferencia": { 
            "club_origen": {"nombre": club_origen, "pais_asociacion": pais_origen},
            "club_destino": {"nombre": club_destino, "pais_asociacion": pais_destino, "categoria_fifa": cat_destino},
            "fecha_transferencia": str(fecha_trans), "moneda": "EUR", "monto_fijo_total": monto 
        },
        "agentes_involucrados": [], "historial_formacion": []
    }

    url_api = "https://open-transfer-api.onrender.com/validar-operacion"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}

    with st.spinner('Procesando...'):
        try:
            response = requests.post(url_api, json=payload, headers=headers)
            if response.status_code == 200:
                st.balloons()
                st.success("✅ ¡Hecho!")
                st.download_button("⬇️ DESCARGAR PDF", data=response.content, file_name=f"Certificado_{nombre}.pdf", mime="application/pdf")
            else:
                st.error(f"Error: {response.text}")
        except Exception as e:
            st.error(f"Error: {e}")