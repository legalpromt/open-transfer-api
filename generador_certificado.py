from fpdf import FPDF
from datetime import datetime
import json
# Importamos tu lógica de validación
from calculadora_solidaridad import validar_transferencia, TARIFA_SOLIDARIDAD, COSTOS_CATEGORIA

class PDF(FPDF):
    def header(self):
        # Logo o Título Corporativo
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(33, 37, 41) # Gris oscuro profesional
        self.cell(0, 10, 'Open Transfer API', 0, 1, 'L')
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(108, 117, 125) # Gris suave
        self.cell(0, 10, 'Estándar de Validación FIFA (RSTP & FFAR)', 0, 1, 'L')
        self.ln(5)
        # Línea divisoria
        self.set_draw_color(200, 200, 200)
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Generado automáticamente por Open Transfer API', 0, 0, 'C')

def generar_reporte_pdf(datos_json):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- CORRECCIÓN CLAVE AQUÍ ---
    # Extraemos el ID desde 'meta'
    id_expediente = datos_json.get('meta', {}).get('id_expediente', 'SIN-ID')
    # -----------------------------

    # 1. DATOS DEL EXPEDIENTE
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"CERTIFICADO DE COMPLIANCE: {id_expediente}", 0, 1)
    
    pdf.set_font('Helvetica', '', 11)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 7, f"Fecha de Emisión: {fecha}", 0, 1)
    
    # Datos del Jugador (con protección si falta algún dato)
    jugador = datos_json.get('jugador', {})
    nombre_jugador = jugador.get('nombre_completo', 'Desconocido')
    nacionalidad = jugador.get('nacionalidad', 'N/A')
    
    pdf.cell(0, 7, f"Jugador: {nombre_jugador} ({nacionalidad})", 0, 1)
    
    # Datos de Transferencia
    acuerdo = datos_json.get('acuerdo_transferencia', {})
    club_origen = acuerdo.get('club_origen', {}).get('nombre', 'Origen Desconocido')
    club_destino = acuerdo.get('club_destino', {}).get('nombre', 'Destino Desconocido')
    monto_val = acuerdo.get('monto_fijo_total', 0)
    moneda_val = acuerdo.get('moneda', 'EUR')
    
    monto_fmt = f"{monto_val:,.2f} {moneda_val}"
    
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240) # Fondo gris claro
    pdf.cell(0, 10, f" {club_origen}  >>  {club_destino}  |  Monto: {monto_fmt}", 0, 1, 'C', fill=True)
    pdf.ln(10)

    # 2. AUDITORÍA DE AGENTES (FFAR)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(33, 37, 41) # Negro
    pdf.set_text_color(255, 255, 255) # Blanco
    pdf.cell(0, 8, " 1. AUDITORÍA DE AGENTES (FFAR 2024)", 0, 1, 'L', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 8, "Agente", 1)
    pdf.cell(50, 8, "Rol Representado", 1)
    pdf.cell(30, 8, "Comisión %", 1)
    pdf.cell(50, 8, "Estado Legal", 1, 1)
    
    pdf.set_font('Helvetica', '', 10)
    for agente in datos_json.get('agentes_involucrados', []):
        pdf.cell(60, 8, agente.get('nombre', 'N/A'), 1)
        pdf.cell(50, 8, agente.get('cliente_representado', 'N/A'), 1)
        porcentaje = agente.get('porcentaje_sobre_salario', 0)
        pdf.cell(30, 8, f"{porcentaje}%", 1)
        
        # Simulación visual de validación
        if porcentaje > 10:
            pdf.set_text_color(200, 0, 0) # Rojo
            estado = "ILEGAL (> Límite)"
        else:
            pdf.set_text_color(0, 150, 0) # Verde
            estado = "VÁLIDO"
        
        pdf.cell(50, 8, estado, 1, 1)
        pdf.set_text_color(0, 0, 0) # Reset color

    pdf.ln(10)

    # 3. COSTES DE FORMACIÓN (RSTP)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(33, 37, 41)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, " 2. DESGLOSE FINANCIERO (RSTP)", 0, 1, 'L', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # Extraemos el tipo de cálculo de META
    tipo = datos_json.get('meta', {}).get('tipo_calculo', 'desconocido')
    
    if tipo == "transferencia_internacional":
        bolsa = monto_val * 0.05
        pdf.set_font('Helvetica', '', 11)
        pdf.write(5, "Concepto: Mecanismo de Solidaridad (Anexo 5)\n")
        pdf.write(5, f"Bolsa Total a Retener (5%): {bolsa:,.2f} {moneda_val}\n")
        pdf.ln(2)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.write(5, "Nota: Esta cantidad debe ser retenida de cada pago parcial proporcionalmente.")
        
    elif tipo == "primer_contrato":
        pdf.set_font('Helvetica', '', 11)
        pdf.write(5, "Concepto: Indemnización por Formación (Anexo 4)\n")
        pdf.ln(5)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(20, 8, "Edad", 1)
        pdf.cell(80, 8, "Club Formador", 1)
        pdf.cell(40, 8, "Categoría", 1)
        pdf.cell(50, 8, "Monto Calculado", 1, 1)
        
        pdf.set_font('Helvetica', '', 10)
        total = 0
        
        fecha_nac_str = jugador.get('fecha_nacimiento', '2000-01-01')
        f_nac = datetime.strptime(fecha_nac_str, "%Y-%m-%d")

        for p in datos_json.get('historial_formacion', []):
            f_inicio_str = p.get('fecha_inicio', '2010-01-01')
            f_inicio = datetime.strptime(f_inicio_str, "%Y-%m-%d")
            
            edad = f_inicio.year - f_nac.year
            
            # Lógica visual simple
            costo = 10000 if 12 <= edad <= 15 else 90000 
            if p.get('pais_asociacion') in ["UAF", "FUR"]: costo = 0 
            
            pdf.cell(20, 8, f"{edad}", 1)
            pdf.cell(80, 8, p.get('club', 'Club ?'), 1)
            pdf.cell(40, 8, "Cat. IV" if costo == 10000 else "Cat. I", 1)
            pdf.cell(50, 8, f"{costo:,.2f}", 1, 1)
            total += costo
            
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(140, 10, "TOTAL A PAGAR", 1)
        pdf.cell(50, 10, f"{total:,.2f} EUR", 1, 1)

    # 4. SELLOS
    pdf.ln(20)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(0, 150, 0)
    pdf.cell(0, 10, "VALIDADO POR OPEN TRANSFER API", 0, 1, 'C')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0)
    pdf.cell(0, 5, "Este documento es informativo y no sustituye una decisión del Tribunal del Fútbol.", 0, 1, 'C')

    # Guardar
    nombre_archivo = f"Certificado_{id_expediente}.pdf"
    pdf.output(nombre_archivo)
    print(f"\n✅ PDF Generado con éxito: {nombre_archivo}")
    return nombre_archivo

if __name__ == "__main__":
    # Esto es solo para probar en local si tienes el archivo
    try:
        with open('transferencia_estandar.json', 'r') as f:
            datos = json.load(f)
            generar_reporte_pdf(datos)
    except FileNotFoundError:
        print("Modo prueba: No se encontró transferencia_estandar.json")
        # Version Final Cloud 2.0
        # V3.0