import streamlit as st
import requests
from datetime import date
from scraper import obtener_datos_besoccer

st.set_page_config(page_title="Open Transfer | FIFA Expert", page_icon="⚖️", layout="wide") # Layout wide para ver mejor la tabla

# Estilos Pro
st.markdown("""
    <style>
    .stButton>button {width: 100%; background-color: #0d6efd; color: white;}
    .reportview-container {background: #f0f2f6;}
    h1 {color: #1a237e;}
    </style>
    """, unsafe_allow_html=True)

# Memoria
if 'nombre_jug' not in st.session_state: st.session_state['nombre_jug'] = ""
if 'nac_jug' not in st.session_state: st.session_state['nac_jug'] = ""
if 'club_origen_jug' not in st.session_state: st.session_state['club_origen_jug'] = ""
# NUEVO: Memoria para el Pasaporte
if 'pasaporte_data' not in st.session_state: 
    st.session_state['pasaporte_data'] = []

st.title("Open Transfer: FIFA Compliance Suite ⚖️")
st.markdown("---")

# 1. ENTRADA INTELIGENTE
col_search, col_res = st.columns([3, 1])
with col_search:
    url_tm = st.text_input("🔗 Pegar enlace de BeSoccer (Autocompletado)", placeholder="https://es.besoccer.com/jugador/...")
with col_res:
    st.write("")
    st.write("")
    if st.button("🕵️‍♂️ Auditar Jugador"):
        if url_tm:
            with st.spinner("Analizando historial..."):
                datos = obtener_datos_besoccer(url_tm)
                if datos:
                    st.session_state['nombre_jug'] = datos['nombre']
                    st.session_state['nac_jug'] = datos['nacionalidad']
                    st.session_state['club_origen_jug'] = datos['club']
                    st.success("Jugador identificado")
                else:
                    st.error("Error de lectura")

# 2. DATOS DE LA OPERACIÓN
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("👤 El Jugador")
    nombre = st.text_input("Nombre", value=st.session_state['nombre_jug'])
    nacionalidad = st.text_input("Nacionalidad", value=st.session_state['nac_jug'])
    fecha_nac = st.date_input("Fecha Nacimiento", date(2004, 7, 13)) # Ejemplo Lamine

with col2:
    st.subheader("💰 La Transferencia")
    club_origen = st.text_input("Club Vendedor", value=st.session_state['club_origen_jug'])
    club_destino = st.text_input("Club Comprador", "Rayo Vallecano")
    cat_destino = st.selectbox("Categoría Comprador", ["I", "II", "III", "IV"])
    monto = st.number_input("Monto Transferencia (€)", value=1000000.0, step=10000.0)
    fecha_trans = st.date_input("Fecha Transferencia", date.today())

with col3:
    st.subheader("⚙️ Configuración")
    tipo_calculo = st.selectbox("¿Qué quieres calcular?", ["Solidaridad (5%)", "Formación (Primer Contrato)", "AMBOS (Reporte Completo)"])
    api_key = st.text_input("API Key", value="sk_live_rayo_2026", type="password")

st.markdown("---")

# 3. EL CORAZÓN: PASAPORTE DEL JUGADOR (Edición Experta)
st.header("🛂 Pasaporte Deportivo del Jugador (FIFA Passport)")
st.info("Ingresa el historial cronológico exacto. Esto definirá la precisión legal del cálculo.")

# Formulario para añadir filas al pasaporte
with st.expander("➕ Añadir Registro al Pasaporte", expanded=True):
    c_club, c_pais, c_ini, c_fin, c_status = st.columns([3, 1, 2, 2, 2])
    
    with c_club: new_club = st.text_input("Club")
    with c_pais: new_pais = st.text_input("País (ISO)", "ESP")
    with c_ini: new_ini = st.date_input("Fecha Inscripción", date(2016, 7, 1))
    with c_fin: new_fin = st.date_input("Fecha Baja", date(2017, 6, 30))
    with c_status: new_status = st.selectbox("Estatus", ["Amateur", "Profesional"])
    
    if st.button("Añadir al Historial ⬇️"):
        st.session_state['pasaporte_data'].append({
            "club": new_club,
            "pais": new_pais,
            "inicio": str(new_ini),
            "fin": str(new_fin),
            "estatus": new_status
        })

# Visualización del Pasaporte en Tabla
if st.session_state['pasaporte_data']:
    st.table(st.session_state['pasaporte_data'])
    if st.button("🗑️ Borrar Historial"):
        st.session_state['pasaporte_data'] = []

st.markdown("---")

if st.button("GENERAR INFORME PERICIAL COMPLETO 📄"):
    # Lógica de envío al backend (simplificada para este paso)
    # Aquí es donde le diríamos al backend: "Calcula TODO con estos datos exactos"
    
    payload = {
        "meta": { "version": "Expert-6.0", "id_expediente": f"EXP-{nombre.split()[0].upper()}", "tipo_calculo": "reporte_completo" },
        "jugador": { "nombre_completo": nombre, "fecha_nacimiento": str(fecha_nac), "nacionalidad": nacionalidad },
        "acuerdo_transferencia": { 
            "club_origen": {"nombre": club_origen}, 
            "club_destino": {"nombre": club_destino, "categoria_fifa": cat_destino}, 
            "monto_fijo_total": monto,
            "moneda": "EUR",
            "fecha_transferencia": str(fecha_trans)
        },
        # AQUÍ ESTÁ LA CLAVE: Enviamos el pasaporte detallado
        "historial_formacion": st.session_state['pasaporte_data']
    }
    
    url_api = "https://open-transfer-api.onrender.com/validar-operacion"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    
    with st.spinner('Auditando normativa FIFA...'):
        try:
            response = requests.post(url_api, json=payload, headers=headers)
            if response.status_code == 200:
                st.balloons()
                st.success("✅ Informe Generado")
                st.download_button("⬇️ Descargar PDF Legal", response.content, file_name=f"Informe_{nombre}.pdf", mime="application/pdf")
            else:
                st.error(f"Error Backend: {response.text}")
        except Exception as e:
            st.error(f"Error Conexión: {e}")