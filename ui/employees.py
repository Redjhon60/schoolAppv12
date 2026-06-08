"""
employees.py — SGS v4
Employee management + full Salary v4:
  - Employee fields: first_name, last_name, CIN, address, phone, email, role, salary_amount, hire_date, active
  - Salary: gross_salary + bonus - deduction = net_salary
  - Duplicate prevention: one salary per employee per month
  - Payslip PDF generation (Bulletin de Paie)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QMessageBox, QDoubleSpinBox, QHeaderView, QAbstractItemView,
    QTabWidget, QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from datetime import datetime, date

from models.database import Employee, Salary, Setting
from themes.style import (DIALOG_CSS, TABLE_CSS, PRIMARY, PRIMARY_LIGHT, SUCCESS,
    SUCCESS_LIGHT, DANGER, DANGER_LIGHT, WARNING, WARNING_LIGHT, BORDER, BG_CARD,
    TEXT_MAIN, TEXT_SUB, MONTHS)

BTN       = f'QPushButton {{ background: {PRIMARY}; color: white; border: none; border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px; }} QPushButton:hover {{ background: #4338CA; }}'
BTN_SEC   = 'QPushButton { background: #F3F4F6; color: #374151; border: 1px solid #E5E7EB; border-radius: 8px; padding: 9px 20px; font-weight: 500; font-size: 13px; } QPushButton:hover { background: #E5E7EB; }'
BTN_DANGER  = f'QPushButton {{ background: {DANGER_LIGHT}; color: #DC2626; border: 1px solid #FECACA; border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px; }} QPushButton:hover {{ background: #FECACA; }}'
BTN_SUCCESS = f'QPushButton {{ background: {SUCCESS}; color: white; border: none; border-radius: 8px; padding: 9px 20px; font-weight: 700; font-size: 13px; }} QPushButton:hover {{ background: #059669; }}'
FIELD_CSS   = (f'QLineEdit, QDoubleSpinBox, QDateEdit, QComboBox, QTextEdit {{ '
               f'background: white; border: 1.5px solid {BORDER}; border-radius: 10px; '
               f'color: {TEXT_MAIN}; padding: 0 12px; font-size: 13px; min-height: 38px; }}'
               f'QLineEdit:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{ border-color: {PRIMARY}; }}'
               f'QTextEdit {{ padding: 8px 12px; min-height: 56px; }}'
               f'QComboBox QAbstractItemView {{ background: white; border: 1.5px solid #C7D2FE; '
               f'border-radius: 10px; color: {TEXT_MAIN}; padding: 4px; outline: none; }}'
               f'QComboBox QAbstractItemView::item {{ padding: 9px 14px; border-radius: 6px; '
               f'margin: 1px 4px; color: {TEXT_MAIN}; }}'
               f'QComboBox QAbstractItemView::item:hover {{ background: #F5F3FF; color: {PRIMARY}; }}'
               f'QComboBox QAbstractItemView::item:selected {{ background: {PRIMARY_LIGHT}; color: {PRIMARY}; }}')
TAB_CSS = f"""
    QTabWidget::pane {{ border: none; background: transparent; }}
    QTabBar::tab {{ background: transparent; color: {TEXT_SUB}; border: none;
        border-bottom: 2px solid transparent; padding: 10px 24px;
        font-size: 13px; font-weight: 500; margin-right: 4px; }}
    QTabBar::tab:selected {{ color: {PRIMARY}; border-bottom: 2px solid {PRIMARY}; font-weight: 700; }}
    QTabBar::tab:hover:!selected {{ color: {TEXT_MAIN}; background: #F9FAFB;
        border-radius: 8px 8px 0 0; }}
