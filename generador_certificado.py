from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from datetime import datetime

def generar_reporte_pdf(datos):
    nombre_pdf = f"Informe_V23_Liquidacion_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- CABECERA ---
    elements.append(Paragraph(f"AUDITORÍA PERICIAL FIFA (V23)", styles['Heading1']))
    elements.append(Paragraph(f"Liquidación Financiera Correcta (Deducción vs Adición)", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # --- DATOS BASICOS ---
    acuerdo = datos.get('acuerdo_transferencia', {})
    jugador = datos.get('jugador', {})
    orig = acuerdo.get('club_origen', {}) or {"nombre": "Desconocido"}
    dest = acuerdo.get('club_destino', {})
    monto_bruto = acuerdo.get('monto_fijo_total', 0)
    
    # --- 1. DATOS OPERACION ---
    data_trans = [
        ["JUGADOR", jugador.get('nombre_completo')],
        ["VENDEDOR (ORIGEN)", f"{orig.get('nombre')} ({orig.get('pais_asociacion', '-')})"],
        ["COMPRADOR (DESTINO)", f"{dest.get('nombre')} ({dest.get('pais_asociacion', '-')})"],
        ["MONTO BRUTO ACORDADO", f"{monto_bruto:,.2f} EUR"]
    ]
    t_trans = Table(data_trans, colWidths=[5*cm, 9*cm])
    t_trans.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold')
    ]))
    elements.append(t_trans)
    elements.append(Spacer(1, 0.8*cm))

    # --- RECUPERAR CALCULOS ---
    calculos = datos.get('calculos_auditoria', {})
    lista_sol = calculos.get('lista_solidaridad', [])
    lista_form = calculos.get('lista_formacion', [])
    total_sol = calculos.get('total_solidaridad', 0)
    total_form = calculos.get('total_formacion', 0)

    # --- 2. TABLAS DETALLE (Igual que antes) ---
    # SOLIDARIDAD
    elements.append(Paragraph("A. DESGLOSE SOLIDARIDAD (Retención del 5%)", styles['Heading3']))
    if lista_sol:
        data_sol = [["Beneficiario", "Periodo", "%", "Monto Retenido"]]
        for r in lista_sol:
            data_sol.append([r['club'], r.get('periodo'), r.get('porcentaje'), f"{r['monto']:,.2f} €"])
        data_sol.append(["TOTAL A RETENER", "", "", f"{total_sol:,.2f} EUR"])
        t_sol = Table(data_sol, colWidths=[7*cm, 4*cm, 2*cm, 4*cm])
        t_sol.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1565C0")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_sol)
    else: elements.append(Paragraph("No aplica.", styles['Italic']))

    elements.append(Spacer(1, 0.5*cm))

    # FORMACION
    elements.append(Paragraph("B. DESGLOSE FORMACIÓN (Coste Adicional)", styles['Heading3']))
    if lista_form:
        data_form = [["Beneficiario", "Cat/Edad", "Nota", "Monto Extra"]]
        for r in lista_form:
            m = f"{r['monto']:,.2f} €" if r['monto'] > 0 else "---"
            data_form.append([r['club'], r.get('cat_periodo'), r['nota'], m])
        data_form.append(["TOTAL FORMACIÓN", "", "", f"{total_form:,.2f} EUR"])
        t_form = Table(data_form, colWidths=[7*cm, 4*cm, 3*cm, 3*cm])
        t_form.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2E7D32")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_form)
    else: elements.append(Paragraph("No aplica.", styles['Italic']))

    elements.append(Spacer(1, 1*cm))

    # =========================================================================
    # --- 3. LIQUIDACIÓN FINANCIERA (EL CORAZÓN DE LA V23) ---
    # =========================================================================
    
    elements.append(Paragraph("3. LIQUIDACIÓN FINAL DE LA OPERACIÓN (CLEARING STATEMENT)", styles['Heading2']))
    
    # Cálculos Financieros Reales
    neto_vendedor = monto_bruto - total_sol
    coste_total_comprador = monto_bruto + total_form
    
    data_final = [
        ["CONCEPTO", "NATURALEZA", "IMPACTO", "MONTO"],
        ["1. Monto Bruto Acordado", "Precio Fijo", "Base", f"{monto_bruto:,.2f} EUR"],
        ["2. (-) Retención Solidaridad", "Deducción (A distribuir)", "Resta al Vendedor", f"- {total_sol:,.2f} EUR"],
        ["3. (=) Neto Estimado al Vendedor", "Pago Principal", "Ingreso Vendedor", f"{neto_vendedor:,.2f} EUR"],
        ["4. (+) Indemnización Formación", "Coste Regulatorio", "Suma al Comprador", f"+ {total_form:,.2f} EUR"],
        ["COSTE TOTAL PARA COMPRADOR", "", "SALIDA DE CAJA", f"{coste_total_comprador:,.2f} EUR"]
    ]
    
    t_final = Table(data_final, colWidths=[6*cm, 4*cm, 3.5*cm, 4*cm])
    t_final.setStyle(TableStyle([
        # Cabecera
        ('BACKGROUND', (0,0), (-1,0), colors.black),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        
        # Columna Montos a la derecha
        ('ALIGN', (3,1), (3,-1), 'RIGHT'),
        
        # Fila de Neto al Vendedor (Gris claro para resaltar)
        ('BACKGROUND', (0,3), (-1,3), colors.lightgrey),
        ('FONTNAME', (0,3), (-1,3), 'Helvetica-Bold'),

        # Fila FINAL (Dorado)
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FFD700")), 
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
        ('FONTSIZE', (0,-1), (-1,-1), 11),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('TOPPADDING', (0,-1), (-1,-1), 8),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 8),
    ]))
    
    elements.append(t_final)
    
    # Nota Explicativa
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("NOTA: La Solidaridad (5%) se deduce del monto bruto acordado (el Vendedor recibe el neto). La Formación es un coste adicional que el Comprador debe abonar aparte. Cálculo sujeto a que el contrato no especifique 'Libre de impuestos/deducciones' (Net Fee).", styles['Italic']))

    doc.build(elements)
    return nombre_pdf