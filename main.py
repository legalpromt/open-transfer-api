from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uvicorn
import os
import difflib # Para comparar nombres
from generador_certificado import generar_reporte_pdf

app = FastAPI(title="Open Transfer API - Precision V18")

PAISES_UEFA = ["ESP", "ENG", "DEU", "ITA", "FRA", "PRT", "NLD", "BEL", "AUT", "SCO", "TUR", "RUS", "UKR", "GRE", "CHE", "HRV", "DNK", "SWE", "NOR", "POL"]

COSTOS_ENTRENAMIENTO = {
    "UEFA": { "I": 90000, "II": 60000, "III": 30000, "IV": 10000 },
    "RESTO": { "I": 50000, "II": 30000, "III": 10000, "IV": 2000 }
}

class ClubInfo(BaseModel):
    nombre: str
    pais_asociacion: Optional[str] = "FIFA"
    categoria_fifa: Optional[str] = "IV"

class RegistroPasaporte(BaseModel):
    club: str
    pais: Optional[str] = "FIFA"
    categoria: Optional[str] = "IV"
    inicio: str
    fin: str
    estatus: Optional[str] = "Profesional"

class Jugador(BaseModel):
    nombre_completo: str
    fecha_nacimiento: str
    nacionalidad: str

class Acuerdo(BaseModel):
    club_origen: ClubInfo # Aquí viene el Vendedor REAL
    club_destino: ClubInfo
    fecha_transferencia: str
    moneda: str = "EUR"
    monto_fijo_total: float

class MetaData(BaseModel):
    version: str
    id_expediente: str

class OperacionInput(BaseModel):
    meta: MetaData
    jugador: Jugador
    acuerdo_transferencia: Acuerdo
    historial_formacion: List[RegistroPasaporte]

API_KEYS_VALIDAS = {"sk_live_rayovallecano_2026": "Rayo Vallecano", "sk_test_demo": "Modo Pruebas"}

async def verificar_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS_VALIDAS: raise HTTPException(status_code=403, detail="Acceso Denegado")
    return x_api_key

def obtener_costo_anual(pais_destino, cat_destino, pais_formador, cat_formador, edad):
    destino_es_uefa = pais_destino.upper() in PAISES_UEFA
    formador_es_uefa = pais_formador.upper() in PAISES_UEFA
    region = "UEFA" if destino_es_uefa else "RESTO"
    costo_destino = COSTOS_ENTRENAMIENTO[region].get(cat_destino, 2000)
    costo_formador = COSTOS_ENTRENAMIENTO[region].get(cat_formador, 2000)

    if 12 <= edad <= 15: return COSTOS_ENTRENAMIENTO[region]["IV"], "Tarifa Base (12-15)"
    elif destino_es_uefa and formador_es_uefa and (costo_destino > costo_formador):
        return (costo_destino + costo_formador) / 2, f"Media UE ({cat_formador}->{cat_destino})"
    else: return costo_destino, f"Tarifa Plena (Cat {cat_destino})"

# Comparación flexible de nombres (ej: "Benfica" == "SL Benfica")
def son_el_mismo_club(nombre1, nombre2):
    return difflib.SequenceMatcher(None, nombre1.upper(), nombre2.upper()).ratio() > 0.6

