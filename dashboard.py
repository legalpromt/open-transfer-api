import streamlit as st
import requests
import pandas as pd
import base64  # <--- IMPORTANTE: Necesario para el visor de PDF
from datetime import date
from scraper import obtener_datos_besoccer

st.set_page_config(page_title="Open Transfer | FIFA Expert", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {width: 100%; background-color: #0d6efd; color: white;}
    .reportview-container {background: #f0f2f6;}
    h1 {color: #1a237e;}
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #e8f0fe; color: #0d6efd; }
    </style>
    """, unsafe_allow_html=True)

# --- MEMORIA DE SESIÓN ---
if 'nombre_jug' not in st.session_state: st.session_state['nombre_jug'] = ""
if 'nac_jug' not in st.session_state: st.session_state['nac_jug'] = ""
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []

st.title("Open Transfer: FIFA Compliance Suite ⚖️")
st.markdown("---")

# 1. ENTRADA INTELIGENTE
col_search, col_res = st.columns([3, 1])
with col_search:
    url_tm = st.text_input("🔗 Pegar enlace de BeSoccer", placeholder="https://es.besoccer.com/jugador/...")
with col_res:
    st.write("")
    st.write("")
    if st.button("🕵️‍♂️ Auditar Jugador"):
        if url_tm:
            with st.spinner("Analizando..."):
                datos = obtener_datos_besoccer(url_tm)
                if datos:
                    st.session_state['nombre_jug'] = datos['nombre']
                    st.session_state['nac_jug'] = datos['nacionalidad']
                    st.success("OK")
                else: st.error("Error")

# 2. DATOS DE LA OPERACIÓN
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("👤 El Jugador")
    nombre = st.text_input("Nombre", value=st.session_state['nombre_jug'])
    nacionalidad = st.text_input("Nacionalidad", value=st.session_state['nac_jug'])
    # Fechas desbloqueadas desde 1900
    fecha_nac = st.date_input("Fecha Nacimiento", value=date(1988, 6, 1), min_value=date(1900, 1, 1), max_value=date.today())

with col2:
    st.subheader("💰 La Transferencia")
    club_destino = st.text_input("Club Comprador", "Manchester United")
    pais_destino = st.text_input("País Comprador (ISO)", "ENG", help="Usa ESP, ENG, ARG, BRA...")
    cat_destino = st.selectbox("Categoría Comprador", ["I", "II", "III", "IV"])
    monto = st.number_input("Monto (€)", value=7500000.0)
    # Fecha desbloqueada desde 1900
    fecha_trans = st.date_input("Fecha Transferencia", value=date(2010, 7, 1), min_value=date(1900, 1, 1), max_value=date.today())

with col3:
    st.subheader("⚙️ Configuración")
    tipo_calculo = st.selectbox("Cálculo", ["AMBOS", "Formación (Primer Contrato)", "Solidaridad (5%)"])
    api_key = st.text_input("API Key", value="sk_live_rayovallecano_2026", type="password")

st.markdown("---")

# 3. PASAPORTE DEPORTIVO
st.header("🛂 Pasaporte Deportivo")
st.info("Incluye la Categoría del club formador para cumplir la regla 'Media UE' (RSTP Anexo 4).")

tab_manual, tab_excel = st.tabs(["✍️ Entrada Manual", "📂 Carga Masiva (Excel/CSV)"])

# >>> PESTAÑA 1: MANUAL <<<
with tab_manual:
    with st.expander("➕ Añadir Registro", expanded=True):
        c_club, c_pais, c_cat, c_ini, c_fin, c_status = st.columns([3, 1, 1, 2, 2, 2])
        
        with c_club: new_club = st.text_input("Club")
        with c_pais: new_pais = st.text_input("País (ISO)", "MEX")
        with c_cat: new_cat = st.selectbox("Cat. Club", ["I", "II", "III", "IV"])
        
        # Fechas desbloqueadas desde 1900
        with c_ini: new_ini = st.date_input("Inicio", value=date(2000, 6, 1), min_value=date(1900, 1, 1))
        with c_fin: new_fin = st.date_input("Fin", value=date(2001, 5, 31), min_value=date(1900, 1, 1))
        
        with c_status: new_status = st.selectbox("Estatus", ["Amateur", "Profesional"])
        
        if st.button("Añadir al Historial ⬇️"):
            st.session_state['pasaporte_data'].append({
                "club": new_club, "pais": new_pais, "categoria": new_cat,
                "inicio": str(new_ini), "fin": str(new_fin), 
                "estatus": new_status
            })

# >>> PESTAÑA 2: EXCEL <<<
with tab_excel:
    st.write("Columnas requeridas: `Club`, `Pais`, `Categoria`, `Inicio`, `Fin`, `Estatus`")
    
    data_plantilla = {
        "Club": ["Chivas", "Chivas"],
        "Pais": ["MEX", "MEX"],
        "Categoria": ["I", "I"],
        "Inicio": ["2000-06-01", "2001-06-01"],
        "Fin": ["2001-05-31", "2002-05-31"],
        "Estatus": ["Amateur", "Amateur"]
    }
    df_plantilla = pd.DataFrame(data_plantilla)
    csv_plantilla = df_plantilla.to_csv(index=False).encode('utf-8')
    
    st.download_button(label="⬇️ Descargar Plantilla CSV", data=csv_plantilla, file_name="plantilla_chicharito.csv", mime="text/csv")
    
    uploaded_file = st.file_uploader("Sube tu archivo (.csv o .xlsx)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        if st.button("⚡ Procesar y Cargar"):
            try:
                if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
                else: df = pd.read_excel(uploaded_file)
                
                df.columns = [c.capitalize() for c in df.columns] 
                
                for index, row in df.iterrows():
                    st.session_state['pasaporte_data'].append({
                        "club": str(row['Club']),
                        "pais": str(row['Pais']),
                        "categoria": str(row.get('Categoria', 'IV')),
                        "inicio": str(row['Inicio']).split()[0],
                        "fin": str(row['Fin']).split()[0],
                        "estatus": str(row['Estatus'])
                    })
                st.success(f"✅ Importados {len(df)} registros.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# VISUALIZACIÓN
st.write("### 📋 Historial Cargado:")
if st.session_state['pasaporte_data']:
    st.dataframe(pd.DataFrame(st.session_state['pasaporte_data']), use_container_width=True)
    if st.button("🗑️ Borrar"): 
        st.session_state['pasaporte_data'] = []
        st.rerun()

st.markdown("---")

if st.button("GENERAR INFORME PERICIAL 📄"):
    payload = {
        "meta": { "version": "Global-V11", "id_expediente": f"EXP-{nombre.split()[0].upper()}", "tipo_calculo": tipo_calculo },
        "jugador": { "nombre_completo": nombre, "fecha_nacimiento": str(fecha_nac), "nacionalidad": nacionalidad },
        "acuerdo_transferencia": { 
            "club_origen": {"nombre": "Chivas"}, 
            "club_destino": {"nombre": club_destino, "categoria_fifa": cat_destino, "pais_asociacion": pais_destino}, 
            "monto_fijo_total": monto,
            "fecha_transferencia": str(fecha_trans)
        },
        "historial_formacion": st.session_state['pasaporte_data']
    }
    
    url_api = "https://open-transfer-api.onrender.com/validar-operacion"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    
    with st.spinner('Aplicando reglas de Media UE/EEE...'):
        try:
            response = requests.post(url_api, json=payload, headers=headers)
            if response.status_code == 200:
                st.balloons()
                
                # --- SOLUCIÓN: LIMPIEZA DE NOMBRE Y VISOR INTEGRADO ---
                
                # 1. Limpiamos el nombre para evitar Error 502 por tildes/espacios
                nombre_clean = nombre.replace(" ", "_").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n")
                file_name_seguro = f"Informe_{nombre_clean}.pdf"
                
                st.success(f"✅ Informe Generado Exitosamente: {file_name_seguro}")
                
                # 2. Botón de Descarga (Con nombre seguro)
                st.download_button(
                    label="⬇️ Descargar PDF Ahora", 
                    data=response.content, 
                    file_name=file_name_seguro, 
                    mime="application/pdf"
                )
                
                # 3. VISOR PDF EN PANTALLA (Para ver sin descargar)
                st.markdown("### 👁️ Vista Previa del Documento")
                base64_pdf = base64.b64encode(response.content).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

            else: 
                st.error(f"Error Backend: {response.text}")
        except Exception as e: 
            st.error(f"Error Conexión: {e}")