"""

ROLES = [
    ('👨‍🏫 Enseignant', 'teacher'),
    ('👔 Personnel',   'staff'),
    ('🚌 Chauffeur',   'driver'),
    ('⚙️ Admin',       'admin'),
    ('🔧 Maintenance', 'maintenance'),
]
ROLE_LABELS = {r: l for l, r in ROLES}


def flbl(text):
    l = QLabel(text)
    l.setStyleSheet('color: #374151; font-size: 12px; font-weight: 600; background: transparent;')
    return l


def section_hdr(icon, title, color=None):
    color = color or PRIMARY
    frame = QFrame()
    frame.setStyleSheet(f'QFrame {{ background: {color}; border-radius: 0; }}')
    frame.setFixedHeight(56)
    hl = QHBoxLayout(frame); hl.setContentsMargins(24, 0, 24, 0)
    lbl = QLabel(f'{icon}  {title}')
    lbl.setStyleSheet('color: white; font-size: 15px; font-weight: 700; background: transparent;')
    hl.addWidget(lbl)
    return frame


# ── Employee Dialog ───────────────────────────────────────────────────────────

class EmployeeDialog(QDialog):
    def __init__(self, parent=None, employee=None):
        super().__init__(parent)
        self.employee = employee
        self.setWindowTitle('Modifier employé' if employee else 'Nouvel employé')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 640, 600)
        self.setStyleSheet(DIALOG_CSS + f'QDialog {{ background: #F7F8FC; }}{FIELD_CSS}')
        self._setup_ui()
        if employee:
            self._populate(employee)

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        outer.addWidget(section_hdr('👤', 'Modifier employé' if self.employee else 'Ajouter un employé'))

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        content = QWidget(); content.setStyleSheet('background: transparent;')
        form = QFormLayout(content)
        form.setContentsMargins(28, 24, 28, 16); form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.first_name = QLineEdit(); self.first_name.setPlaceholderText('Prénom')
        self.last_name  = QLineEdit(); self.last_name.setPlaceholderText('Nom')
        self.cin        = QLineEdit(); self.cin.setPlaceholderText('AA999999')
        self.role       = QComboBox()
        for display, val in ROLES:
            self.role.addItem(display, val)
        self.phone      = QLineEdit(); self.phone.setPlaceholderText('0600000000')
        self.email      = QLineEdit(); self.email.setPlaceholderText('email@example.com')
        self.address    = QTextEdit(); self.address.setMaximumHeight(70)
        self.hire_date  = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate())
        self.base_salary = QDoubleSpinBox()
        self.base_salary.setRange(0, 99999); self.base_salary.setSuffix(' MAD')
        self.base_salary.setDecimals(2)

        form.addRow(flbl('Prénom *:'),        self.first_name)
        form.addRow(flbl('Nom *:'),           self.last_name)
        form.addRow(flbl('CIN:'),             self.cin)
        form.addRow(flbl('Poste:'),           self.role)
        form.addRow(flbl('Téléphone:'),       self.phone)
        form.addRow(flbl('Email:'),           self.email)
        form.addRow(flbl('Adresse:'),         self.address)
        form.addRow(flbl('Date d\'embauche:'), self.hire_date)
        form.addRow(flbl('Salaire de base:'), self.base_salary)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background: white; border-top: 1px solid {BORDER}; }}')
        footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24, 0, 24, 0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        save = QPushButton('💾  Enregistrer'); save.setStyleSheet(BTN); save.clicked.connect(self._save)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(save)
        outer.addWidget(footer)

    def _populate(self, e):
        self.first_name.setText(e.first_name or '')
        self.last_name.setText(e.last_name or '')
        self.cin.setText(e.cin or '')
        idx = self.role.findData(e.role)
        if idx >= 0: self.role.setCurrentIndex(idx)
        self.phone.setText(e.phone or '')
        self.email.setText(e.email or '')
        self.address.setText(e.address or '')
        if e.hire_date:
            self.hire_date.setDate(QDate(e.hire_date.year, e.hire_date.month, e.hire_date.day))
        self.base_salary.setValue(e.base_salary or 0)

    def _save(self):
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            QMessageBox.warning(self, 'Erreur', 'Prénom et nom sont obligatoires.')
            return
        self.accept()

    def get_data(self):
        hd = self.hire_date.date()
        return {
            'first_name':   self.first_name.text().strip(),
            'last_name':    self.last_name.text().strip(),
            'cin':          self.cin.text().strip(),
            'role':         self.role.currentData(),
            'phone':        self.phone.text().strip(),
            'email':        self.email.text().strip(),
            'address':      self.address.toPlainText().strip(),
            'hire_date':    date(hd.year(), hd.month(), hd.day()),
            'base_salary':  self.base_salary.value(),
        }


# ── Salary Dialog ─────────────────────────────────────────────────────────────

class SalaryDialog(QDialog):
    """
    v4 Salary Dialog:
      Net = Gross + Bonus - Deduction
      Duplicate prevention: one salary per employee per month.
      Generates PDF payslip (Bulletin de Paie).
    """
    def __init__(self, parent, employee: Employee, session):
        super().__init__(parent)
        self.employee = employee
        self.session = session
        self.setWindowTitle(f'Salaire — {employee.first_name} {employee.last_name}')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 580, 540)
        self.setStyleSheet(DIALOG_CSS + f'QDialog {{ background: #F7F8FC; }}{FIELD_CSS}')
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        outer.addWidget(section_hdr('💰',
            f'Bulletin de salaire — {self.employee.first_name} {self.employee.last_name}',
            SUCCESS))

        content = QWidget(); content.setStyleSheet('background: transparent;')
        cl = QVBoxLayout(content); cl.setContentsMargins(28, 22, 28, 16); cl.setSpacing(14)

        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)

        self.month_combo = QComboBox()
        self.month_combo.addItems(MONTHS)

        self.year_input = QLineEdit(str(datetime.now().year))
        self.year_input.setMaximumWidth(120)

        self.gross = QDoubleSpinBox()
        self.gross.setRange(0, 999999); self.gross.setSuffix(' MAD'); self.gross.setDecimals(2)
        self.gross.setValue(self.employee.base_salary or 0)

        self.bonus = QDoubleSpinBox()
        self.bonus.setRange(0, 999999); self.bonus.setSuffix(' MAD'); self.bonus.setDecimals(2)

        self.deduction = QDoubleSpinBox()
        self.deduction.setRange(0, 999999); self.deduction.setSuffix(' MAD'); self.deduction.setDecimals(2)

        self.notes = QLineEdit(); self.notes.setPlaceholderText('Note optionnelle...')

        for spin in (self.gross, self.bonus, self.deduction):
            spin.valueChanged.connect(self._update_net)

        form.addRow(flbl('Mois:'),           self.month_combo)
        form.addRow(flbl('Année:'),          self.year_input)
        form.addRow(flbl('Salaire brut:'),   self.gross)
        form.addRow(flbl('Prime / Bonus:'),  self.bonus)
        form.addRow(flbl('Déduction:'),      self.deduction)
        form.addRow(flbl('Notes:'),          self.notes)
        cl.addLayout(form)

        # Net salary display card
        net_frame = QFrame()
        net_frame.setStyleSheet(
            f'QFrame {{ background: {SUCCESS_LIGHT}; border-radius: 12px; '
            f'border: 1px solid #A7F3D0; border-left: 5px solid {SUCCESS}; }}'
        )
        ncl = QVBoxLayout(net_frame); ncl.setContentsMargins(20, 14, 20, 14); ncl.setSpacing(4)
        formula_lbl = QLabel('Brut  +  Bonus  −  Déduction  =  NET')
        formula_lbl.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; background: transparent;')
        self.net_lbl = QLabel(f'{self.employee.base_salary or 0:.2f} MAD')
        self.net_lbl.setStyleSheet(
            f'color: {SUCCESS}; font-size: 28px; font-weight: 800; background: transparent;'
        )
        ncl.addWidget(formula_lbl); ncl.addWidget(self.net_lbl)
        cl.addWidget(net_frame)
        cl.addStretch()
        outer.addWidget(content, 1)

        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background: white; border-top: 1px solid {BORDER}; }}')
        footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24, 0, 24, 0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        pay_btn = QPushButton('✅  Valider & Générer Bulletin')
        pay_btn.setStyleSheet(BTN_SUCCESS)
        pay_btn.clicked.connect(self._save)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(pay_btn)
        outer.addWidget(footer)

    def _update_net(self):
        net = self.gross.value() + self.bonus.value() - self.deduction.value()
        self.net_lbl.setText(f'{net:.2f} MAD')
        color = SUCCESS if net >= 0 else DANGER
        self.net_lbl.setStyleSheet(
            f'color: {color}; font-size: 28px; font-weight: 800; background: transparent;'
        )

    def _save(self):
        month = self.month_combo.currentText()
        try:
            year = int(self.year_input.text())
        except ValueError:
            year = datetime.now().year

        # ── Duplicate check ───────────────────────────────────────────────────
        existing = self.session.query(Salary).filter_by(
            employee_id=self.employee.id,
            month=month,
            year=year,
        ).first()
        if existing:
            QMessageBox.warning(
                self, 'Doublon',
                f'Un bulletin de salaire pour {self.employee.first_name} '
                f'{self.employee.last_name} en {month} {year} existe déjà.'
            )
            return

        gross     = self.gross.value()
        bonus     = self.bonus.value()
        deduction = self.deduction.value()
        net       = gross + bonus - deduction

        # Receipt number
        count = self.session.query(Salary).count() + 1
        rec_num = f'SAL-{year}-{count:05d}'

        sal = Salary(
            employee_id  = self.employee.id,
            month        = month,
            year         = year,
            gross_salary = gross,
            bonus        = bonus,
            deduction    = deduction,
            net_salary   = net,
            # backward compat
            base_amount  = gross,
            total        = net,
            paid         = True,
            paid_date    = datetime.now(),
            payment_date = datetime.now(),
            receipt_number = rec_num,
            notes        = self.notes.text().strip(),
        )
        self.session.add(sal)
        self.session.commit()

        # Generate payslip PDF
        pdf_path = None
        try:
            pdf_path = self._generate_payslip(sal, net)
        except Exception as e:
            print(f'Payslip generation error: {e}')

        msg = (f'✅ Salaire enregistré\n\n'
               f'Employé : {self.employee.first_name} {self.employee.last_name}\n'
               f'CIN     : {self.employee.cin or "—"}\n'
               f'Mois    : {month} {year}\n'
               f'Brut    : {gross:.2f} MAD\n'
               f'Bonus   : {bonus:.2f} MAD\n'
               f'Déd.    : {deduction:.2f} MAD\n'
               f'NET     : {net:.2f} MAD\n'
               f'N° Reçu : {rec_num}')

        if pdf_path:
            reply = QMessageBox.question(
                self, 'Succès', msg + '\n\nOuvrir le bulletin de paie ?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._open_file(pdf_path)
        else:
            QMessageBox.information(self, 'Succès', msg)

        self.accept()

    def _generate_payslip(self, sal: Salary, net: float) -> str:
        """Generate PDF Bulletin de Paie using reportlab."""
        from services.receipt_service import get_receipts_dir
        import os

        receipts_dir = get_receipts_dir()
        filename = f'PAYSLIP-{sal.receipt_number}.pdf'
        filepath = os.path.join(receipts_dir, filename)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            doc = SimpleDocTemplate(filepath, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle('title', fontSize=18, fontName='Helvetica-Bold',
                                         textColor=colors.HexColor('#1A1D2E'),
                                         spaceAfter=6)
            sub_style = ParagraphStyle('sub', fontSize=11, fontName='Helvetica',
                                       textColor=colors.HexColor('#6B7280'), spaceAfter=16)
            body_style = ParagraphStyle('body', fontSize=11, fontName='Helvetica',
                                        textColor=colors.HexColor('#374151'))
            label_style = ParagraphStyle('label', fontSize=10, fontName='Helvetica-Bold',
                                         textColor=colors.HexColor('#6B7280'))
            amount_style = ParagraphStyle('amount', fontSize=13, fontName='Helvetica-Bold',
                                          textColor=colors.HexColor('#059669'))

            story.append(Paragraph('BULLETIN DE PAIE', title_style))
            story.append(Paragraph(f'Période : {sal.month} {sal.year}', sub_style))

            # Employee info table
            emp_data = [
                ['Employé',    f'{self.employee.first_name} {self.employee.last_name}',
                 'N° Bulletin', sal.receipt_number],
                ['CIN',         self.employee.cin or '—',
                 'Date',        sal.payment_date.strftime('%d/%m/%Y') if sal.payment_date else '—'],
                ['Poste',       ROLE_LABELS.get(self.employee.role, self.employee.role or '—'),
                 'Adresse',     (self.employee.address or '—')[:40]],
            ]
            emp_table = Table(emp_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
            emp_table.setStyle(TableStyle([
                ('FONTNAME',    (0,0), (-1,-1), 'Helvetica'),
                ('FONTNAME',    (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTNAME',    (2,0), (2,-1), 'Helvetica-Bold'),
                ('FONTSIZE',    (0,0), (-1,-1), 10),
                ('TEXTCOLOR',   (0,0), (0,-1), colors.HexColor('#6B7280')),
                ('TEXTCOLOR',   (2,0), (2,-1), colors.HexColor('#6B7280')),
                ('BACKGROUND',  (0,0), (-1,-1), colors.HexColor('#F9FAFB')),
                ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#F9FAFB'), colors.white]),
                ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('PADDING',     (0,0), (-1,-1), 8),
                ('ROUNDED',     (0,0), (-1,-1), 4),
            ]))
            story.append(emp_table)
            story.append(Spacer(1, 0.5*cm))

            # Salary breakdown
            salary_data = [
                ['', 'Libellé', 'Montant'],
                ['+', 'Salaire brut', f'{sal.gross_salary:,.2f} MAD'],
                ['+', f'Prime / Bonus', f'{sal.bonus:,.2f} MAD'],
                ['−', 'Déduction', f'{sal.deduction:,.2f} MAD'],
                ['=', 'SALAIRE NET', f'{net:,.2f} MAD'],
            ]
            sal_table = Table(salary_data, colWidths=[1*cm, 10*cm, 6*cm])
            sal_table.setStyle(TableStyle([
                ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',    (0,0), (-1,-1), 11),
                ('BACKGROUND',  (0,0), (-1,0), colors.HexColor('#1A1D2E')),
                ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
                ('BACKGROUND',  (0,-1), (-1,-1), colors.HexColor('#ECFDF5')),
                ('FONTNAME',    (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('TEXTCOLOR',   (0,-1), (-1,-1), colors.HexColor('#059669')),
                ('FONTSIZE',    (0,-1), (-1,-1), 13),
                ('ROWBACKGROUNDS', (0,1), (-1,-2),
                 [colors.white, colors.HexColor('#F9FAFB')]),
                ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('ALIGN',       (2,0), (2,-1), 'RIGHT'),
                ('PADDING',     (0,0), (-1,-1), 10),
            ]))
            story.append(sal_table)

            if sal.notes:
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph(f'Notes : {sal.notes}', body_style))

            doc.build(story)
            return filepath
        except Exception as e:
            print(f'PDF error: {e}')
            return None

    def _open_file(self, path):
        import subprocess, platform
        if platform.system() == 'Linux':
            subprocess.Popen(['xdg-open', path])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', path])
        else:
            try: os.startfile(path)
            except Exception: pass


# ── Main EmployeesWidget ──────────────────────────────────────────────────────

class EmployeesWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.all_employees = []
        self.setStyleSheet('background: transparent;')
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        tabs = QTabWidget()
        tabs.setStyleSheet(TAB_CSS)

        # ── Employees tab ─────────────────────────────────────────────────────
        emp_tab = QWidget(); emp_tab.setStyleSheet('background: transparent;')
        el = QVBoxLayout(emp_tab); el.setContentsMargins(0, 16, 0, 0); el.setSpacing(14)

        tb = QHBoxLayout(); tb.setSpacing(10)
        self.search_emp = QLineEdit()
        self.search_emp.setPlaceholderText('🔍  Rechercher...')
        self.search_emp.setFixedHeight(40); self.search_emp.setFixedWidth(260)
        self.search_emp.setStyleSheet(
            f'QLineEdit {{ background: white; border: 1.5px solid {BORDER}; '
            f'border-radius: 10px; color: {TEXT_MAIN}; padding: 0 14px; font-size: 13px; }}'
            f'QLineEdit:focus {{ border-color: {PRIMARY}; }}'
        )
        self.search_emp.textChanged.connect(self._filter_employees)

        self.role_filter = QComboBox()
        self.role_filter.setFixedHeight(40)
        self.role_filter.addItem('Tous les postes', '')
        for display, val in ROLES:
            self.role_filter.addItem(display, val)
        self.role_filter.setStyleSheet(
            f'QComboBox {{ background: white; border: 1.5px solid {BORDER}; '
            f'border-radius: 10px; color: {TEXT_MAIN}; padding: 0 12px; '
            f'font-size: 13px; min-width: 160px; }}'
        )
        self.role_filter.currentIndexChanged.connect(self._filter_employees)

        add_btn = QPushButton('＋  Ajouter employé')
        add_btn.setFixedHeight(40); add_btn.setStyleSheet(BTN)
        add_btn.clicked.connect(self._add_employee)

        tb.addWidget(self.search_emp); tb.addWidget(self.role_filter)
        tb.addStretch(); tb.addWidget(add_btn)
        el.addLayout(tb)

        # Summary chips
        self.emp_chips = QHBoxLayout(); self.emp_chips.setSpacing(8)
        el.addLayout(self.emp_chips)

        # Table
        tcard = QFrame()
        tcard.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 14px; }}')
        tcl = QVBoxLayout(tcard); tcl.setContentsMargins(0, 0, 0, 0)
        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(8)
        self.emp_table.setHorizontalHeaderLabels(
            ['Prénom', 'Nom', 'CIN', 'Poste', 'Téléphone', 'Email', 'Embauché le', 'Salaire base']
        )
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.emp_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.emp_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.emp_table.setAlternatingRowColors(True)
        self.emp_table.verticalHeader().setVisible(False)
        self.emp_table.setShowGrid(False)
        self.emp_table.setStyleSheet(TABLE_CSS)
        tcl.addWidget(self.emp_table)
        el.addWidget(tcard, 1)

        # Actions
        ab = QHBoxLayout(); ab.setSpacing(8)
        self.emp_status = QLabel()
        self.emp_status.setStyleSheet('color: #9CA3AF; font-size: 12px; background: transparent;')
        edit_btn  = QPushButton('✏️  Modifier');   edit_btn.setStyleSheet(BTN_SEC)
        del_btn   = QPushButton('🗑️  Supprimer');  del_btn.setStyleSheet(BTN_DANGER)
        sal_btn   = QPushButton('💰  Payer salaire'); sal_btn.setStyleSheet(BTN_SUCCESS)
        edit_btn.clicked.connect(self._edit_employee)
        del_btn.clicked.connect(self._delete_employee)
        sal_btn.clicked.connect(self._pay_salary)
        ab.addWidget(self.emp_status); ab.addStretch()
        ab.addWidget(edit_btn); ab.addWidget(del_btn); ab.addWidget(sal_btn)
        el.addLayout(ab)

        # ── Salary history tab ────────────────────────────────────────────────
        sal_tab = QWidget(); sal_tab.setStyleSheet('background: transparent;')
        sl = QVBoxLayout(sal_tab); sl.setContentsMargins(0, 16, 0, 0); sl.setSpacing(14)

        sal_tb = QHBoxLayout()
        sal_lbl = QLabel('Historique des Salaires')
        sal_lbl.setStyleSheet(
            f'color: {TEXT_MAIN}; font-size: 15px; font-weight: 700; background: transparent;'
        )
        refresh_btn = QPushButton('↺  Actualiser')
        refresh_btn.setFixedHeight(36); refresh_btn.setStyleSheet(BTN_SEC)
        refresh_btn.clicked.connect(self._load_salary_history)
        sal_tb.addWidget(sal_lbl); sal_tb.addStretch(); sal_tb.addWidget(refresh_btn)
        sl.addLayout(sal_tb)

        # Summary chips row
        self.sal_chips = QHBoxLayout(); self.sal_chips.setSpacing(10)
        sl.addLayout(self.sal_chips)

        stcard = QFrame()
        stcard.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 14px; }}'
        )
        stcl = QVBoxLayout(stcard); stcl.setContentsMargins(0, 0, 0, 0)
        self.sal_table = QTableWidget()
        self.sal_table.setColumnCount(9)
        self.sal_table.setHorizontalHeaderLabels(
            ['Employé', 'CIN', 'Poste', 'Mois', 'Année',
             'Brut', 'Bonus', 'Déduction', 'Net']
        )
        self.sal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sal_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sal_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sal_table.setAlternatingRowColors(True)
        self.sal_table.verticalHeader().setVisible(False)
        self.sal_table.setShowGrid(False)
        self.sal_table.setStyleSheet(TABLE_CSS)
        stcl.addWidget(self.sal_table)
        sl.addWidget(stcard, 1)

        self.sal_total_lbl = QLabel()
        self.sal_total_lbl.setStyleSheet(
            'color: #9CA3AF; font-size: 12px; background: transparent;'
        )
        sl.addWidget(self.sal_total_lbl)

        tabs.addTab(emp_tab, '👥  Employés & Enseignants')
        tabs.addTab(sal_tab, '💰  Historique Salaires')
        layout.addWidget(tabs)

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_data(self):
        self.session.expire_all()
        self.all_employees = self.session.query(Employee).filter_by(active=True).all()
        self._populate_emp_table(self.all_employees)
        self._update_chips()
        self._load_salary_history()

    def _chip(self, text, color, bg):
        c = QLabel(text)
        c.setStyleSheet(
            f'color: {color}; background: {bg}; border-radius: 10px; '
            f'padding: 4px 12px; font-size: 11px; font-weight: 600;'
        )
        return c

    def _update_chips(self):
        for i in reversed(range(self.emp_chips.count())):
            w = self.emp_chips.itemAt(i).widget()
            if w: w.setParent(None)
        total    = len(self.all_employees)
        teachers = sum(1 for e in self.all_employees if e.role == 'teacher')
        drivers  = sum(1 for e in self.all_employees if e.role == 'driver')
        self.emp_chips.addWidget(self._chip(f'  {total} personnes', PRIMARY, PRIMARY_LIGHT))
        self.emp_chips.addWidget(self._chip(f'👨‍🏫 {teachers} enseignants', '#0369A1', '#DBEAFE'))
        self.emp_chips.addWidget(self._chip(f'🚌 {drivers} chauffeurs', '#92400E', WARNING_LIGHT))
        self.emp_chips.addStretch()
        self.emp_status.setText(f'{total} employés actifs')

    def _populate_emp_table(self, employees):
        self.emp_table.setRowCount(len(employees))
        for row, e in enumerate(employees):
            data = [
                (e.first_name or '',                                        TEXT_MAIN, True),
                (e.last_name or '',                                         TEXT_MAIN, True),
                (e.cin or '—',                                              '#6B7280', False),
                (ROLE_LABELS.get(e.role, e.role or '—'),                   '#0369A1', False),
                (e.phone or '—',                                            TEXT_MAIN, False),
                (e.email or '—',                                            TEXT_MAIN, False),
                (str(e.hire_date) if e.hire_date else '—',                  TEXT_SUB, False),
                (f'{e.base_salary:.0f} MAD',                               SUCCESS,   True),
            ]
            for col, (text, color, bold) in enumerate(data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.emp_table.setItem(row, col, item)
            self.emp_table.setRowHeight(row, 44)

    def _filter_employees(self):
        search    = self.search_emp.text().lower()
        role_data = self.role_filter.currentData()
        filtered  = [
            e for e in self.all_employees
            if (not search
                or search in (e.first_name or '').lower()
                or search in (e.last_name or '').lower()
                or search in (e.cin or '').lower())
            and (not role_data or e.role == role_data)
        ]
        self._populate_emp_table(filtered)

    def _load_salary_history(self):
        salaries = (self.session.query(Salary)
                    .order_by(Salary.year.desc(), Salary.id.desc())
                    .limit(300).all())
        self.sal_table.setRowCount(len(salaries))
        total_net = 0.0
        for row, s in enumerate(salaries):
            emp = self.session.query(Employee).filter_by(id=s.employee_id).first()
            name = f'{emp.first_name} {emp.last_name}' if emp else '—'
            cin  = (emp.cin or '—') if emp else '—'
            role = ROLE_LABELS.get(emp.role, emp.role or '—') if emp else '—'
            gross    = s.gross_salary or s.base_amount or 0
            bonus    = s.bonus or 0
            ded      = s.deduction or 0
            net      = s.net_salary or s.total or (gross + bonus - ded)
            data = [
                (name,                 TEXT_MAIN, True),
                (cin,                  '#6B7280', False),
                (role,                 '#0369A1', False),
                (s.month or '—',       TEXT_MAIN, False),
                (str(s.year or ''),    TEXT_SUB,  False),
                (f'{gross:.0f} MAD',   TEXT_MAIN, False),
                (f'{bonus:.0f} MAD',   SUCCESS,   False),
                (f'{ded:.0f} MAD',     DANGER,    False),
                (f'{net:.0f} MAD',     SUCCESS,   True),
            ]
            for col, (text, color, bold) in enumerate(data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.sal_table.setItem(row, col, item)
            self.sal_table.setRowHeight(row, 44)
            total_net += net

        # Chips
        for i in reversed(range(self.sal_chips.count())):
            w = self.sal_chips.itemAt(i).widget()
            if w: w.setParent(None)
        self.sal_chips.addWidget(
            self._chip(f'{len(salaries)} bulletins', PRIMARY, PRIMARY_LIGHT))
        self.sal_chips.addWidget(
            self._chip(f'Total net versé: {total_net:,.0f} MAD', SUCCESS, SUCCESS_LIGHT))
        self.sal_chips.addStretch()
        self.sal_total_lbl.setText(
            f'Total net versé: {total_net:,.0f} MAD  •  {len(salaries)} bulletins'
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _get_selected_employee(self):
        row = self.emp_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Veuillez sélectionner un employé.')
            return None
        search    = self.search_emp.text().lower()
        role_data = self.role_filter.currentData()
        filtered  = [
            e for e in self.all_employees
            if (not search
                or search in (e.first_name or '').lower()
                or search in (e.last_name or '').lower())
            and (not role_data or e.role == role_data)
        ]
        return filtered[row] if row < len(filtered) else None

    def _add_employee(self):
        dlg = EmployeeDialog(self)
        if dlg.exec():
            emp = Employee(**dlg.get_data())
            self.session.add(emp)
            self.session.commit()
            self._load_data()

    def _edit_employee(self):
        e = self._get_selected_employee()
        if not e: return
        dlg = EmployeeDialog(self, e)
        if dlg.exec():
            for k, v in dlg.get_data().items():
                setattr(e, k, v)
            self.session.commit()
            self._load_data()

    def _delete_employee(self):
        e = self._get_selected_employee()
        if not e: return
        if QMessageBox.question(
            self, 'Confirmation',
            f'Supprimer {e.first_name} {e.last_name} ?',
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            e.active = False
            self.session.commit()
            self._load_data()

    def _pay_salary(self):
        e = self._get_selected_employee()
        if not e: return
        dlg = SalaryDialog(self, e, self.session)
        dlg.exec()
        self._load_salary_history()
