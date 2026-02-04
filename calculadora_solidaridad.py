import json
from datetime import datetime

# 1. Definir las tarifas de Solidaridad FIFA (Art. 21 y Anexo 5 RSTP)
# 5% total distribuido por años
TARIFA_POR_ANIO = {
    12: 0.25, 13: 0.25, 14: 0.25, 15: 0.25,  # 0.25% por año
    16: 0.50, 17: 0.50, 18: 0.50, 19: 0.50,  # 0.50% por año
    20: 0.50, 21: 0.50, 22: 0.50, 23: 0.50   # 0.50% por año
}

def calcular_solidaridad(datos):
    monto_total = datos['transaccion']['monto_fijo'] + datos['transaccion']['variables']
    historial = datos['historial_formacion']
    
    resultados = []
    total_a_pagar = 0
    
    print(f"--- CÁLCULO PARA: {datos['jugador']['nombre_completo']} ---")
    print(f"Monto Transferencia: {monto_total} {datos['transaccion']['moneda']}")
    print("--- DESGLOSE DE PAGOS ---")

    # Lógica simplificada: Asumimos años completos por ahora para el MVP
    # En la versión real, calcularemos días exactos.
    
    for etapa in historial:
        # Aquí convertimos fechas a edad del jugador (Lógica compleja para el futuro)
        # Para este ejemplo, simulamos que el sistema detecta los años
        
        # Simulación: Si estuvo de 2014 a 2016, son los años 12 y 13 del jugador (nacido en 2002)
        anios_cubiertos = [12, 13] 
        
        porcentaje_etapa = sum([TARIFA_POR_ANIO[y] for y in anios_cubiertos])
        monto_pagar = (monto_total * porcentaje_etapa) / 100
        
        total_a_pagar += monto_pagar
        
        resultado_club = {
            "club": etapa['club'],
            "porcentaje_reclamable": f"{porcentaje_etapa}%",
            "monto_a_pagar": f"{monto_pagar} {datos['transaccion']['moneda']}"
        }
        resultados.append(resultado_club)
        print(f"Pagar a {etapa['club']}: {monto_pagar} (Porcentaje: {porcentaje_etapa}%)")

    print(f"--- TOTAL MECANISMO SOLIDARIDAD: {total_a_pagar} ---")
    return resultados

# Simular que leemos el archivo JSON que creamos antes
with open('transferencia_estandar.json', 'r') as f:
    datos_transferencia = json.load(f)
    calcular_solidaridad(datos_transferencia)
