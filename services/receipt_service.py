import os
import qrcode
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECEIPTS_DIR = os.path.join(BASE_DIR, 'receipts')
LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'school_logo.png')
os.makedirs(RECEIPTS_DIR, exist_ok=True)


def generate_qr(data: str) -> BytesIO:
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def get_next_receipt_number(session) -> str:
    from models.database import Receipt, get_session
    year = datetime.now().year
    count = session.query(Receipt).filter(Receipt.receipt_number.like(f'REC-{year}-%')).count()
    return f'REC-{year}-{count + 1:06d}'


def generate_receipt_pdf(session, student, payment, payment_type_label: str):
    receipt_number = get_next_receipt_number(session)
    filename = f'{receipt_number}.pdf'
    filepath = os.path.join(RECEIPTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A5,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    story = []

    title_style = ParagraphStyle('title', fontSize=16, textColor=colors.HexColor('#0044cc'),
                                 alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=2)
    sub_style = ParagraphStyle('sub', fontSize=9, textColor=colors.HexColor('#333333'),
                               alignment=TA_CENTER, fontName='Helvetica-Oblique')
    value_style = ParagraphStyle('value', fontSize=9, textColor=colors.HexColor('#111111'),
                                 fontName='Helvetica-Bold')
    amount_style = ParagraphStyle('amount', fontSize=22, textColor=colors.HexColor('#0044cc'),
                                  alignment=TA_CENTER, fontName='Helvetica-Bold')
    small_style = ParagraphStyle('small', fontSize=8, textColor=colors.HexColor('#888888'),
                                 alignment=TA_CENTER)
    sh_style = ParagraphStyle('sh', fontSize=10, textColor=colors.HexColor('#0044cc'),
                              fontName='Helvetica-Bold', spaceBefore=4, spaceAfter=3)

    # Logo row
    if os.path.exists(LOGO_PATH):
        try:
            logo = RLImage(LOGO_PATH, width=20*mm, height=20*mm)
            logo_table = Table([[logo, Paragraph('<b>Le Schéma</b>', title_style)]], colWidths=[25*mm, None])
            logo_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
            story.append(logo_table)
        except:
            story.append(Paragraph('<b>Le Schéma</b>', title_style))
    else:
        story.append(Paragraph('<b>Le Schéma</b>', title_style))

    story.append(Paragraph('Innover - Créer - Exceller', sub_style))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#0044cc')))
    story.append(Spacer(1, 3*mm))

    rec_style = ParagraphStyle('rec', fontSize=13, textColor=colors.HexColor('#ffffff'),
                               alignment=TA_CENTER, fontName='Helvetica-Bold',
                               backColor=colors.HexColor('#0044cc'), borderPad=5, spaceAfter=4)
    story.append(Paragraph('REÇU DE PAIEMENT', rec_style))
    story.append(Spacer(1, 3*mm))

    meta_table = Table([[Paragraph(f'<b>N° Reçu:</b> {receipt_number}', value_style),
                         Paragraph(f'<b>Date:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}', value_style)]],
                       colWidths=[75*mm, 75*mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f4ff')),
        ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#0044cc')),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#ccddff')),
        ('PADDING',(0,0),(-1,-1),6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('INFORMATIONS ÉLÈVE', sh_style))

    student_data = [
        ['Nom complet:', f'{student.first_name} {student.last_name}'],
        ['Code élève:', student.code or '-'],
        ['Classe:', student.class_name or '-'],
        ['Parent / Tuteur:', student.parent_name or '-'],
    ]
    st = Table(student_data, colWidths=[45*mm, 105*mm])
    st.setStyle(TableStyle([
        ('FONT',(0,0),(0,-1),'Helvetica-Bold',9),('FONT',(1,0),(1,-1),'Helvetica',9),
        ('TEXTCOLOR',(0,0),(0,-1),colors.HexColor('#555555')),
        ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#dddddd')),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#eeeeee')),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,colors.HexColor('#f8f8ff')]),
        ('PADDING',(0,0),(-1,-1),5),
    ]))
    story.append(st)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('DÉTAILS DU PAIEMENT', sh_style))

    month_year = f'{payment.month} {payment.year}' if hasattr(payment,'month') and payment.month else datetime.now().strftime('%B %Y')
    pay_data = [
        ['Type de paiement:', payment_type_label],
        ['Période:', month_year],
        ['Mode de paiement:', 'Espèces'],
    ]
    pt = Table(pay_data, colWidths=[45*mm, 105*mm])
    pt.setStyle(TableStyle([
        ('FONT',(0,0),(0,-1),'Helvetica-Bold',9),('FONT',(1,0),(1,-1),'Helvetica',9),
        ('TEXTCOLOR',(0,0),(0,-1),colors.HexColor('#555555')),
        ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#dddddd')),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#eeeeee')),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,colors.HexColor('#f8f8ff')]),
        ('PADDING',(0,0),(-1,-1),5),
    ]))
    story.append(pt)
    story.append(Spacer(1, 5*mm))

    amt_box = Table([[Paragraph(f'{payment.amount:.2f} MAD', amount_style)]], colWidths=[150*mm])
    amt_box.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e8f0ff')),
        ('BOX',(0,0),(-1,-1),2,colors.HexColor('#0044cc')),
        ('PADDING',(0,0),(-1,-1),10),('ALIGN',(0,0),(-1,-1),'CENTER'),
    ]))
    story.append(amt_box)
    story.append(Spacer(1, 5*mm))

    qr_buf = generate_qr(f'REC:{receipt_number}|STU:{student.code}|AMT:{payment.amount}|TYPE:{payment_type_label}')
    qr_img = RLImage(qr_buf, width=18*mm, height=18*mm)
    sig_style = ParagraphStyle('sig', fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#333333'))
    sig_block = [Paragraph('Signature & Cachet', sig_style), Spacer(1, 12*mm),
                 HRFlowable(width=50*mm, thickness=0.5, color=colors.HexColor('#999999')),
                 Paragraph('Responsable financier', sig_style)]
    bot = Table([[qr_img, sig_block]], colWidths=[30*mm, 120*mm])
    bot.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(0,0),'CENTER'),('ALIGN',(1,0),(1,0),'CENTER')]))
    story.append(bot)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#dddddd')))
    story.append(Paragraph('Ce reçu est un document officiel. Merci pour votre confiance. — Le Schéma', small_style))

    doc.build(story)
    return filepath, receipt_number
