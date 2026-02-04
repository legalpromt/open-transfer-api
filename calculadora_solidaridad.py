import json
from datetime import datetime

# ==========================================
# 🏛️ BASE DE DATOS LEGAL (FIFA COMPLIANCE)
# ==========================================

COSTOS_CATEGORIA = {
    "I": 90000,
    "II": 60000,
    "III": 30000,
    "IV": 10000
}

TARIFA_SOLIDARIDAD = {
    12: 0.25, 13: 0.25, 14: 0.25, 15: 0.25,
    16: 0.50, 17: 0.50, 18: 0.50, 19: 0.50,
    20: 0.50, 21: 0.50, 22: 0.50, 23: 0.50
}

ASOCIACIONES_ANEXO_7 = ["UAF", "FUR"] 

def validar_transferencia(datos):
    # --- CORRECCIÓN AQUÍ: Leer ID con seguridad ---
    id_exp = datos.get('meta', {}).get('id_expediente', 'SIN-ID')
    print(f"\n⚡ INICIANDO AUDITORÍA LEGAL INTEGRAL PARA: {id_exp}")
    # ----------------------------------------------
    print("📜 Reglamentos: FFAR (Dic 2024) + RSTP (Julio 2025)")
    
    errores = []
    alertas = []

    # =================================================================
    # 🕵️ FASE 1: DETECCIÓN DE FRAUDE Y EXCEPCIONES
    # =================================================================
    
    # Validamos que existan las claves antes de usarlas
    jugador = datos.get('jugador', {})
    acuerdo = datos.get('acuerdo_transferencia', {})
    
    # 1.1. Transferencia Puente (Art. 5bis)
    if "ultimo_movimiento_fecha" in jugador and "fecha_transferencia" in acuerdo:
        fecha_ultimo = datetime.strptime(jugador['ultimo_movimiento_fecha'], "%Y-%m-%d")
        fecha_actual = datetime.strptime(acuerdo['fecha_transferencia'], "%Y-%m-%d")
        semanas = (fecha_actual - fecha_ultimo).days / 7
        
        if semanas < 16:
            errores.append(f"⛔ ALERTA ROJA (Art. 5bis): Han pasado solo {semanas:.1f} semanas. Posible TRANSFERENCIA PUENTE.")

    # 1.2. Excepción de Guerra (Anexo 7)
    origen = acuerdo.get('club_origen', {})
    aplica_anexo7 = False
    
    if origen.get('pais_asociacion') in ASOCIACIONES_ANEXO_7:
        if datos.get('meta', {}).get('bajo_anexo_7', False):
            aplica_anexo7 = True
            print(f"\n⚠️ AVISO: Operación bajo Anexo 7 (Conflicto {origen['pais_asociacion']}).")
            if acuerdo.get('monto_fijo_total', 0) > 0:
                errores.append(f"⛔ BLOQUEO ANEXO 7: Jugador con contrato suspendido por guerra NO puede ser transferido por dinero.")

    # =================================================================
    # 🕴️ FASE 2: AUDITORÍA DE AGENTES (FFAR)
    # =================================================================
    print("\n[⚖️  FFAR] Auditando Comisiones de Agentes...")
    
    contrato = datos.get('contrato_jugador', {})
    salario_fijo = contrato.get('salario_fijo_anual_usd', 0)
    umbral_salarial = 200000 
    
    for agente in datos.get('agentes_involucrados', []):
        rol = agente.get('cliente_representado')
        pct = agente.get('porcentaje_sobre_salario', 0)
        
        if rol == "club_origen_y_jugador":
            errores.append(f"⛔ ERROR CRÍTICO: Conflicto de Interés (Art 12).")
            continue

        limite = 10.0 # Default seguro
        tipo_limite = "General"
        
        if rol == "club_origen":
            limite = 10.0
            tipo_limite = "del Transfer Fee"
        elif rol == "dual":
            limite = 10.0 if salario_fijo <= umbral_salarial else 6.0
            tipo_limite = "del Salario"
        else:
            limite = 5.0 if salario_fijo <= umbral_salarial else 3.0
            tipo_limite = "del Salario"

        if pct > limite:
            errores.append(f"❌ VIOLACIÓN FFAR: Agente {agente.get('nombre')} pide {pct}%. Límite legal es {limite}% ({tipo_limite}).")
        else:
            print(f"   ✅ Agente {agente.get('nombre')}: {pct}% Aprobado.")

    # =================================================================
    # 💰 FASE 3: CÁLCULOS ECONÓMICOS
    # =================================================================
    
    tipo_calculo = datos.get('meta', {}).get('tipo_calculo', 'desconocido')

    if tipo_calculo == "transferencia_internacional" and not aplica_anexo7:
        monto = acuerdo.get('monto_fijo_total', 0)
        bolsa = monto * 0.05
        print(f"\n[⚽ RSTP Anexo 5] Solidaridad a Repartir: {bolsa:,.2f} {acuerdo.get('moneda', 'EUR')}")

    elif tipo_calculo == "primer_contrato":
        print("\n[🎓 RSTP Anexo 4] Calculando Indemnización por Formación...")
        
        if aplica_anexo7:
            print("   ✅ EXENCIÓN: No se paga formación a clubes UAF/FUR (Anexo 7).")
        else:
            cat_destino = acuerdo.get('club_destino', {}).get('categoria_fifa', 'IV')
            costo_anual_destino = COSTOS_CATEGORIA.get(cat_destino, 10000)
            
            total_deuda = 0
            historial = datos.get('historial_formacion', [])
            
            for periodo in historial:
                f_inicio = datetime.strptime(periodo['fecha_inicio'], "%Y-%m-%d")
                f_nac_str = jugador.get('fecha_nacimiento', '2000-01-01')
                f_nac = datetime.strptime(f_nac_str, "%Y-%m-%d")
                edad = f_inicio.year - f_nac.year
                
                if 12 <= edad <= 15:
                    costo_aplicable = COSTOS_CATEGORIA["IV"]
                else:
                    costo_aplicable = costo_anual_destino
                
                if periodo.get('pais_asociacion') in ASOCIACIONES_ANEXO_7:
                    monto = 0
                else:
                    monto = costo_aplicable
                
                total_deuda += monto
                print(f"   - Temp. {edad} años: {monto:,.0f}€")
            
            print(f"   💰 DEUDA TOTAL FORMACIÓN: {total_deuda:,.2f}€")

    # =================================================================
    # 🏁 RESUMEN FINAL
    # =================================================================
    if errores:
        print("\n🚨 OPERACIÓN BLOQUEADA POR COMPLIANCE:")
        # Lanzamos excepción para parar el PDF si hay fraude grave
        raise Exception(f"Validación Fallida: {errores[0]}")
    else:
        print("\n✅ OPERACIÓN 100% VÁLIDA PARA FIFA TMS")

if __name__ == "__main__":
    try:
        with open('transferencia_estandar.json', 'r') as f:
            datos_json = json.load(f)
            validar_transferencia(datos_json)
    except FileNotFoundError:
        print("❌ Error: No se encuentra 'transferencia_estandar.json'.")