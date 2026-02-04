import json
from datetime import datetime

# ==========================================
# 🏛️ BASE DE DATOS LEGAL (FIFA COMPLIANCE)
# ==========================================

# 1. COSTOS DE FORMACIÓN (RSTP Anexo 4 - Art. 4)
# Nota: Precios estimados UEFA (Circular Anual). Se usan para indemnización.
COSTOS_CATEGORIA = {
    "I": 90000,   # Ej. Big-5 Ligas (Referencia estándar)
    "II": 60000,  # Ej. Segunda División
    "III": 30000,
    "IV": 10000   # Coste base obligatorio para años 12-15
}

# 2. MECANISMO DE SOLIDARIDAD (RSTP Anexo 5 - Art. 1)
# Porcentaje del monto total de transferencia asignado por edad
TARIFA_SOLIDARIDAD = {
    12: 0.25, 13: 0.25, 14: 0.25, 15: 0.25, # 5% del 5%
    16: 0.50, 17: 0.50, 18: 0.50, 19: 0.50, # 10% del 5%
    20: 0.50, 21: 0.50, 22: 0.50, 23: 0.50  # 10% del 5%
}

# 3. LISTA DE CONFLICTO (RSTP Anexo 7 - Excepción Guerra)
# Clubes de estas asociaciones tienen reglas especiales de impago
ASOCIACIONES_ANEXO_7 = ["UAF", "FUR"] # Ucrania, Rusia