# --- MOTOR DE PRECISIÓN V18 ---
def calcular_auditoria_precision(historial, fecha_nac, fecha_trans, monto, club_destino, club_vendedor_real):
    distribucion = []
    total_acumulado = 0
    f_nac = datetime.strptime(fecha_nac, "%Y-%m-%d")
    f_trans = datetime.strptime(fecha_trans, "%Y-%m-%d")
    edad_transferencia = f_trans.year - f_nac.year

    # 1. ORDENAR HISTORIAL (CRÍTICO)
    historial_ordenado = sorted(historial, key=lambda x: x['inicio'])
    if not historial_ordenado: return [], 0, "Error: Historial vacío"
    
    primer_club = historial_ordenado[0]
    
    # 2. DETERMINAR TIPO DE TRANSFERENCIA
    # ¿El país del Vendedor es el mismo que el del Primer Club?
    # ARG == ARG -> Primera Salida (Pagan Todos)
    # PRT != ARG -> Subsiguiente (Paga solo Vendedor)
    
    pais_vendedor = club_vendedor_real.pais_asociacion.upper()
    pais_primer_club = primer_club['pais'].upper()
    
    es_primera_salida = (pais_vendedor == pais_primer_club)
    
    nota_auditoria = "DETECTADO: PRIMERA SALIDA (Pagan Todos)" if es_primera_salida else f"DETECTADO: SUBSIGUIENTE (Solo paga {club_vendedor_real.nombre})"

    # -----------------------------------------------

    for reg in historial_ordenado:
        try:
            f_ini = datetime.strptime(reg['inicio'], "%Y-%m-%d")
            f_fin = datetime.strptime(reg['fin'], "%Y-%m-%d")
            dias = (f_fin - f_ini).days + 1
            if dias <= 0: continue
            edad_periodo = f_ini.year - f_nac.year
            factor_tiempo = dias / 365.0

            # --- A. SOLIDARIDAD (SIEMPRE SE PAGA SI HAY MONTO) ---
            if monto > 0:
                pct = 0.25 if (12 <= edad_periodo <= 15) else (0.50 if 16 <= edad_periodo <= 23 else 0)
                if pct > 0:
                    monto_sol = monto * (pct/100) * factor_tiempo
                    distribucion.append({
                        "club": reg['club'], "edad_ref": str(edad_periodo), "estatus": "Solidaridad",
                        "monto": monto_sol, "nota": f"5% ({pct}%) - OK"
                    })
                    total_acumulado += monto_sol

            # --- B. FORMACIÓN (LÓGICA BLINDADA) ---
            if 12 <= edad_periodo <= 21:
                costo, nota_c = obtener_costo_anual(club_destino.pais_asociacion, club_destino.categoria_fifa, reg.get('pais', 'FIFA'), reg.get('categoria', 'IV'), edad_periodo)
                monto_form = costo * factor_tiempo
                
                cobra_formacion = False
                razon = ""

                # REGLA DE ORO:
                if edad_transferencia > 23:
                    razon = "NO APLICA (>23 años)"
                else:
                    if es_primera_salida:
                        cobra_formacion = True # Pagan todos
                    else:
                        # Es subsiguiente: SOLO COBRA SI ES EL CLUB VENDEDOR
                        if son_el_mismo_club(reg['club'], club_vendedor_real.nombre):
                            cobra_formacion = True
                            nota_c += " (Club Vendedor)"
                        else:
                            cobra_formacion = False
                            razon = "YA PAGADO (Prev. Transf)"

                if cobra_formacion:
                    distribucion.append({
                        "club": reg['club'], "edad_ref": str(edad_periodo), "estatus": "Formación",
                        "monto": monto_form, "nota": nota_c
                    })
                    total_acumulado += monto_form
                else:
                    # Mostramos 0 y la razón
                    distribucion.append({
                        "club": reg['club'], "edad_ref": str(edad_periodo), "estatus": "Formación",
                        "monto": 0.0, "nota": f"EXENTO: {razon}"
                    })

        except: continue
    
    return distribucion, total_acumulado, nota_auditoria

@app.post("/validar-operacion")
async def validar_operacion(datos: OperacionInput, api_key: str = Depends(verificar_api_key)):
    historial_limpio = [r.dict() for r in datos.historial_formacion]
    
    tabla, total, nota_detect = calcular_auditoria_precision(
        historial_limpio, datos.jugador.fecha_nacimiento, datos.acuerdo_transferencia.fecha_transferencia,
        datos.acuerdo_transferencia.monto_fijo_total, datos.acuerdo_transferencia.club_destino,
        datos.acuerdo_transferencia.club_origen # Pasamos el objeto vendedor completo
    )

    datos_pdf = datos.dict()
    datos_pdf['historial_formacion'] = historial_limpio
    datos_pdf['calculos_auditoria'] = {"tabla_reparto": tabla, "total_auditado": total, "nota_inteligente": nota_detect}

    try:
        pdf_path = generar_reporte_pdf(datos_pdf)
        with open(pdf_path, "rb") as f: pdf_content = f.read()
        from fastapi.responses import Response
        return Response(content=pdf_content, media_type="application/pdf")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)