from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uvicorn
import os
import difflib
from fastapi.responses import Response
from generador_certificado import generar_reporte_pdf

app = FastAPI(title="Open Transfer API - V21 Clearing House Edition")

# --- BASES DE DATOS FIFA ---
PAISES_UEFA = ["ESP", "ENG", "DEU", "ITA", "FRA", "PRT", "NLD", "BEL", "AUT", "SCO", "TUR", "RUS", "UKR", "GRE", "CHE", "HRV", "DNK", "SWE", "NOR", "POL"]
COSTOS = {
    "UEFA": {"I": 90000, "II": 60000, "III": 30000, "IV": 10000}, 
    "RESTO": {"I": 50000, "II": 30000, "III": 10000, "IV": 2000}
}
API_KEYS = {"sk_live_rayovallecano_2026": "Rayo"}

# --- MODELOS DE DATOS (FLEXIBLES) ---
class ClubInfo(BaseModel):
    nombre: str
    pais_asociacion: str = "UNK" # Valor por defecto para no romper
    categoria_fifa: str = "IV"   # Valor por defecto

class Acuerdo(BaseModel):
    club_destino: ClubInfo
    club_origen: Optional[ClubInfo] = None # Opcional para evitar error 422
    fecha_transferencia: str
    monto_fijo_total: float

class RegistroPasaporte(BaseModel):
    club: str
    pais: str
    categoria: str = "IV"
    inicio: str
    fin: str
    estatus: Optional[str] = "Profesional"

class OperacionInput(BaseModel):
    meta: dict
    jugador: dict
    acuerdo_transferencia: Acuerdo
    historial_formacion: List[RegistroPasaporte]

# --- UTILIDADES ---
def obtener_costo(pais_dest, cat_dest, pais_form, cat_form, edad):
    # Lógica de costos según región y edad
    region = "UEFA" if pais_dest.upper() in PAISES_UEFA else "RESTO"
    base = COSTOS[region].get(cat_dest, 2000)
    # De los 12 a los 15 años siempre es Categoría IV
    if 12 <= edad <= 15: return COSTOS[region]["IV"]
    return base

def son_el_mismo_club(n1, n2):
    # Comparación "fuzzy" para saber si Benfica == SL Benfica
    if not n1 or not n2: return False
    return difflib.SequenceMatcher(None, n1.upper(), n2.upper()).ratio() > 0.6

