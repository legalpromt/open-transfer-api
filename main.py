from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
import os
import uvicorn

# Importamos tus motores de cálculo
from calculadora_solidaridad import validar_transferencia
from generador_certificado import generar_reporte_pdf

# ==========================================
# 🔐 CONFIGURACIÓN DE SEGURIDAD (EL PORTERO)
# ==========================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

CLIENTES_AUTORIZADOS = {
    "sk_live_rayovallecano_2026": "Rayo Vallecano SAD",
    "sk_live_santoslaguna_mx": "Club Santos Laguna",
    "sk_test_demo_gratis": "Cuenta de Prueba (Demo)"
}

def obtener_api_key(api_key: str = Security(api_key_header)):
    if api_key in CLIENTES_AUTORIZADOS:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="⛔ ACCESO DENEGADO: API Key inválida o faltante. Contacte a ventas@opentransfer.com"
    )

# ==========================================
# 🚀 INICIO DE LA APLICACIÓN
# ==========================================

app = FastAPI(
    title="Open Transfer API",
    description="Sistema de Compliance FIFA con Seguridad B2B.",
    version="3.0.0 (Bugfix Edition)"
)

@app.get("/")
def home():
    return {"status": "ONLINE", "mensaje": "Sistema protegido. Se requiere API Key para operar."}

@app.post("/validar-operacion")
async def validar_operacion(datos: dict, token: str = Security(obtener_api_key)):
    
    cliente = CLIENTES_AUTORIZADOS[token]
    print(f"✅ Acceso autorizado para: {cliente}")
    
    try:
        # 1. Ejecutar el motor de validación
        validar_transferencia(datos)
        
        # 2. Generar el PDF
        # Aquí usamos la función actualizada que ya sabe leer 'meta'
        generar_reporte_pdf(datos)
        
        # --- CORRECCIÓN CLAVE AQUÍ ---
        # Leemos el ID correctamente desde la carpeta 'meta'
        id_exp = datos.get('meta', {}).get('id_expediente', 'SIN-ID')
        nombre_pdf = f"Certificado_{id_exp}.pdf"
        # -----------------------------
        
        # 3. Devolver el PDF
        ruta_pdf = os.path.abspath(nombre_pdf)
        
        if not os.path.exists(ruta_pdf):
             raise HTTPException(status_code=500, detail="El PDF no se generó correctamente en el servidor.")

        return FileResponse(
            path=ruta_pdf, 
            filename=nombre_pdf, 
            media_type='application/pdf'
        )
    
    except Exception as e:
        # Esto nos dirá exactamente qué pasó si vuelve a fallar
        print(f"❌ ERROR CRÍTICO: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)