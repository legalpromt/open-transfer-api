from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uvicorn
import os
from generador_certificado import generar_reporte_pdf

app = FastAPI(title="Open Transfer API - Average Rule Edition V11")

# --- BASE DE DATOS DE COSTOS (CIRCULAR 1853) ---
PAISES_UEFA = [
    "ESP", "ENG", "DEU", "ITA", "FRA", "PRT", "NLD", "BEL", "AUT", "SCO", 
    "TUR", "RUS", "UKR", "GRE", "CHE", "HRV", "DNK", "SWE", "NOR", "POL"
]

COSTOS_ENTRENAMIENTO = {
    "UEFA": { "I": 90000, "II": 60000, "III": 30000, "IV": 10000 },
    "RESTO": { "I": 50000, "II": 30000, "III": 10000, "IV": 2000 }
}

# --- MODELOS DE DATOS ---
class ClubInfo(BaseModel):
    nombre: str
    pais_asociacion: Optional[str] = "FIFA"
    categoria_fifa: Optional[str] = "IV"

class RegistroPasaporte(BaseModel):
    club: str
    pais: Optional[str] = "FIFA"
    # NUEVO: El backend ahora acepta la categoría del club formador
    categoria: Optional[str] = "IV" 
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

# --- 🧠 MOTOR INTELIGENTE V11: REGLA DE LA MEDIA ---
def obtener_costo_anual(pais_destino, cat_destino, pais_formador, cat_formador, edad):
    # 1. Detectar Región
    destino_es_uefa = pais_destino.upper() in PAISES_UEFA
    formador_es_uefa = pais_formador.upper() in PAISES_UEFA
    
    region = "UEFA" if destino_es_uefa else "RESTO"
    moneda_costo = "EUR" if destino_es_uefa else "USD"
    
    # Costes base
    costo_destino = COSTOS_ENTRENAMIENTO[region].get(cat_destino, 2000)
    costo_formador = COSTOS_ENTRENAMIENTO[region].get(cat_formador, 2000)

    # 2. Regla Art 5.3 (12-15 años siempre es Cat IV)
    if 12 <= edad <= 15:
        costo_final = COSTOS_ENTRENAMIENTO[region]["IV"]
        nota = f"Tarifa Base (12-15 años)"
        
    # 3. REGLA DE LA MEDIA (AVERAGE RULE) - ART 6 ANEXO 4
    # Solo aplica si AMBOS son UEFA y se pasa de categoría inferior a superior
    elif destino_es_uefa and formador_es_uefa and (costo_destino > costo_formador):
        costo_final = (costo_destino + costo_formador) / 2
        nota = f"Media UE ({cat_formador} -> {cat_destino})"
        
    else:
        costo_final = costo_destino
        nota = f"Tarifa Plena (Cat {cat_destino})"
        
    return costo_final, moneda_costo, nota

# --- MOTOR DE CÁLCULO ---
def calcular_auditoria(historial, fecha_nacimiento, monto_total, club_destino, tipo_calculo):
    distribucion = []
    total_acumulado = 0
    f_nac = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")

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

            # LÓGICA SOLIDARIDAD (5%)
            if not es_formacion:
                pct = 0.25 if (12 <= edad <= 15) else (0.50 if 16 <= edad <= 23 else 0)
                if pct > 0:
                    monto_fila = monto_total * (pct/100) * (dias/365)
                    nota = f"Solidaridad ({pct}%)"
                else: nota = "Fuera de rango"

            # LÓGICA FORMACIÓN (COSTE ENTRENAMIENTO)
            else:
                if 12 <= edad <= 21:
                    # AQUÍ USAMOS LA NUEVA INTELIGENCIA V11
                    costo_base, _, nota_tarifa = obtener_costo_anual(
                        club_destino.pais_asociacion, 
                        club_destino.categoria_fifa,
                        reg.get('pais', 'FIFA'),       # País del club formador
                        reg.get('categoria', 'IV'),    # Categoría del formador
                        edad
                    )
                    monto_fila = costo_base * (dias/365)
                    nota = f"Formación: {nota_tarifa}"
                else: nota = "Fuera periodo (12-21)"

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

        except Exception: continue
            
    return distribucion, total_acumulado

# --- ENDPOINT ---
@app.post("/validar-operacion")
async def validar_operacion(datos: OperacionInput, api_key: str = Depends(verificar_api_key)):
    historial_limpio = [r.dict() for r in datos.historial_formacion]
    
    tabla, total = calcular_auditoria(
        historial_limpio, 
        datos.jugador.fecha_nacimiento, 
        datos.acuerdo_transferencia.monto_fijo_total,
        datos.acuerdo_transferencia.club_destino,
        datos.meta.tipo_calculo
    )

    datos_pdf = datos.dict()
    datos_pdf['historial_formacion'] = historial_limpio
    datos_pdf['calculos_auditoria'] = {"tabla_reparto": tabla, "total_auditado": total}

    try:
        pdf_path = generar_reporte_pdf(datos_pdf)
        with open(pdf_path, "rb") as f: pdf_content = f.read()
        from fastapi.responses import Response
        return Response(content=pdf_content, media_type="application/pdf")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)