# --- MOTOR DE CÁLCULO V21 (SEPARACIÓN DE LISTAS) ---
def calcular_auditoria_v21(historial, fecha_nac_str, fecha_trans_str, monto, club_dest, club_orig_manual=None):
    f_nac = datetime.strptime(fecha_nac_str, "%Y-%m-%d")
    f_trans = datetime.strptime(fecha_trans_str, "%Y-%m-%d")
    edad_transferencia = f_trans.year - f_nac.year

    # Listas SEPARADAS para el PDF
    lista_solidaridad = []
    lista_formacion = []
    
    total_solidaridad = 0
    total_formacion = 0

    # 1. ORDENAR Y PREPARAR
    historial_sorted = sorted(historial, key=lambda x: x['inicio'])
    if not historial_sorted: 
        return {
            "tipo_operacion_detectada": "Error: Historial Vacío",
            "lista_solidaridad": [], "lista_formacion": [],
            "total_solidaridad": 0, "total_formacion": 0
        }

    primer_club = historial_sorted[0]
    ultimo_club = historial_sorted[-1]
    
    pais_origen = primer_club['pais'].upper()
    pais_vendedor = ultimo_club['pais'].upper()
    
    # Nombre del vendedor real (detectado o manual)
    nombre_vendedor_real = club_orig_manual.nombre if club_orig_manual else ultimo_club['club']
    
    # Lógica de Detección Automática
    es_primera_salida = (pais_origen == pais_vendedor)
    
    if edad_transferencia > 23:
        tipo_caso = "VETERANO (>23 AÑOS) - Solo Solidaridad"
        aplica_formacion = False
    elif es_primera_salida:
        tipo_caso = "PRIMERA TRANSFERENCIA (Pagan Todos)"
        aplica_formacion = True
    else:
        tipo_caso = f"SUBSIGUIENTE (Paga solo: {nombre_vendedor_real})"
        aplica_formacion = True

    # 2. BUCLE ÚNICO DE CÁLCULO
    for reg in historial_sorted:
        try:
            f_ini = datetime.strptime(reg['inicio'], "%Y-%m-%d")
            f_fin = datetime.strptime(reg['fin'], "%Y-%m-%d")
            dias = (f_fin - f_ini).days + 1
            if dias <= 0: continue
            
            # Edad al final del periodo
            edad_periodo = f_ini.year - f_nac.year
            factor = dias / 365.0
        except: continue

        # --- A. SOLIDARIDAD (LISTA AZUL) ---
        if monto > 0:
            pct = 0.25 if (12 <= edad_periodo <= 15) else (0.50 if 16 <= edad_periodo <= 23 else 0)
            if pct > 0:
                monto_sol = monto * (pct/100) * factor
                lista_solidaridad.append({
                    "club": reg['club'],
                    "periodo": f"{edad_periodo} años",
                    "porcentaje": f"{pct}%",
                    "nota": "OK",
                    "monto": monto_sol
                })
                total_solidaridad += monto_sol

        # --- B. FORMACIÓN (LISTA VERDE) ---
        if aplica_formacion and 12 <= edad_periodo <= 21:
            costo = obtener_costo(club_dest.pais_asociacion, club_dest.categoria_fifa, reg['pais'], reg['categoria'], edad_periodo)
            monto_form = costo * factor
            
            debe_pagar = False
            nota = ""
            
            if es_primera_salida:
                debe_pagar = True
                nota = "Corresponde (1ª Salida)"
            else:
                # Fuzzy match para saber si es el vendedor
                if son_el_mismo_club(reg['club'], nombre_vendedor_real):
                    debe_pagar = True
                    nota = "Corresponde (Vendedor)"
                else:
                    debe_pagar = False
                    nota = "EXENTO: Ya Pagado"
            
            lista_formacion.append({
                "club": reg['club'],
                "cat_periodo": f"Cat. {reg['categoria']} ({edad_periodo})",
                "edad_ref": str(edad_periodo), # Para el PDF
                "periodo": str(edad_periodo),  # Fallback
                "nota": nota,
                "monto": monto_form if debe_pagar else 0.0
            })
            if debe_pagar: total_formacion += monto_form

    # Devolvemos estructura completa
    return {
        "tipo_operacion_detectada": tipo_caso,
        "lista_solidaridad": lista_solidaridad,
        "lista_formacion": lista_formacion,
        "total_solidaridad": total_solidaridad,
        "total_formacion": total_formacion
    }

# --- ENDPOINT ---
@app.post("/validar-operacion")
async def validar_operacion(datos: OperacionInput, x_api_key: str = Header(None)):
    if x_api_key not in API_KEYS: raise HTTPException(403, "API Key Invalida")

    historial = [r.dict() for r in datos.historial_formacion]
    acuerdo = datos.acuerdo_transferencia
    
    # Llamamos a la lógica V21
    resultados = calcular_auditoria_v21(
        historial, 
        datos.jugador['fecha_nacimiento'], 
        acuerdo.fecha_transferencia, 
        acuerdo.monto_fijo_total,
        acuerdo.club_destino,
        acuerdo.club_origen
    )

    datos_pdf = datos.dict()
    datos_pdf['calculos_auditoria'] = resultados
    
    # Generamos PDF con el nuevo diseñador
    pdf_path = generar_reporte_pdf(datos_pdf)
    
    with open(pdf_path, "rb") as f: 
        return Response(content=f.read(), media_type="application/pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)