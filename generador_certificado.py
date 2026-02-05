from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generar_reporte_pdf(datos):
    nombre_pdf = f"Certificado_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # TÍTULO
    elements.append(Paragraph("INFORME DE COMPLIANCE & PASAPORTE FIFA", styles['Heading1']))
    elements.append(Paragraph(f"Ref: {datos['meta'].get('id_expediente', 'N/A')} | Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # 1. RESUMEN
    jugador = datos.get('jugador', {})
    acuerdo = datos.get('acuerdo_transferencia', {})
    data_res = [
        ["JUGADOR", jugador.get('nombre_completo')],
        ["FECHA NACIMIENTO", jugador.get('fecha_nacimiento')],
        ["TRANSFERENCIA", f"{acuerdo.get('monto_fijo_total', 0):,.2f} {acuerdo.get('moneda', 'EUR')}"]
    ]
    t_res = Table(data_res, colWidths=[150, 300])
    t_res.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)]))
    elements.append(t_res)
    elements.append(Spacer(1, 20))

    # 2. EL PASAPORTE (LA VERDAD DEL JUGADOR)
    elements.append(Paragraph("2. PASAPORTE DEPORTIVO (Registration History)", styles['Heading3']))
    
    # Encabezados de la tabla Pasaporte
    data_pass = [["Temporada/Periodo", "Club", "Asociación", "Estatus", "Fechas"]]
    
    historial = datos.get('historial_formacion', [])
    for reg in historial:
        # Formateamos bonito para el PDF
        fechas_str = f"{reg.get('inicio', '?')} a {reg.get('fin', '?')}"
        club_str = reg.get('club', 'Desc.')
        # Si es Amateur, lo pintamos diferente o lo marcamos
        estatus = reg.get('estatus', 'N/A').upper()
        
        data_pass.append([
            "Periodo Registrado", # Aquí podríamos calcular la temporada exacta
            club_str,
            reg.get('pais', '-'),
            estatus,
            fechas_str
        ])

    t_pass = Table(data_pass, colWidths=[90, 120, 50, 70, 140])
    t_pass.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1a237e")), # Azul FIFA
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_pass)
    elements.append(Spacer(1, 20))

    # 3. CÁLCULO SOLIDARIDAD (Estimado basado en monto)
    monto = float(acuerdo.get('monto_fijo_total', 0))
    soli = monto * 0.05
    elements.append(Paragraph("3. CÁLCULO FINANCIERO", styles['Heading3']))
    data_fin = [
        ["Concepto", "Monto"],
        ["Transferencia Bruta", f"{monto:,.2f}"],
        ["Retención Solidaridad (5%)", f"{soli:,.2f}"],
        ["A Pagar Neto", f"{monto - soli:,.2f}"]
    ]
    t_fin = Table(data_fin)
    t_fin.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(t_fin)
    
    # BLOQUE TMS (Tu joya)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("DATOS PARA FIFA TMS (COPIAR)", styles['Heading4']))
    data_tms = [
        ["Solidarity Contribution?", "YES"],
        ["Deducted Amount", f"{soli:,.2f}"],
        ["Payable Amount", f"{monto - soli:,.2f}"]
    ]
    t_tms = Table(data_tms)
    t_tms.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.black),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.red),
        ('FONTNAME', (0,0), (-1,-1), 'Courier-Bold')
    ]))
    elements.append(t_tms)

    doc.build(elements)
    print("✅ PDF Experto Generado")