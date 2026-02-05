from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generar_reporte_pdf(datos):
    nombre_pdf = f"Informe_Audit_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. TÍTULO EXPERTO
    elements.append(Paragraph("AUDITORÍA DE PREVISIÓN DE PAGOS (FCH SHADOW REPORT)", styles['Heading1']))
    elements.append(Paragraph(f"Ref: {datos['meta'].get('id_expediente')} | RSTP Annex 5 Analysis", styles['Normal']))
    elements.append(Spacer(1, 15))

    # 2. DATOS CLAVE
    jugador = datos.get('jugador', {})
    acuerdo = datos.get('acuerdo_transferencia', {})
    monto_total = acuerdo.get('monto_fijo_total', 0)
    moneda = acuerdo.get('moneda', 'EUR')
    
    # 3. PASAPORTE (Ya lo tenemos, lo simplificamos aquí para espacio)
    elements.append(Paragraph("1. PASAPORTE DEPORTIVO AUDITADO", styles['Heading3']))
    data_pass = [["Periodo", "Club", "Estatus", "Días"]]
    historial = datos.get('historial_formacion', [])
    for reg in historial:
        # Calculamos días visualmente
        try:
            d1 = datetime.strptime(reg['inicio'], "%Y-%m-%d")
            d2 = datetime.strptime(reg['fin'], "%Y-%m-%d")
            dias = (d2 - d1).days + 1
        except: dias = "?"
        data_pass.append([f"{reg['inicio']} / {reg['fin']}", reg['club'], reg.get('estatus','Pro'), str(dias)])
    
    t_pass = Table(data_pass, colWidths=[140, 150, 80, 50])
    t_pass.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1a237e")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_pass)
    elements.append(Spacer(1, 20))

    # ==========================================================
    # 4. LA JOYA: TABLA DE PREVISIÓN DE REPARTO (ALLOCATION)
    # ==========================================================
    elements.append(Paragraph("2. PREVISIÓN DE LIQUIDACIÓN (CLEARING HOUSE FORECAST)", styles['Heading3']))
    elements.append(Paragraph("Desglose calculado según Art 1. Anexo 5 RSTP para contrastar con 'Allocation Statement' de FIFA.", styles['Normal']))
    elements.append(Spacer(1, 5))

    calculos = datos.get('calculos_auditoria', {})
    tabla_reparto = calculos.get('tabla_reparto', [])
    total_repartir = calculos.get('total_auditado', 0)
    
    # Encabezados
    data_alloc = [["Beneficiario (Club)", "Edad Ref.", "Estatus", "Resultado Auditoría", "Notas"]]
    
    for row in tabla_reparto:
        monto_fmt = f"{row['monto']:,.2f} {moneda}"
        estilo_fila = colors.black
        
        # Si es Amateur (0 euros), lo ponemos en gris
        if row['monto'] == 0:
            estilo_fila = colors.grey
            
        data_alloc.append([
            row['club'],
            f"{row['edad_ref']} años",
            row['estatus'],
            monto_fmt,
            row['nota']
        ])

    # Fila de TOTALES
    data_alloc.append(["TOTAL A DISTRIBUIR", "", "", f"{total_repartir:,.2f} {moneda}", ""])

    t_alloc = Table(data_alloc, colWidths=[140, 50, 70, 100, 100])
    t_alloc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.black), # Cabecera Negra
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (3,1), (3,-1), 'RIGHT'), # Montos a la derecha
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        # Fila Total
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#ffeb3b")), # Amarillo Resaltador
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))
    elements.append(t_alloc)

    # 5. BLOQUE TMS (Resumen Ejecutivo)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("DATOS PARA FIFA TMS (PAYMENT DETAILS)", styles['Heading4']))
    
    remanente = (monto_total * 0.05) - total_repartir
    # A veces sobra dinero (si no hay registro en años 12-23), eso va a la Federación
    
    data_tms = [
        ["Solidarity Contribution?", "YES"],
        ["Total Deducted (5%)", f"{(monto_total*0.05):,.2f} {moneda}"],
        ["Distributed to Clubs", f"{total_repartir:,.2f} {moneda}"],
        ["Remainder (To Association)", f"{remanente:,.2f} {moneda}"]
    ]
    t_tms = Table(data_tms, colWidths=[200, 200])
    t_tms.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.black),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.red), # ROJO ALARMA
        ('FONTNAME', (0,0), (-1,-1), 'Courier-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.white),
    ]))
    elements.append(t_tms)

    doc.build(elements)
    print("✅ Informe de Auditoría Generado")