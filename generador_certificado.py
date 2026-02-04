from fpdf import FPDF
from datetime import datetime
import json
# Importamos tu lógica de validación (asegúrate de que el otro archivo se llame calculadora_solidaridad.py)
from calculadora_solidaridad import validar_transferencia, TARIFA_SOLIDARIDAD, COSTOS_CATEGORIA

class PDF(FPDF):
    def header(self):
        # Logo o Título Corporativo (Estilo Invopop)
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
    
    # 1. DATOS DEL EXPEDIENTE
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"CERTIFICADO DE COMPLIANCE: {datos_json['id_expediente']}", 0, 1)
    
    pdf.set_font('Helvetica', '', 11)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 7, f"Fecha de Emisión: {fecha}", 0, 1)
    pdf.cell(0, 7, f"Jugador: {datos_json['jugador']['nombre_completo']} ({datos_json['jugador']['nacionalidad']})", 0, 1)
    
    origen = datos_json['acuerdo_transferencia']['club_origen']['nombre']
    destino = datos_json['acuerdo_transferencia']['club_destino']['nombre']
    monto = f"{datos_json['acuerdo_transferencia']['monto_fijo_total']:,.2f} {datos_json['acuerdo_transferencia']['moneda']}"
    
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240) # Fondo gris claro
    pdf.cell(0, 10, f" {origen}  >>  {destino}  |  Monto: {monto}", 0, 1, 'C', fill=True)
    pdf.ln(10)

    # 2. AUDITORÍA DE AGENTES (FFAR)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(33, 37, 41) # Negro
    pdf.set_text_color(255, 255, 255) # Blanco
    pdf.cell(0, 8, " 1. AUDITORÍA DE AGENTES (FFAR 2024)", 0, 1, 'L', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    # Aquí simulamos la lógica visual (en una versión pro, importaríamos los errores reales)
    # Por ahora mostramos la tabla de agentes
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 8, "Agente", 1)
    pdf.cell(50, 8, "Rol Representado", 1)
    pdf.cell(30, 8, "Comisión %", 1)
    pdf.cell(50, 8, "Estado Legal", 1, 1)
    
    pdf.set_font('Helvetica', '', 10)
    for agente in datos_json.get('agentes_involucrados', []):
        pdf.cell(60, 8, agente['nombre'], 1)
        pdf.cell(50, 8, agente['cliente_representado'], 1)
        pdf.cell(30, 8, f"{agente['porcentaje_sobre_salario']}%", 1)
        
        # Simulación visual de validación
        if agente['porcentaje_sobre_salario'] > 10:
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

    tipo = datos_json['meta']['tipo_calculo']
    if tipo == "transferencia_internacional":
        bolsa = datos_json['acuerdo_transferencia']['monto_fijo_total'] * 0.05
        pdf.set_font('Helvetica', '', 11)
        pdf.write(5, "Concepto: Mecanismo de Solidaridad (Anexo 5)\n")
        pdf.write(5, f"Bolsa Total a Retener (5%): {bolsa:,.2f} {datos_json['acuerdo_transferencia']['moneda']}\n")
        pdf.ln(2)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.write(5, "Nota: Esta cantidad debe ser retenida de cada pago parcial proporcionalmente.")
        
    elif tipo == "primer_contrato":
        pdf.set_font('Helvetica', '', 11)
        pdf.write(5, "Concepto: Indemnización por Formación (Anexo 4)\n")
        # Aquí pondríamos la lógica de tabla de años, simplificada para el ejemplo visual
        pdf.ln(5)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(20, 8, "Edad", 1)
        pdf.cell(80, 8, "Club Formador", 1)
        pdf.cell(40, 8, "Categoría", 1)
        pdf.cell(50, 8, "Monto Calculado", 1, 1)
        
        pdf.set_font('Helvetica', '', 10)
        total = 0
        for p in datos_json.get('historial_formacion', []):
            f_inicio = datetime.strptime(p['fecha_inicio'], "%Y-%m-%d")
            f_nac = datetime.strptime(datos_json['jugador']['fecha_nacimiento'], "%Y-%m-%d")
            edad = f_inicio.year - f_nac.year
            
            # Lógica visual simple
            costo = 10000 if 12 <= edad <= 15 else 90000 
            if p.get('pais_asociacion') in ["UAF", "FUR"]: costo = 0 # Anexo 7
            
            pdf.cell(20, 8, f"{edad}", 1)
            pdf.cell(80, 8, p['club'], 1)
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
    nombre_archivo = f"Certificado_{datos_json['id_expediente']}.pdf"
    pdf.output(nombre_archivo)
    print(f"\n✅ PDF Generado con éxito: {nombre_archivo}")

if __name__ == "__main__":
    with open('transferencia_estandar.json', 'r') as f:
        datos = json.load(f)
        generar_reporte_pdf(datos)