def validar_transferencia(datos):
    print(f"\n⚡ INICIANDO AUDITORÍA LEGAL INTEGRAL PARA: {datos['id_expediente']}")
    print("📜 Reglamentos: FFAR (Dic 2024) + RSTP (Julio 2025)")
    
    errores = []
    alertas = []

    # =================================================================
    # 🕵️ FASE 1: DETECCIÓN DE FRAUDE Y EXCEPCIONES (RSTP Art. 5bis y Anexo 7)
    # =================================================================
    
    # 1.1. Transferencia Puente (Art. 5bis)
    if "ultimo_movimiento_fecha" in datos['jugador']:
        fecha_ultimo = datetime.strptime(datos['jugador']['ultimo_movimiento_fecha'], "%Y-%m-%d")
        fecha_actual = datetime.strptime(datos['acuerdo_transferencia']['fecha_transferencia'], "%Y-%m-%d")
        semanas = (fecha_actual - fecha_ultimo).days / 7
        
        if semanas < 16:
            errores.append(f"⛔ ALERTA ROJA (Art. 5bis): Han pasado solo {semanas:.1f} semanas desde el último fichaje. Posible TRANSFERENCIA PUENTE.")

    # 1.2. Excepción de Guerra (Anexo 7)
    origen = datos['acuerdo_transferencia']['club_origen']
    aplica_anexo7 = False
    
    if origen['pais_asociacion'] in ASOCIACIONES_ANEXO_7:
        if datos['meta'].get('bajo_anexo_7', False):
            aplica_anexo7 = True
            print(f"\n⚠️ AVISO: Operación bajo Anexo 7 (Conflicto {origen['pais_asociacion']}).")
            if datos['acuerdo_transferencia']['monto_fijo_total'] > 0:
                errores.append(f"⛔ BLOQUEO ANEXO 7: Jugador con contrato suspendido por guerra NO puede ser transferido por dinero.")

    # =================================================================
    # 🕴️ FASE 2: AUDITORÍA DE AGENTES (FFAR Art. 12, 14 y 15)
    # =================================================================
    print("\n[⚖️  FFAR] Auditando Comisiones de Agentes...")
    
    contrato = datos.get('contrato_jugador', {})
    # Art 14.3: El umbral de 200k se mide SOLO con remuneración fija
    salario_fijo = contrato.get('salario_fijo_anual_usd', 0)
    umbral_salarial = 200000 
    
    for agente in datos.get('agentes_involucrados', []):
        rol = agente['cliente_representado']
        pct = agente['porcentaje_sobre_salario']
        
        # Validación de Doble Representación Prohibida (Art. 12)
        if rol == "club_origen_y_jugador":
            errores.append(f"⛔ ERROR CRÍTICO: Conflicto de Interés (Art 12). Un agente NO puede representar al Club Vendedor y al Jugador a la vez.")
            continue

        # Cálculo de Límites (Art. 15)
        limite = 0
        tipo_limite = ""
        
        if rol == "club_origen":
            limite = 10.0
            tipo_limite = "del Transfer Fee"
        elif rol == "dual": # Jugador + Club Comprador
            limite = 10.0 if salario_fijo <= umbral_salarial else 6.0
            tipo_limite = "del Salario"
        else: # Solo Jugador o Solo Club Comprador
            limite = 5.0 if salario_fijo <= umbral_salarial else 3.0
            tipo_limite = "del Salario"

        if pct > limite:
            errores.append(f"❌ VIOLACIÓN FFAR: Agente {agente['nombre']} pide {pct}%. Límite legal es {limite}% ({tipo_limite}) porque salario fijo es {'<= ' if salario_fijo <= umbral_salarial else '> '}200k.")
        else:
            print(f"   ✅ Agente {agente['nombre']}: {pct}% Aprobado (Límite {limite}%).")

    # =================================================================
    # 💰 FASE 3: CÁLCULOS ECONÓMICOS (RSTP Anexos 4 y 5)
    # =================================================================
    
    # 3.1. Mecanismo de Solidaridad (Si hay transferencia pagada)
    if datos['meta']['tipo_calculo'] == "transferencia_internacional" and not aplica_anexo7:
        monto = datos['acuerdo_transferencia']['monto_fijo_total']
        bolsa = monto * 0.05
        print(f"\n[⚽ RSTP Anexo 5] Solidaridad a Repartir: {bolsa:,.2f} {datos['acuerdo_transferencia']['moneda']}")
        print("   (Se debe retener el 5% de cada pago parcial programado)")

    # 3.2. Indemnización por Formación (Primer contrato o <23 años)
    elif datos['meta']['tipo_calculo'] == "primer_contrato":
        print("\n[🎓 RSTP Anexo 4] Calculando Indemnización por Formación...")
        
        if aplica_anexo7:
            print("   ✅ EXENCIÓN: No se paga formación a clubes UAF/FUR (Anexo 7).")
        else:
            cat_destino = datos['acuerdo_transferencia']['club_destino']['categoria_fifa']
            costo_anual_destino = COSTOS_CATEGORIA.get(cat_destino, 10000)
            
            total_deuda = 0
            historial = datos.get('historial_formacion', [])
            
            print(f"   ℹ️  Club Destino Categoría {cat_destino} (Base: {costo_anual_destino:,.0f}€)")
            
            for periodo in historial:
                # Calcular edad
                f_inicio = datetime.strptime(periodo['fecha_inicio'], "%Y-%m-%d")
                f_nac = datetime.strptime(datos['jugador']['fecha_nacimiento'], "%Y-%m-%d")
                edad = f_inicio.year - f_nac.year
                
                # REGLA CRÍTICA ART. 5.3: Años 12-15 siempre a Categoría IV
                if 12 <= edad <= 15:
                    costo_aplicable = COSTOS_CATEGORIA["IV"]
                    nota = "(Reducido Cat. IV)"
                else:
                    costo_aplicable = costo_anual_destino
                    nota = "(Tarifa Plena)"
                
                # Exención específica si el club formador es ruso/ucraniano
                if periodo.get('pais_asociacion') in ASOCIACIONES_ANEXO_7:
                    monto = 0
                    nota = "(Exento Anexo 7)"
                else:
                    monto = costo_aplicable # Simplificado a año completo
                
                total_deuda += monto
                print(f"   - Temp. {edad} años ({periodo['club']}): {monto:,.0f}€ {nota}")
            
            print(f"   💰 DEUDA TOTAL FORMACIÓN: {total_deuda:,.2f}€")

    # =================================================================
    # 🏁 RESUMEN FINAL
    # =================================================================
    if errores:
        print("\n🚨 OPERACIÓN BLOQUEADA POR COMPLIANCE:")
        for e in errores: print(e)
    elif alertas:
        print("\n⚠️ APROBADA CON ADVERTENCIAS:")
        for a in alertas: print(a)
    else:
        print("\n✅ OPERACIÓN 100% VÁLIDA PARA FIFA TMS")

if __name__ == "__main__":
    try:
        # Cargar datos desde el archivo JSON estándar
        with open('transferencia_estandar.json', 'r') as f:
            datos_json = json.load(f)
            validar_transferencia(datos_json)
    except FileNotFoundError:
        print("❌ Error: No se encuentra 'transferencia_estandar.json'. Sube el archivo de datos primero.")
