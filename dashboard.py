import streamlit as st
import requests
import json
from datetime import date

# ==============================================
# 🎨 CONFIGURACIÓN VISUAL (ESTILO CORPORATIVO)
# ==============================================
st.set_page_config(
    page_title="Open Transfer | Dashboard",
    page_icon="⚽",
    layout="centered"
)

# Ocultar elementos por defecto de Streamlit para que parezca una Web App PRO
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stButton>button {
                width: 100%;
                background-color: #212529;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            .stButton>button:hover {
                background-color: #495057;
                color: white;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==============================================
# 🏠 ENCABEZADO
# ==============================================
st.title("Open Transfer API ⚽")
st.markdown("### Plataforma de Validación de Compliance FIFA")
st.markdown("---")

# ==============================================
# ⚙️ SIDEBAR (CONFIGURACIÓN)
# ==============================================
with st.sidebar:
    st.header("🔐 Acceso Seguro")
    api_key = st.text_input("Tu API Key", value="sk_live_rayovallecano_2026", type="password")
    st.info("Sistema conectado al servidor en Frankfurt (Render).")
    st.markdown("---")
    st.caption("© 2026 Open Transfer S.L.")

# ==============================================
# 📝 FORMULARIO DE ENTRADA
# ==============================================

# Selector de tipo de operación
tipo_operacion = st.radio(
    "¿Qué tipo de operación deseas certificar?",
    ["Transferencia Internacional (Solidaridad)", "Primer Contrato (Formación)"],
    horizontal=True
)

st.markdown("#### 1. Datos del Jugador")
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre Completo", "Luka Modric Jr")
    nacionalidad = st.text_input("Nacionalidad", "Croacia")
with col2:
    fecha_nac = st.date_input("Fecha de Nacimiento", date(2002, 9, 9))
    pasaporte = st.text_input("ID Pasaporte FIFA", "HRV-LM10")

st.markdown("#### 2. Datos de la Transferencia")
col3, col4 = st.columns(2)
with col3:
    club_origen = st.text_input("Club Origen (Vendedor)", "Dinamo Zagreb")
    pais_origen = st.text_input("País Origen (Código FIFA)", "HRV")
with col4:
    club_destino = st.text_input("Club Destino (Comprador)", "Rayo Vallecano")
    pais_destino = st.text_input("País Destino", "ESP")
    cat_destino = st.selectbox("Categoría FIFA Destino", ["I", "II", "III", "IV"])

col5, col6 = st.columns(2)
with col5:
    monto = st.number_input("Monto de Transferencia (EUR)", value=5000000, step=10000)
with col6:
    fecha_trans = st.date_input("Fecha de Transferencia", date(2026, 7, 1))

# Historial (Simplificado para la Demo)
historial = []
if tipo_operacion == "Primer Contrato (Formación)":
    st.markdown("#### 3. Historial de Formación (Simplificado)")
    st.info("El sistema calculará automáticamente los costes por año.")
    club_formador = st.text_input("Nombre del Club Formador Principal", "Academia Barrio")
    # Generamos historial automático de 12 a 21 años para el ejemplo
    for year in range(2014, 2024):
        historial.append({
            "club": club_formador,
            "fecha_inicio": f"{year}-01-01",
            "pais_asociacion": "ARG" # Default para demo
        })

# ==============================================
# 🚀 BOTÓN DE ACCIÓN
# ==============================================
st.markdown("---")
if st.button("GENERAR CERTIFICADO OFICIAL 📄"):
    
    # 1. Preparar el JSON (El "Pedido" para la cocina)
    tipo_calc_api = "transferencia_internacional" if "Solidaridad" in tipo_operacion else "primer_contrato"
    
    payload = {
        "meta": {
            "version": "Web-1.0",
            "id_expediente": f"WEB-{nombre.split()[0].upper()}-{date.today().year}",
            "tipo_calculo": tipo_calc_api
        },
        "jugador": {
            "nombre_completo": nombre,
            "fecha_nacimiento": str(fecha_nac),
            "nacionalidad": nacionalidad,
            "pasaporte_fifa_id": pasaporte
        },
        "acuerdo_transferencia": {
            "club_origen": {"nombre": club_origen, "pais_asociacion": pais_origen},
            "club_destino": {"nombre": club_destino, "pais_asociacion": pais_destino, "categoria_fifa": cat_destino},
            "fecha_transferencia": str(fecha_trans),
            "moneda": "EUR",
            "monto_fijo_total": monto
        },
        "agentes_involucrados": [], # Dejamos vacío para simplificar la web por ahora
        "historial_formacion": historial
    }

    # 2. Enviar a tu API en Render (La "Cocina")
    url_api = "https://open-transfer-api.onrender.com/validar-operacion"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    with st.spinner('Conectando con Servidor Legal en Frankfurt...'):
        try:
            response = requests.post(url_api, json=payload, headers=headers)
            
            if response.status_code == 200:
                st.success("✅ ¡Operación Validada con Éxito!")
                st.balloons()
                
                # Botón de Descarga
                st.download_button(
                    label="⬇️ DESCARGAR CERTIFICADO PDF",
                    data=response.content,
                    file_name=f"Certificado_{nombre}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error(f"Error del Servidor: {response.text}")
                
        except Exception as e:
            st.error(f"Error de Conexión: {e}")