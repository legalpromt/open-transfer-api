import streamlit as st
import requests
import pandas as pd
import base64
from datetime import date
import time

st.set_page_config(page_title="Open Transfer V29", layout="wide", page_icon="🏛️")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stSelectbox > label {font-size:14px; font-weight:bold; color:#333;}
    div[data-testid="stImage"] {border: 1px solid #ddd; border-radius: 10px; padding: 15px; background: white; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS JERÁRQUICA (ÁRBOL DE SELECCIÓN) ---
# Esto cubre el 95% de las transferencias. Para el resto, hay opción manual.
WORLD_DB = {
    "Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿": {
        "Premier League": ["Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham", "Liverpool", "Luton Town", "Man City", "Man United", "Newcastle", "Nottm Forest", "Sheffield Utd", "Tottenham", "West Ham", "Wolves"],
        "Championship": ["Leicester City", "Leeds United", "Southampton", "Ipswich Town", "Norwich City", "West Brom", "Hull City", "Coventry", "Preston", "Middlesbrough", "Sunderland", "Watford"]
    },
    "España 🇪🇸": {
        "La Liga": ["Alaves", "Almeria", "Athletic Club", "Atletico Madrid", "Barcelona", "Cadiz", "Celta Vigo", "Getafe", "Girona", "Granada", "Las Palmas", "Mallorca", "Osasuna", "Rayo Vallecano", "Real Betis", "Real Madrid", "Real Sociedad", "Sevilla", "Valencia", "Villarreal"],
        "La Liga 2": ["Leganes", "Espanyol", "Eibar", "Real Valladolid", "Sporting Gijon", "Burgos", "Oviedo", "Racing Santander", "Elche", "Levante", "Tenerife", "Zaragoza"]
    },
    "Italia 🇮🇹": {
        "Serie A": ["Atalanta", "Bologna", "Cagliari", "Empoli", "Fiorentina", "Frosinone", "Genoa", "Inter", "Juventus", "Lazio", "Lecce", "Milan", "Monza", "Napoli", "Roma", "Salernitana", "Sassuolo", "Torino", "Udinese", "Verona"]
    },
    "Alemania 🇩🇪": {
        "Bundesliga": ["Augsburg", "Bayern Munich", "Bochum", "Darmstadt", "Dortmund", "Frankfurt", "Freiburg", "Heidenheim", "Hoffenheim", "Koln", "Leipzig", "Leverkusen", "Mainz", "Gladbach", "Union Berlin", "Stuttgart", "Werder Bremen", "Wolfsburg"]
    },
    "Francia 🇫🇷": {
        "Ligue 1": ["Brest", "Clermont", "Le Havre", "Lens", "Lille", "Lorient", "Lyon", "Marseille", "Metz", "Monaco", "Montpellier", "Nantes", "Nice", "PSG", "Reims", "Rennes", "Strasbourg", "Toulouse"]
    },
    "Portugal 🇵🇹": {
        "Primeira Liga": ["Benfica", "Porto", "Sporting CP", "Braga", "Vitoria SC", "Arouca", "Moreirense", "Famalicao"]
    },
    "Argentina 🇦🇷": {
        "Liga Profesional": ["River Plate", "Boca Juniors", "Racing Club", "Independiente", "San Lorenzo", "Estudiantes", "Talleres", "Rosario Central", "Defensa y Justicia", "Lanus", "Velez", "Newells", "Argentinos Jrs"]
    },
    "Brasil 🇧🇷": {
        "Brasileirao": ["Flamengo", "Palmeiras", "Atletico Mineiro", "Fluminense", "Botafogo", "Gremio", "Bragantino", "Athletico Paranaense", "Internacional", "Sao Paulo", "Corinthians", "Santos", "Vasco da Gama", "Cruzeiro"]
    },
    "USA / MLS 🇺🇸": {
        "Major League Soccer": ["Inter Miami", "LA Galaxy", "LAFC", "Atlanta United", "NYCFC", "Seattle Sounders", "Orlando City", "Columbus Crew", "Cincinnati"]
    },
    "Arabia Saudí 🇸🇦": {
        "Saudi Pro League": ["Al Hilal", "Al Nassr", "Al Ittihad", "Al Ahli", "Al Ettifaq", "Al Shabab"]
    },
    "🌍 Resto del Mundo / Otro": {
        "Otros": ["Escribir Manualmente"]
    }
}

# --- GESTIÓN DE ESTADO ---
if 'pasaporte_data' not in st.session_state: st.session_state['pasaporte_data'] = []
if 'cached_logo' not in st.session_state: st.session_state['cached_logo'] = ""
if 'last_selected_club' not in st.session_state: st.session_state['last_selected_club'] = ""

st.title("Open Transfer V29: Selector Profesional 🏛️")
st.markdown("---")

# --- FUNCIÓN DE LOGO ---
@st.cache_data
def obtener_logo_api(nombre_exacto):
    """Busca el logo usando el nombre exacto del selector"""
    try:
        # Usamos TheSportsDB API
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={nombre_exacto}"
        r = requests.get(url, timeout=3)
        data = r.json()
        if data and data['teams']:
            return data['teams'][0]['strTeamBadge']
    except:
        return ""
    return ""

# --- INTERFAZ ---
col_jugador, col_transfer = st.columns([1, 1.3])

with col_jugador:
    st.subheader("👤 Ficha Jugador")
    with st.container(border=True):
        nombre = st.text_input("Nombre Completo", "Enzo Fernandez")
        c1, c2 = st.columns(2)
        with c1: nac = st.text_input("Nacionalidad", "ARG")
        with c2: fnac = st.date_input("Fecha Nacimiento", date(2001, 1, 17))

with col_transfer:
    st.subheader("🛡️ Club Destino (Selector Oficial)")
    
    with st.container(border=True):
        # 1. SELECCIÓN DE PAÍS
        pais = st.selectbox("1. Selecciona País / Federación", list(WORLD_DB.keys()))
        
        # 2. SELECCIÓN DE LIGA (Depende del País)
        ligas_disponibles = list(WORLD_DB[pais].keys())
        liga = st.selectbox("2. Selecciona Competición", ligas_disponibles)
        
        # 3. SELECCIÓN DE CLUB (Depende de la Liga)
        clubes_disponibles = WORLD_DB[pais][liga]
        
        # Lógica para "Escribir Manualmente"
        if clubes_disponibles[0] == "Escribir Manualmente":
            club_seleccionado = st.text_input("3. Escribe el Nombre del Club")
            club_final_name = club_seleccionado
        else:
            club_seleccionado = st.selectbox("3. Selecciona Club", clubes_disponibles)
            club_final_name = club_seleccionado

        # 4. FETCH AUTOMÁTICO DE LOGO
        logo_url_show = ""
        
        if club_final_name:
            # Solo buscamos si cambió la selección para ahorrar recursos
            if club_final_name != st.session_state['last_selected_club']:
                with st.spinner(f"Obteniendo escudo oficial de {club_final_name}..."):
                    found_url = obtener_logo_api(club_final_name)
                    st.session_state['cached_logo'] = found_url
                    st.session_state['last_selected_club'] = club_final_name
            
            logo_url_show = st.session_state['cached_logo']

        # MOSTRAR RESULTADO
        c_img, c_url = st.columns([1, 3])
        with c_img:
            if logo_url_show:
                st.image(logo_url_show, width=100)
            else:
                st.write("waiting...")
        
        with c_url:
            # Permitimos override manual si la API falla
            logo_final = st.text_input("URL Escudo (Editable)", value=logo_url_show)
            
            # Mapeo de ISO (Aproximado para el PDF)
            iso_map = {"Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿": "ENG", "España 🇪🇸": "ESP", "Italia 🇮🇹": "ITA", "Alemania 🇩🇪": "DEU", "Francia 🇫🇷": "FRA", "Portugal 🇵🇹": "PRT", "Argentina 🇦🇷": "ARG", "Brasil 🇧🇷": "BRA", "USA / MLS 🇺🇸": "USA", "Arabia Saudí 🇸🇦": "SAU"}
            iso_auto = iso_map.get(pais, "FIFA")
            
            pais_iso = st.text_input("ISO Asociación", value=iso_auto)
            cat_fifa = st.selectbox("Categoría FIFA", ["I", "II", "III", "IV"])

    st.write("")
    with st.container(border=True):
        st.write("💰 **Datos Económicos**")
        cm, cf = st.columns(2)
        with cm: monto = st.number_input("Monto (€)", value=121000000.0)
        with cf: ftrans = st.date_input("Fecha Firma", date(2023, 1, 31))

# --- PASAPORTE ---
st.markdown("---")
st.subheader("📚 Historial Deportivo")
uploaded_file = st.file_uploader("Sube Excel/CSV", type=['csv', 'xlsx'])

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
    with st.expander("Ver Tabla"): st.dataframe(pd.DataFrame(st.session_state['pasaporte_data']))

# --- GENERAR ---
st.markdown("---")
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    if st.button("GENERAR INFORME OFICIAL 🚀", type="primary", use_container_width=True):
        origen = {"nombre": "Desconocido", "pais_asociacion": "UNK"}
        if st.session_state['pasaporte_data']:
            last = st.session_state['pasaporte_data'][-1]
            origen = {"nombre": last.get('club'), "pais_asociacion": last.get('pais')}

        payload = {
            "meta": {"version": "V29-DRILLDOWN", "id_expediente": f"EXP-{str(time.time())[-4:]}"},
            "jugador": {"nombre_completo": nombre, "fecha_nacimiento": str(fnac), "nacionalidad": nac},
            "acuerdo_transferencia": {
                "club_destino": {"nombre": club_final_name, "pais_asociacion": pais_iso, "categoria_fifa": cat_fifa, "logo": logo_final},
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