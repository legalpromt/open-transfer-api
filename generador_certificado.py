from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os

def generar_reporte_pdf(datos):
    nombre_pdf = f"Certificado_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=20, textColor=colors.HexColor("#1A237E"))
    estilo_subtitulo = ParagraphStyle('Subtitulo', parent=styles['Heading2'], fontSize=12, textColor=colors.grey)
    estilo_normal = styles['Normal']
    estilo_tms_header = ParagraphStyle('TMSHeader', parent=styles['Heading3'], fontSize=10, textColor=colors.white, alignment=1)
    
    # 1. ENCABEZADO CORPORATIVO
    elements.append(Paragraph("CERTIFICADO DE COMPLIANCE FIFA", estilo_titulo))
    elements.append(Paragraph(f"Ref: {datos['meta'].get('id_expediente', 'N/A')} | Fecha: {datetime.now().strftime('%d/%m/%Y')}", estilo_subtitulo))
    elements.append(Spacer(1, 20))

    # 2. RESUMEN DE LA OPERACIÓN
    jugador = datos.get('jugador', {})
    acuerdo = datos.get('acuerdo_transferencia', {})
    
    data_resumen = [
        ["JUGADOR", jugador.get('nombre_completo', 'N/A').upper()],
        ["ID FIFA / PASAPORTE", jugador.get('pasaporte_fifa_id', 'N/A')],
        ["CLUB ORIGEN (Vendedor)", f"{acuerdo.get('club_origen', {}).get('nombre')} ({acuerdo.get('club_origen', {}).get('pais_asociacion')})"],
        ["CLUB DESTINO (Comprador)", f"{acuerdo.get('club_destino', {}).get('nombre')} ({acuerdo.get('club_destino', {}).get('pais_asociacion')})"],
        ["FECHA TRANSFERENCIA", acuerdo.get('fecha_transferencia', 'N/A')],
        ["MONEDA", acuerdo.get('moneda', 'EUR')]
    ]
    
    tabla_resumen = Table(data_resumen, colWidths=[200, 250])
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#E8EAF6")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.white),
    ]))
    elements.append(tabla_resumen)
    elements.append(Spacer(1, 20))

    # 3. CÁLCULOS FINANCIEROS (Solidaridad o Formación)
    tipo = datos['meta'].get('tipo_calculo')
    monto_bruto = float(acuerdo.get('monto_fijo_total', 0))
    monto_deduccion = 0
    
    if tipo == "transferencia_internacional":
        elements.append(Paragraph("3. CÁLCULO MECANISMO DE SOLIDARIDAD (Anexo 5 RSTP)", styles['Heading3']))
        # Cálculo del 5%
        monto_deduccion = monto_bruto * 0.05
        
        data_fin = [
            ["CONCEPTO", "DETALLE", "IMPORTE"],
            ["Monto de Transferencia (Fijo)", "100% del Acuerdo", f"{monto_bruto:,.2f}"],
            ["Retención Solidaridad", "5.00% (A deducir)", f"- {monto_deduccion:,.2f}"],
            ["MONTO NETO A PAGAR", "Al Club Vendedor", f"{monto_bruto - monto_deduccion:,.2f}"]
        ]
        
    elif tipo == "primer_contrato":
        elements.append(Paragraph("3. CÁLCULO INDEMNIZACIÓN POR FORMACIÓN (Anexo 4 RSTP)", styles['Heading3']))
        # Lógica simplificada para el PDF (el cálculo real lo hizo la calculadora, aquí sumamos para mostrar)
        total_formacion = 0
        historial = datos.get('historial_formacion', [])
        # Recalculamos rápido para el PDF (idealmente vendría de la calculadora, pero esto asegura consistencia visual)
        cat_destino = acuerdo.get('club_destino', {}).get('categoria_fifa', 'IV')
        costos = {"I": 90000, "II": 60000, "III": 30000, "IV": 10000}
        
        data_fin = [["Temporada/Edad", "Categoría Aplicada", "Importe"]]
        
        f_nac = datetime.strptime(jugador.get('fecha_nacimiento', '2000-01-01'), "%Y-%m-%d")
        
        for periodo in historial:
            f_ini = datetime.strptime(periodo['fecha_inicio'], "%Y-%m-%d")
            edad = f_ini.year - f_nac.year
            costo = costos["IV"] if 12 <= edad <= 15 else costos.get(cat_destino, 10000)
            data_fin.append([f"Temp. {edad} años", f"Cat. {'IV' if 12<=edad<=15 else cat_destino}", f"{costo:,.2f}"])
            total_formacion += costo
            
        data_fin.append(["TOTAL A PAGAR", "", f"{total_formacion:,.2f}"])
        monto_deduccion = total_formacion # En formación se paga esto extra, no se deduce del transfer fee normalmente, pero para efectos de tabla final:
    
    # Tabla Financiera
    t_fin = Table(data_fin, colWidths=[150, 150, 150])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#283593")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Negrita fila final
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#C5CAE9")), # Color fila final
    ]))
    elements.append(t_fin)
    elements.append(Spacer(1, 30))

    # ==============================================================================
    # 4. ZONA CRÍTICA: HOJA DE CARGA PARA FIFA TMS (La "Investigación Real")
    # ==============================================================================
    
    # Creamos un bloque visual distintivo
    elements.append(Paragraph("⬇️ DATOS PARA CARGA EN FIFA TMS (COPIAR EXACTAMENTE) ⬇️", estilo_titulo))
    elements.append(Paragraph("Instrucción: Utilice estos valores en la pestaña 'Payment Details' para evitar bloqueos por 'Matching Failure'.", estilo_normal))
    elements.append(Spacer(1, 10))

    if tipo == "transferencia_internacional":
        # Datos masticados para TMS
        monto_neto = monto_bruto - monto_deduccion
        moneda = acuerdo.get('moneda', 'EUR')
        
        data_tms = [
            ["CAMPO TMS (Inglés)", "VALOR A INGRESAR", "EXPLICACIÓN TÉCNICA"],
            ["Transfer Fee (Gross)", f"{monto_bruto:,.2f} {moneda}", "Monto TOTAL del acuerdo (sin restas)."],
            ["Solidarity Contribution?", "YES / SÍ", "Marcar la casilla de deducción."],
            ["Deducted Amount", f"{monto_deduccion:,.2f} {moneda}", "El 5% que se retiene y NO se envía al vendedor."],
            ["Payable Amount (Net)", f"{monto_neto:,.2f} {moneda}", "Lo que realmente sale del banco hacia el vendedor."]
        ]
    else:
        # Datos para Formación (Training Compensation)
        # En formación no se deduce, se paga aparte.
        data_tms = [
            ["CAMPO TMS (Inglés)", "VALOR A INGRESAR", "EXPLICACIÓN TÉCNICA"],
            ["Training Compensation", "Claim / Declaration", "Subir este PDF como 'Supporting Document'."],
            ["Total Calculated", f"{total_formacion:,.2f}", "Suma total de todas las temporadas."],
            ["Beneficiaries", "Ver Historial", "Crear una línea de pago por cada club del historial."]
        ]

    t_tms = Table(data_tms, colWidths=[160, 140, 160])
    t_tms.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.black), # Encabezado Negro (Estilo Consola)
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F5F5F5")), # Fondo gris muy claro
        ('TEXTCOLOR', (1,1), (1,-1), colors.red), # El valor a ingresar en ROJO para destacar
        ('FONTNAME', (1,1), (1,-1), 'Courier-Bold'), # Fuente tipo máquina de escribir para el dato
    ]))
    
    elements.append(t_tms)
    
    # Disclaimer Legal
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Este documento es una herramienta de asistencia técnica basada en el reglamento RSTP. No sustituye el asesoramiento legal.", estilo_subtitulo))

    # Construir PDF
    doc.build(elements)
    print(f"✅ PDF Generado con Bloque TMS: {nombre_pdf}")

if __name__ == "__main__":
    # Prueba rápida local
    mock_data = {
        "meta": {"id_expediente": "TEST-TMS", "tipo_calculo": "transferencia_internacional"},
        "jugador": {"nombre_completo": "Test Player", "pasaporte_fifa_id": "12345"},
        "acuerdo_transferencia": {"club_origen": {"nombre": "Club A", "pais_asociacion": "ESP"}, "club_destino": {"nombre": "Club B", "pais_asociacion": "ENG"}, "fecha_transferencia": "2026-01-01", "monto_fijo_total": 1000000, "moneda": "EUR"}
    }
    generar_reporte_pdf(mock_data)