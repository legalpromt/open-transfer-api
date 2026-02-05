from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uvicorn
import os
from generador_certificado import generar_reporte_pdf

app = FastAPI(title="Open Transfer API - Global Edition V10")

# --- BASE DE DATOS DE COSTOS (CIRCULAR 1853) ---
PAISES_UEFA = [
    "ESP", "ENG", "DEU", "ITA", "FRA", "PRT", "NLD", "BEL", "AUT", "SCO", 
    "TUR", "RUS", "UKR", "GRE", "CHE", "HRV", "DNK", "SWE", "NOR", "POL"
]

COSTOS_ENTRENAMIENTO = {
    "UEFA": { # En EUROS
        "I": 90000, "II": 60000, "III": 30000, "IV": 10000
    },
    "RESTO": { # En DÓLARES (CONMEBOL, CONCACAF, AFC, CAF, OFC)
        "I": 50000, "II": 30000, "III": 10000, "IV": 2000
    }
}

# --- MODELOS DE DATOS ---
class ClubInfo(BaseModel):
    nombre: str
    pais_asociacion: Optional[str] = "FIFA"
    categoria_fifa: Optional[str] = "IV" # El usuario elige I, II, III o IV

class RegistroPasaporte(BaseModel):
    club: str
    pais: Optional[str] = "FIFA"
    inicio: str
    fin: str
    estatus: Optional[str] = "Profesional"

class Jugador(BaseModel):
    nombre_completo: str
    fecha_nacimiento: str
    nacionalidad: str
    pasaporte_fifa_id: Optional[str] = None

class Acuerdo(BaseModel):
    club_origen: ClubInfo
    club_destino: ClubInfo
    fecha_transferencia: str
    moneda: str = "EUR"
    monto_fijo_total: float

class MetaData(BaseModel):
    version: str
    id_expediente: str
    tipo_calculo: str

class OperacionInput(BaseModel):
    meta: MetaData
    jugador: Jugador
    acuerdo_transferencia: Acuerdo
    historial_formacion: List[RegistroPasaporte]
    agentes_involucrados: List[dict] = []

# --- SEGURIDAD ---
API_KEYS_VALIDAS = {
    "sk_live_rayovallecano_2026": "Rayo Vallecano",
    "sk_test_demo": "Modo Pruebas"
}

async def verificar_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS_VALIDAS:
        raise HTTPException(status_code=403, detail="⛔ ACCESO DENEGADO")
    return x_api_key

# --- 🧠 MOTOR INTELIGENTE: DETERMINAR PRECIO ---
def obtener_costo_anual(pais_destino, cat_destino, edad):
    # 1. Detectar Confederación
    es_uefa = pais_destino.upper() in PAISES_UEFA
    region = "UEFA" if es_uefa else "RESTO"
    moneda_costo = "EUR" if es_uefa else "USD"
    
    # 2. Aplicar Regla Art 5.3 (12-15 años siempre es Cat IV)
    if 12 <= edad <= 15:
        costo = COSTOS_ENTRENAMIENTO[region]["IV"]
        nota_costo = f"Tarifa Base (Cat. IV {region})"
    else:
        # A partir de 16 años, usamos la categoría del club comprador
        costo = COSTOS_ENTRENAMIENTO[region].get(cat_destino, 2000)
        nota_costo = f"Tarifa Plena (Cat. {cat_destino} {region})"
        
    return costo, moneda_costo, nota_costo

# --- MOTOR DE CÁLCULO ---
def calcular_auditoria(historial, fecha_nacimiento, monto_total, club_destino, tipo_calculo):
    distribucion = []
    total_acumulado = 0
    f_nac = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")

    # Si es FORMACIÓN (Training Compensation)
    es_formacion = "formacion" in tipo_calculo or "primer_contrato" in tipo_calculo

    for reg in historial:
        try:
            f_ini = datetime.strptime(reg['inicio'], "%Y-%m-%d")
            f_fin = datetime.strptime(reg['fin'], "%Y-%m-%d")
            dias = (f_fin - f_ini).days + 1
            if dias <= 0: continue
            
            edad = f_ini.year - f_nac.year
            
            monto_fila = 0
            nota = ""
            moneda_fila = "EUR"

            # --- LÓGICA A: SOLIDARIDAD (5% del Transfer) ---
            if not es_formacion:
                # Regla: 12-15 años (0.25% del total), 16-23 años (0.5% del total)
                pct = 0.25 if (12 <= edad <= 15) else (0.50 if 16 <= edad <= 23 else 0)
                if pct > 0:
                    monto_fila = monto_total * (pct/100) * (dias/365)
                    nota = f"Solidaridad ({pct}%)"
                    if reg.get('estatus') == 'Amateur': nota += " [AMATEUR COBRA]"
                else:
                    nota = "Fuera de rango edad"

            # --- LÓGICA B: FORMACIÓN (Costos Fijos Circular 1853) ---
            else:
                # Solo se paga formación hasta los 23 y solo si fue formado antes de los 21
                if 12 <= edad <= 21:
                    costo_base, moneda_fila, nota_tarifa = obtener_costo_anual(
                        club_destino.pais_asociacion, 
                        club_destino.categoria_fifa, 
                        edad
                    )
                    # Prorrateo
                    monto_fila = costo_base * (dias/365)
                    nota = f"Formación: {nota_tarifa}"
                else:
                    nota = "Fuera periodo formación (12-21)"

            if monto_fila > 0:
                distribucion.append({
                    "club": reg['club'],
                    "periodo": f"{reg['inicio']} a {reg['fin']}",
                    "edad_ref": str(edad),
                    "estatus": reg.get('estatus', 'Pro'),
                    "monto": monto_fila,
                    "nota": nota
                })
                total_acumulado += monto_fila

        except Exception as e:
            continue
            
    return distribucion, total_acumulado

# --- ENDPOINT ---
@app.post("/validar-operacion")
async def validar_operacion(datos: OperacionInput, api_key: str = Depends(verificar_api_key)):
    
    # 1. Preparar Historial
    historial_limpio = [r.dict() for r in datos.historial_formacion]

    # 2. EJECUTAR MOTOR
    tabla, total = calcular_auditoria(
        historial_limpio, 
        datos.jugador.fecha_nacimiento, 
        datos.acuerdo_transferencia.monto_fijo_total,
        datos.acuerdo_transferencia.club_destino,
        datos.meta.tipo_calculo
    )

    # 3. Empaquetar
    datos_pdf = datos.dict()
    datos_pdf['historial_formacion'] = historial_limpio
    datos_pdf['calculos_auditoria'] = {"tabla_reparto": tabla, "total_auditado": total}

    try:
        pdf_path = generar_reporte_pdf(datos_pdf)
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
        from fastapi.responses import Response
        return Response(content=pdf_content, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)