from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uvicorn
import os
# Importamos nuestros módulos (asegúrate de que existan)
from generador_certificado import generar_reporte_pdf

app = FastAPI(title="Open Transfer API - Expert Mode")

# --- MODELOS DE DATOS (EL NUEVO LENGUAJE) ---
class ClubInfo(BaseModel):
    nombre: str
    pais_asociacion: Optional[str] = "FIFA"
    categoria_fifa: Optional[str] = "IV"

class RegistroPasaporte(BaseModel):
    # Este modelo acepta TANTO el formato viejo como el nuevo del Dashboard
    club: str
    pais: Optional[str] = None
    pais_asociacion: Optional[str] = None # Compatibilidad
    inicio: Optional[str] = None
    fin: Optional[str] = None
    fecha_inicio: Optional[str] = None # Compatibilidad vieja
    estatus: Optional[str] = "Profesional" # Nuevo campo clave!

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
        raise HTTPException(status_code=403, detail="⛔ ACCESO DENEGADO: API Key inválida o faltante. Contacte a ventas@opentransfer.com")
    return x_api_key

# --- ENDPOINT PRINCIPAL ---
@app.post("/validar-operacion")
async def validar_operacion(datos: OperacionInput, api_key: str = Depends(verificar_api_key)):
    
    print(f"🔄 Procesando expediente: {datos.meta.id_expediente}")
    
    # 1. Normalizar Historial (Convertir formato Dashboard a formato Cálculo)
    historial_limpio = []
    for reg in datos.historial_formacion:
        # Unificamos claves
        r_dict = reg.dict()
        # Si viene 'inicio' (nuevo) usalo, si no 'fecha_inicio' (viejo)
        f_ini = r_dict.get('inicio') or r_dict.get('fecha_inicio')
        # Si no hay fecha, no podemos calcular
        if not f_ini: continue 
        
        historial_limpio.append({
            "club": r_dict['club'],
            "inicio": f_ini,
            "fin": r_dict.get('fin'),
            "estatus": r_dict.get('estatus', 'Profesional'),
            "pais": r_dict.get('pais') or r_dict.get('pais_asociacion')
        })

    # 2. Re-empaquetar datos para el PDF
    datos_pdf = datos.dict()
    datos_pdf['historial_formacion'] = historial_limpio # Usamos el limpio

    # 3. Generar PDF
    try:
        pdf_path = generar_reporte_pdf(datos_pdf)
        
        # Leemos el archivo para enviarlo
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
            
        from fastapi.responses import Response
        return Response(content=pdf_content, media_type="application/pdf")
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)