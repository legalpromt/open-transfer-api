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

# Definimos que la llave debe venir en el encabezado (Header) llamado "X-API-Key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# BASE DE DATOS DE CLIENTES (En el futuro esto irá en una base de datos real)
# Formato: "LA_LLAVE_SECRETA": "NOMBRE_DEL_CLIENTE"
CLIENTES_AUTORIZADOS = {
    "sk_live_rayovallecano_2026": "Rayo Vallecano SAD",
    "sk_live_santoslaguna_mx": "Club Santos Laguna",
    "sk_test_demo_gratis": "Cuenta de Prueba (Demo)"
}

def obtener_api_key(api_key: str = Security(api_key_header)):
    """
    Función que verifica si la llave existe en nuestra lista de clientes.
    Si no existe, bloquea el acceso con un error 403 (Prohibido).
    """
    if api_key in CLIENTES_AUTORIZADOS:
        return api_key
    
    # Si llegamos aquí, es que la llave es falsa o no existe
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
    version="2.0.0 (Secure)"
)

@app.get("/")
def home():
    return {"status": "ONLINE", "mensaje": "Sistema protegido. Se requiere API Key para operar."}

# ENDPOINT PROTEGIDO
# Fíjate en la parte: 'token: str = Security(obtener_api_key)'
# Eso es lo que obliga a tener llave para entrar aquí.
@app.post("/validar-operacion")
async def validar_operacion(datos: dict, token: str = Security(obtener_api_key)):
    
    cliente = CLIENTES_AUTORIZADOS[token]
    print(f"✅ Acceso autorizado para: {cliente}")
    
    try:
        # 1. Ejecutar el motor de validación
        validar_transferencia(datos)
        
        # 2. Generar el PDF
        generar_reporte_pdf(datos)
        nombre_pdf = f"Certificado_{datos['id_expediente']}.pdf"
        
        # 3. Devolver el PDF
        ruta_pdf = os.path.abspath(nombre_pdf)
        return FileResponse(
            path=ruta_pdf, 
            filename=nombre_pdf, 
            media_type='application/pdf'
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)