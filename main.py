from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uvicorn
import os
from generador_certificado import generar_reporte_pdf

app = FastAPI(title="Open Transfer API - FIFA Audit Mode")

# --- MODELOS DE DATOS ---
class ClubInfo(BaseModel):
    nombre: str
    pais_asociacion: Optional[str] = "FIFA"
    categoria_fifa: Optional[str] = "IV"

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

# --- MOTOR DE CÁLCULO RSTP (ANEXO 5) ---
def calcular_distribucion(historial, fecha_nacimiento, monto_total):
    distribucion = []
    f_nac = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
    
    # Bolsa total de solidaridad (5%)
    bolsa_solidaridad = monto_total * 0.05
    monto_acumulado = 0

    for reg in historial:
        try:
            f_ini = datetime.strptime(reg['inicio'], "%Y-%m-%d")
            f_fin = datetime.strptime(reg['fin'], "%Y-%m-%d")
            
            # 1. Calcular Días Registrados
            dias_registrados = (f_fin - f_ini).days + 1 # Inclusive
            if dias_registrados <= 0: continue

            # 2. Calcular Edad durante el periodo (Aprox para auditoría)
            # La FIFA usa temporadas, aquí usaremos la edad al inicio del periodo como referencia
            edad = f_ini.year - f_nac.year
            
            # 3. Determinar Porcentaje según Anexo 5
            # 12-15 años: 5% de la bolsa (0.25% del transfer)
            # 16-23 años: 10% de la bolsa (0.50% del transfer)
            porcentaje_anual = 0
            if 12 <= edad <= 15:
                porcentaje_anual = 0.25 # % del transfer fee total
            elif 16 <= edad <= 23:
                porcentaje_anual = 0.50
            else:
                porcentaje_anual = 0 # Fuera de rango (ej: antes de los 12 o después de los 23)

            # 4. Cálculo del Monto (Pro-rata temporis)
            factor_tiempo = dias_registrados / 365.0
            
            # Si es AMATEUR, el cobro es 0, pero se registra para auditoría
            es_amateur = reg.get('estatus', '').lower() == 'amateur'
            
            if es_amateur:
                monto_calculado = 0.0
                nota = "EXENTO (Amateur)"
            elif porcentaje_anual == 0:
                monto_calculado = 0.0
                nota = "FUERA RANGO EDAD"
            else:
                # Fórmula: Monto Total * (Porcentaje / 100) * (Días / 365)
                monto_calculado = monto_total * (porcentaje_anual / 100) * factor_tiempo
                nota = f"Auditado ({dias_registrados} días)"

            distribucion.append({
                "club": reg['club'],
                "periodo": f"{reg['inicio']} a {reg['fin']}",
                "edad_ref": str(edad),
                "estatus": reg.get('estatus', 'Pro'),
                "monto": monto_calculado,
                "nota": nota
            })
            
            monto_acumulado += monto_calculado

        except Exception as e:
            print(f"Error calculando fila: {e}")
            continue
            
    return distribucion, monto_acumulado

# --- ENDPOINT ---
@app.post("/validar-operacion")
async def validar_operacion(datos: OperacionInput, api_key: str = Depends(verificar_api_key)):
    
    # 1. Preparar Historial
    historial_limpio = []
    for reg in datos.historial_formacion:
        historial_limpio.append(reg.dict())

    # 2. EJECUTAR MOTOR DE AUDITORÍA
    tabla_reparto, total_auditado = calcular_distribucion(
        historial_limpio, 
        datos.jugador.fecha_nacimiento, 
        datos.acuerdo_transferencia.monto_fijo_total
    )

    # 3. Empaquetar para PDF
    datos_pdf = datos.dict()
    datos_pdf['historial_formacion'] = historial_limpio
    # Inyectamos los cálculos nuevos
    datos_pdf['calculos_auditoria'] = {
        "tabla_reparto": tabla_reparto,
        "total_auditado": total_auditado
    }

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