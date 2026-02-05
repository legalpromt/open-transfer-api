from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from datetime import datetime

def generar_reporte_pdf(datos):
    nombre_pdf = f"Informe_V22_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # CABECERA
    elements.append(Paragraph(f"AUDITORÍA PERICIAL FIFA (V22)", styles['Heading1']))
    elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # 1. DATOS DE LA OPERACIÓN
    acuerdo = datos.get('acuerdo_transferencia', {})
    jugador = datos.get('jugador', {})
    orig = acuerdo.get('club_origen', {}) or {"nombre": "Desconocido"}
    dest = acuerdo.get('club_destino', {})
    monto_trans = acuerdo.get('monto_fijo_total', 0)
    
    data_trans = [
        ["JUGADOR", jugador.get('nombre_completo')],
        ["VENDEDOR", f"{orig.get('nombre')} ({orig.get('pais_asociacion', '-')})"],
        ["COMPRADOR", f"{dest.get('nombre')} ({dest.get('pais_asociacion', '-')})"],
        ["MONTO FIJO", f"{monto_trans:,.2f} EUR"]
    ]
    t_trans = Table(data_trans, colWidths=[4*cm, 10*cm])
    t_trans.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (0,-1), colors.lightgrey), ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold')]))
    elements.append(t_trans)
    elements.append(Spacer(1, 0.5*cm))

    # 2. SOLIDARIDAD
    calculos = datos.get('calculos_auditoria', {})
    lista_sol = calculos.get('lista_solidaridad', [])
    total_sol = calculos.get('total_solidaridad', 0)

    elements.append(Paragraph("A. MECANISMO DE SOLIDARIDAD (5%)", styles['Heading2']))
    if lista_sol:
        data_sol = [["Club", "Periodo", "%", "Monto"]]
        for r in lista_sol:
            data_sol.append([r['club'], r.get('periodo'), r.get('porcentaje'), f"{r['monto']:,.2f} €"])
        data_sol.append(["TOTAL SOLIDARIDAD", "", "", f"{total_sol:,.2f} EUR"])
        t_sol = Table(data_sol, colWidths=[7*cm, 4*cm, 2*cm, 4*cm])
        t_sol.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1565C0")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_sol)
    else: elements.append(Paragraph("No aplica.", styles['Normal']))

    elements.append(Spacer(1, 0.5*cm))

    # 3. FORMACIÓN
    lista_form = calculos.get('lista_formacion', [])
    total_form = calculos.get('total_formacion', 0)

    elements.append(Paragraph("B. INDEMNIZACIÓN POR FORMACIÓN", styles['Heading2']))
    if lista_form:
        data_form = [["Club", "Cat/Edad", "Nota", "Monto"]]
        for r in lista_form:
            m_txt = f"{r['monto']:,.2f} €" if r['monto'] > 0 else "---"
            data_form.append([r['club'], r.get('cat_periodo'), r['nota'], m_txt])
        data_form.append(["TOTAL FORMACIÓN", "", "", f"{total_form:,.2f} EUR"])
        t_form = Table(data_form, colWidths=[7*cm, 4*cm, 3*cm, 3*cm])
        t_form.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2E7D32")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_form)
    else: elements.append(Paragraph("No aplica.", styles['Normal']))

    elements.append(Spacer(1, 1*cm))

    # 4. RESUMEN FINAL
    elements.append(Paragraph("RESUMEN EJECUTIVO (CLEARING HOUSE)", styles['Heading2']))
    total_op = monto_trans + total_sol + total_form
    
    data_final = [
        ["CONCEPTO", "MONTO"],
        ["1. Principal Transferencia", f"{monto_trans:,.2f} EUR"],
        ["2. Total Solidaridad", f"{total_sol:,.2f} EUR"],
        ["3. Total Formación", f"{total_form:,.2f} EUR"],
        ["COSTE TOTAL OPERACIÓN", f"{total_op:,.2f} EUR"]
    ]
    t_final = Table(data_final, colWidths=[10*cm, 5*cm])
    t_final.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.black), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FFD700")), # Dorado
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT')
    ]))
    elements.append(t_final)

    doc.build(elements)
    return nombre_pdf