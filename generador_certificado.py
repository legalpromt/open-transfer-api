from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

def generar_reporte_pdf(datos):
    nombre_pdf = f"Informe_V20_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # TITULO
    elements.append(Paragraph(f"AUDITORÍA PERICIAL FIFA (V20)", styles['Heading1']))
    elements.append(Paragraph("Doble Verificación: Solidaridad y Formación", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # 1. DATOS OPERACION
    acuerdo = datos.get('acuerdo_transferencia', {})
    dest = acuerdo.get('club_destino', {})
    orig = acuerdo.get('club_origen', {}) or {"nombre": "Desconocido"}
    
    data_resumen = [
        ["JUGADOR", datos['jugador']['nombre_completo']],
        ["ORIGEN (VENDEDOR)", f"{orig.get('nombre', '-')} ({orig.get('pais_asociacion', '-')})"],
        ["DESTINO (COMPRADOR)", f"{dest.get('nombre')} ({dest.get('pais_asociacion')})"],
        ["MONTO / TIPO", f"{acuerdo.get('monto_fijo_total', 0):,.2f} EUR"]
    ]
    
    t_res = Table(data_resumen, colWidths=[6*cm, 10*cm])
    t_res.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))
    elements.append(t_res)
    elements.append(Spacer(1, 1*cm))

    # A. SOLIDARIDAD
    elements.append(Paragraph("A. MECANISMO DE SOLIDARIDAD (5%)", styles['Heading2']))
    lista_sol = datos['calculos_auditoria'].get('lista_solidaridad', [])
    
    if lista_sol:
        data_sol = [["Club", "Edad", "%", "Monto"]]
        total = 0
        for r in lista_sol:
            data_sol.append([r['club'], r['periodo'], r['porcentaje'], f"{r['monto']:,.2f} €"])
            total += r['monto']
        data_sol.append(["TOTAL", "", "", f"{total:,.2f} €"])
        t_sol = Table(data_sol, colWidths=[7*cm, 3*cm, 2*cm, 4*cm])
        t_sol.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1565C0")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_sol)
    else: elements.append(Paragraph("No aplica.", styles['Normal']))

    elements.append(Spacer(1, 0.5*cm))

    # B. FORMACION
    elements.append(Paragraph("B. INDEMNIZACIÓN POR FORMACIÓN", styles['Heading2']))
    lista_form = datos['calculos_auditoria'].get('lista_formacion', [])
    
    if lista_form:
        data_form = [["Club", "Cat/Edad", "Nota", "Monto"]]
        total = 0
        for r in lista_form:
            txt_monto = f"{r['monto']:,.2f} €" if r['monto'] > 0 else "---"
            data_form.append([r['club'], r['cat_periodo'], r['nota'], txt_monto])
            total += r['monto']
        data_form.append(["TOTAL", "", "", f"{total:,.2f} €"])
        t_form = Table(data_form, colWidths=[7*cm, 4*cm, 3*cm, 2*cm])
        t_form.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2E7D32")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_form)
    else: elements.append(Paragraph("No aplica.", styles['Normal']))

    doc.build(elements)
    return nombre_pdf