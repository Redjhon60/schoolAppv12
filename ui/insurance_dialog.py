"""
insurance_dialog.py — SGS v4  MODULE 2
Full insurance management:
  - InsurancePaymentDialog : pay insurance for one student (duplicate prevention)
  - InsuranceManagementWidget : list all students with insurance status,
      bulk-pay, history tab, summary KPIs
  - Insurance is ANNUAL — one payment per student per school year
  - Insurance revenue is EXCLUDED from monthly profit / revenue gap
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget, QMessageBox, QScrollArea, QTabWidget, QLineEdit, QComboBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from datetime import datetime

from models.database import Student, Payment, Receipt, Setting, SCHOOL_MONTHS
from services.receipt_service import generate_receipt_pdf
from themes.style import (
    DIALOG_CSS, TABLE_CSS, PRIMARY, PRIMARY_LIGHT, SUCCESS, SUCCESS_LIGHT,
    DANGER, DANGER_LIGHT, WARNING, WARNING_LIGHT, INFO, INFO_LIGHT,
    TEAL, TEAL_LIGHT, BORDER, BG_CARD, TEXT_MAIN, TEXT_SUB
)

# ── Shared styles ─────────────────────────────────────────────────────────────
BTN     = (f'QPushButton {{ background: {PRIMARY}; color: white; border: none; '
           f'border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px; }}'
           f'QPushButton:hover {{ background: #4338CA; }}')
BTN_SEC = ('QPushButton { background: #F3F4F6; color: #374151; border: 1px solid #E5E7EB; '
           'border-radius: 8px; padding: 9px 20px; font-weight: 500; font-size: 13px; }'
           'QPushButton:hover { background: #E5E7EB; }')
BTN_INS = (f'QPushButton {{ background: {TEAL}; color: white; border: none; '
           f'border-radius: 8px; padding: 9px 22px; font-weight: 700; font-size: 13px; }}'
           f'QPushButton:hover {{ background: #0F766E; }}')
BTN_DIS = ('QPushButton { background: #D1D5DB; color: #9CA3AF; border: none; '
           'border-radius: 8px; padding: 9px 22px; font-weight: 700; font-size: 13px; }')
FIELD_CSS = (f'QLineEdit, QComboBox {{ background: white; border: 1.5px solid {BORDER}; '
             f'border-radius: 10px; color: {TEXT_MAIN}; padding: 0 14px; '
             f'font-size: 13px; min-height: 40px; }}'
             f'QLineEdit:focus, QComboBox:focus {{ border-color: {TEAL}; }}'
             f'QComboBox QAbstractItemView {{ background: white; border: 1.5px solid {TEAL}; '
             f'border-radius: 10px; color: {TEXT_MAIN}; padding: 4px; outline: none; }}'
             f'QComboBox QAbstractItemView::item {{ padding: 8px 12px; border-radius: 6px; '
             f'margin: 1px 4px; }}'
             f'QComboBox QAbstractItemView::item:hover {{ background: {TEAL_LIGHT}; }}')
TAB_CSS = f"""
    QTabWidget::pane {{ border: none; background: transparent; }}
    QTabBar::tab {{ background: transparent; color: {TEXT_SUB}; border: none;
        border-bottom: 2px solid transparent; padding: 10px 24px;
        font-size: 13px; font-weight: 500; margin-right: 4px; }}
    QTabBar::tab:selected {{ color: {TEAL}; border-bottom: 2px solid {TEAL}; font-weight: 700; }}
    QTabBar::tab:hover:!selected {{ color: {TEXT_MAIN}; background: #F9FAFB;
        border-radius: 8px 8px 0 0; }}
"""


def _get_school_year(session) -> str:
    s = session.query(Setting).filter_by(key='school_year').first()
    return s.value if s else '2024-25'


def _insurance_payment_exists(session, student_id: int, school_year: str) -> bool:
    """Return True if insurance already paid for this student this school year."""
    return session.query(Payment).filter_by(
        student_id=student_id,
        payment_type='insurance',
        school_year=school_year,
    ).first() is not None


def _mini_kpi(label, value, accent, light):
    card = QFrame()
    card.setStyleSheet(
        f'QFrame {{ background: {light}; border: 1px solid {accent}33; '
        f'border-radius: 12px; border-left: 4px solid {accent}; }}'
    )
    card.setFixedHeight(80)
    cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 10); cl.setSpacing(3)
    val_lbl = QLabel(str(value))
    val_lbl.setStyleSheet(f'color: {accent}; font-size: 21px; font-weight: 800; background: transparent;')
    lbl = QLabel(label)
    lbl.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; font-weight: 500; background: transparent;')
    cl.addWidget(val_lbl); cl.addWidget(lbl)
    card._val = val_lbl
    return card


# ── Single-student Insurance Payment Dialog ───────────────────────────────────

class InsurancePaymentDialog(QDialog):
    """
    Pay insurance for one student.
    Rules:
      - ONE payment per student per school year
      - Creates Payment(payment_type='insurance')
      - Sets student.insurance_paid = True
      - Generates PDF receipt
    """
    payment_done = Signal()

    def __init__(self, parent, student: Student, session):
        super().__init__(parent)
        self.student = student
        self.session = session
        self.school_year = _get_school_year(session)

        self.setWindowTitle(f'Assurance — {student.first_name} {student.last_name}')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 560, 460)
        self.setStyleSheet(DIALOG_CSS + f'QDialog {{ background: #F7F8FC; }}{FIELD_CSS}')
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(f'QFrame {{ background: {TEAL}; }}')
        hdr.setFixedHeight(56)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24, 0, 24, 0)
        ht = QLabel(f'🛡️  Paiement Assurance — {self.student.first_name} {self.student.last_name}')
        ht.setStyleSheet('color: white; font-size: 14px; font-weight: 700; background: transparent;')
        hl.addWidget(ht); hl.addStretch()
        yr = QLabel(f'Année: {self.school_year}')
        yr.setStyleSheet('color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;')
        hl.addWidget(yr)
        outer.addWidget(hdr)

        content = QWidget(); content.setStyleSheet('background: transparent;')
        cl = QVBoxLayout(content); cl.setContentsMargins(28, 22, 28, 16); cl.setSpacing(16)

        already_paid = _insurance_payment_exists(self.session, self.student.id, self.school_year)

        if already_paid:
            # Show already-paid banner
            info = QFrame()
            info.setStyleSheet(
                f'QFrame {{ background: {SUCCESS_LIGHT}; border: 1.5px solid #A7F3D0; '
                f'border-radius: 12px; }}'
            )
            il = QHBoxLayout(info); il.setContentsMargins(20, 16, 20, 16)
            icon_lbl = QLabel('✅'); icon_lbl.setStyleSheet('font-size: 28px; background: transparent;')
            txt = QLabel(
                f'<b>{self.student.first_name} {self.student.last_name}</b>'
                f'<br>L\'assurance pour l\'année <b>{self.school_year}</b> a déjà été payée.'
            )
            txt.setStyleSheet(f'color: #065F46; font-size: 13px; background: transparent;')
            il.addWidget(icon_lbl); il.addSpacing(12); il.addWidget(txt); il.addStretch()
            cl.addWidget(info)
            cl.addStretch()
        else:
            # Student info card
            ins_amount = self.student.insurance_amount or 500.0
            card = QFrame()
            card.setStyleSheet(
                f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 12px; }}'
            )
            cardl = QVBoxLayout(card); cardl.setContentsMargins(20, 16, 20, 16); cardl.setSpacing(10)

            rows = [
                ('Élève',       f'{self.student.first_name} {self.student.last_name}', TEXT_MAIN),
                ('Classe',      self.student.class_name or '—',                        PRIMARY),
                ('Montant',     f'{ins_amount:.0f} MAD',                               TEAL),
                ('Type',        'Annuelle — une fois par année scolaire',              TEXT_SUB),
                ('Statut',      '❌ Non payée',                                         DANGER),
            ]
            for label, value, color in rows:
                row_w = QHBoxLayout(); row_w.setContentsMargins(0, 0, 0, 0)
                lbl = QLabel(label + ' :')
                lbl.setStyleSheet(f'color: {TEXT_SUB}; font-size: 12px; font-weight: 600; '
                                  f'min-width: 80px; background: transparent;')
                val = QLabel(value)
                val.setStyleSheet(f'color: {color}; font-size: 13px; font-weight: 700; background: transparent;')
                row_w.addWidget(lbl); row_w.addWidget(val); row_w.addStretch()
                cardl.addLayout(row_w)
            cl.addWidget(card)

            # Amount display
            amt_frame = QFrame()
            amt_frame.setStyleSheet(
                f'QFrame {{ background: {TEAL_LIGHT}; border: 1.5px solid {TEAL}33; '
                f'border-radius: 12px; border-left: 5px solid {TEAL}; }}'
            )
            afl = QVBoxLayout(amt_frame); afl.setContentsMargins(20, 14, 20, 14); afl.setSpacing(4)
            amt_lbl_title = QLabel('MONTANT ASSURANCE')
            amt_lbl_title.setStyleSheet(f'color: {TEXT_SUB}; font-size: 10px; font-weight: 700; '
                                        f'letter-spacing: 0.5px; background: transparent;')
            self.amt_display = QLabel(f'{ins_amount:.0f} MAD')
            self.amt_display.setStyleSheet(
                f'color: {TEAL}; font-size: 28px; font-weight: 800; background: transparent;'
            )
            note = QLabel('⚠️  Paiement annuel unique — ne sera plus demandé cette année scolaire')
            note.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; font-style: italic; background: transparent;')
            afl.addWidget(amt_lbl_title); afl.addWidget(self.amt_display); afl.addWidget(note)
            cl.addWidget(amt_frame)
            cl.addStretch()

        outer.addWidget(content, 1)

        # Footer
        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background: white; border-top: 1px solid {BORDER}; }}')
        footer.setFixedHeight(62)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24, 0, 24, 0); fl.setSpacing(10)
        cancel = QPushButton('Fermer'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)

        if already_paid:
            self.pay_btn = QPushButton('✅  Déjà payée')
            self.pay_btn.setStyleSheet(BTN_DIS)
            self.pay_btn.setEnabled(False)
        else:
            self.pay_btn = QPushButton('🛡️  Valider Paiement Assurance & Générer Reçu')
            self.pay_btn.setStyleSheet(BTN_INS)
            self.pay_btn.clicked.connect(self._process_payment)

        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(self.pay_btn)
        outer.addWidget(footer)

    def _process_payment(self):
        # Final duplicate guard
        if _insurance_payment_exists(self.session, self.student.id, self.school_year):
            QMessageBox.warning(
                self, 'Doublon',
                f'L\'assurance de {self.student.first_name} {self.student.last_name} '
                f'pour {self.school_year} est déjà enregistrée.'
            )
            return

        ins_amount = self.student.insurance_amount or 500.0

        reply = QMessageBox.question(
            self, 'Confirmer paiement assurance',
            f'Confirmer le paiement d\'assurance :\n\n'
            f'Élève  : {self.student.first_name} {self.student.last_name}\n'
            f'Année  : {self.school_year}\n'
            f'Montant: {ins_amount:.0f} MAD\n\n'
            f'⚠️  Ce paiement est annuel et ne peut pas être répété.',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # Create Payment record
            ins_payment = Payment(
                student_id   = self.student.id,
                payment_type = 'insurance',
                amount       = ins_amount,
                month        = 'Annuel',
                year         = datetime.now().year,
                school_year  = self.school_year,
                payment_date = datetime.now(),
            )
            self.session.add(ins_payment)
            self.session.flush()

            # Update student flag
            self.student.insurance_paid = True

            # Generate PDF receipt
            pdf_path, rec_num = None, None
            try:
                pdf_path, rec_num = generate_receipt_pdf(
                    self.session, self.student, ins_payment,
                    f'Assurance Scolaire — {self.school_year}'
                )
                ins_payment.receipt_number = rec_num
                from models.database import Receipt
                self.session.add(Receipt(
                    receipt_number = rec_num,
                    student_id     = self.student.id,
                    payment_id     = ins_payment.id,
                    amount         = ins_amount,
                    payment_type   = 'insurance',
                    pdf_path       = pdf_path,
                ))
            except Exception as e:
                print(f'Insurance receipt error: {e}')

            self.session.commit()
            self.payment_done.emit()

            # Success + open PDF offer
            msg = (f'✅ Assurance enregistrée !\n\n'
                   f'Élève   : {self.student.first_name} {self.student.last_name}\n'
                   f'Montant : {ins_amount:.0f} MAD\n'
                   f'Année   : {self.school_year}\n'
                   f'N° Reçu : {rec_num or "—"}')

            if pdf_path:
                r = QMessageBox.question(
                    self, 'Succès', msg + '\n\nOuvrir le reçu PDF ?',
                    QMessageBox.Yes | QMessageBox.No
                )
                if r == QMessageBox.Yes:
                    self._open_file(pdf_path)
            else:
                QMessageBox.information(self, 'Succès', msg)

            self.accept()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors du paiement :\n{str(e)}')

    def _open_file(self, path):
        import subprocess, platform
        if platform.system() == 'Linux':
            subprocess.Popen(['xdg-open', path])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', path])
        else:
            try: os.startfile(path)
            except Exception: pass


# ── Full Insurance Management Widget ─────────────────────────────────────────

class InsuranceManagementWidget(QWidget):
    """
    Full module:
      Tab 1 — Students list with insurance status + pay button per row
      Tab 2 — Insurance payment history
    """
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.all_students = []
        self.setStyleSheet('background: transparent;')
        self._setup_ui()
        self._load_data()

    def _get_school_year(self):
        return _get_school_year(self.session)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title row
        tr = QHBoxLayout()
        title = QLabel('🛡️  Gestion des Assurances')
        title.setStyleSheet(
            f'color: {TEXT_MAIN}; font-size: 16px; font-weight: 800; background: transparent;'
        )
        tr.addWidget(title); tr.addStretch()
        refresh_btn = QPushButton('🔄')
        refresh_btn.setFixedSize(38, 38); refresh_btn.setStyleSheet(BTN_SEC)
        refresh_btn.setToolTip('Rafraîchir'); refresh_btn.clicked.connect(self._load_data)
        tr.addWidget(refresh_btn)
        layout.addLayout(tr)

        # KPI row
        self.kpi_row = QHBoxLayout(); self.kpi_row.setSpacing(12)
        layout.addLayout(self.kpi_row)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_CSS)
        layout.addWidget(self.tabs, 1)

        # ── Tab 1: Students ───────────────────────────────────────────────────
        students_tab = QWidget(); students_tab.setStyleSheet('background: transparent;')
        stl = QVBoxLayout(students_tab); stl.setContentsMargins(0, 14, 0, 0); stl.setSpacing(12)

        # Toolbar
        tb = QHBoxLayout(); tb.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText('🔍  Rechercher élève...')
        self.search.setFixedWidth(280); self.search.setFixedHeight(40)
        self.search.setStyleSheet(
            f'QLineEdit {{ background: white; border: 1.5px solid {BORDER}; '
            f'border-radius: 10px; color: {TEXT_MAIN}; padding: 0 14px; font-size: 13px; }}'
            f'QLineEdit:focus {{ border-color: {TEAL}; }}'
        )
        self.search.textChanged.connect(self._filter)

        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(40)
        self.status_filter.setStyleSheet(FIELD_CSS)
        self.status_filter.addItem('Tous les statuts', '')
        self.status_filter.addItem('✅  Payée', 'paid')
        self.status_filter.addItem('❌  Non payée', 'unpaid')
        self.status_filter.currentIndexChanged.connect(self._filter)

        self.class_filter = QComboBox()
        self.class_filter.setFixedHeight(40)
        self.class_filter.setStyleSheet(FIELD_CSS)
        self.class_filter.addItem('Toutes les classes', '')
        self.class_filter.currentIndexChanged.connect(self._filter)

        pay_all_btn = QPushButton('🛡️  Payer sélectionné')
        pay_all_btn.setFixedHeight(40); pay_all_btn.setStyleSheet(BTN_INS)
        pay_all_btn.clicked.connect(self._pay_selected)

        tb.addWidget(self.search); tb.addWidget(self.status_filter)
        tb.addWidget(self.class_filter); tb.addStretch(); tb.addWidget(pay_all_btn)
        stl.addLayout(tb)

        # Students table
        tcard = QFrame()
        tcard.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 14px; }}'
        )
        tcl = QVBoxLayout(tcard); tcl.setContentsMargins(0, 0, 0, 0)
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(7)
        self.student_table.setHorizontalHeaderLabels(
            ['Nom', 'Prénom', 'Classe', 'Montant', 'Statut', 'Date paiement', 'Action']
        )
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.student_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.student_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.student_table.setAlternatingRowColors(True)
        self.student_table.verticalHeader().setVisible(False)
        self.student_table.setShowGrid(False)
        self.student_table.setStyleSheet(TABLE_CSS)
        self.student_table.doubleClicked.connect(self._pay_selected)
        tcl.addWidget(self.student_table)
        stl.addWidget(tcard, 1)

        self.student_status_lbl = QLabel()
        self.student_status_lbl.setStyleSheet('color: #9CA3AF; font-size: 12px; background: transparent;')
        stl.addWidget(self.student_status_lbl)

        # ── Tab 2: History ────────────────────────────────────────────────────
        history_tab = QWidget(); history_tab.setStyleSheet('background: transparent;')
        htl = QVBoxLayout(history_tab); htl.setContentsMargins(0, 14, 0, 0); htl.setSpacing(12)

        # History toolbar
        htb = QHBoxLayout()
        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText('🔍  Rechercher...')
        self.hist_search.setFixedHeight(40); self.hist_search.setFixedWidth(280)
        self.hist_search.setStyleSheet(
            f'QLineEdit {{ background: white; border: 1.5px solid {BORDER}; '
            f'border-radius: 10px; color: {TEXT_MAIN}; padding: 0 14px; font-size: 13px; }}'
            f'QLineEdit:focus {{ border-color: {TEAL}; }}'
        )
        self.hist_search.textChanged.connect(self._filter_history)
        open_rec_btn = QPushButton('🧾  Ouvrir Reçu')
        open_rec_btn.setFixedHeight(40); open_rec_btn.setStyleSheet(BTN_SEC)
        open_rec_btn.clicked.connect(self._open_receipt)
        htb.addWidget(self.hist_search); htb.addStretch(); htb.addWidget(open_rec_btn)
        htl.addLayout(htb)

        hcard = QFrame()
        hcard.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 14px; }}'
        )
        hcl = QVBoxLayout(hcard); hcl.setContentsMargins(0, 0, 0, 0)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels(
            ['N° Reçu', 'Élève', 'Classe', 'Montant', 'Année scolaire', 'Date', 'Statut']
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setShowGrid(False)
        self.history_table.setStyleSheet(TABLE_CSS)
        hcl.addWidget(self.history_table)
        htl.addWidget(hcard, 1)

        self.hist_status_lbl = QLabel()
        self.hist_status_lbl.setStyleSheet('color: #9CA3AF; font-size: 12px; background: transparent;')
        htl.addWidget(self.hist_status_lbl)

        self.tabs.addTab(students_tab, '👥  Élèves & Statut Assurance')
        self.tabs.addTab(history_tab, '📋  Historique des Paiements')

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_data(self):
        self.session.expire_all()
        school_year = self._get_school_year()

        # Load all active students
        self.all_students = (
            self.session.query(Student)
            .filter_by(active=True)
            .order_by(Student.class_name, Student.last_name, Student.first_name)
            .all()
        )

        # Update class filter
        classes = sorted(set(s.class_name for s in self.all_students if s.class_name))
        self.class_filter.blockSignals(True)
        self.class_filter.clear()
        self.class_filter.addItem('Toutes les classes', '')
        for c in classes:
            self.class_filter.addItem(c, c)
        self.class_filter.blockSignals(False)

        # Build insurance payment map: student_id → Payment
        ins_payments = {
            p.student_id: p
            for p in self.session.query(Payment).filter_by(
                payment_type='insurance', school_year=school_year
            ).all()
        }
        self._ins_payments = ins_payments

        # KPIs
        n_paid     = sum(1 for s in self.all_students if s.id in ins_payments)
        n_unpaid   = len(self.all_students) - n_paid
        collected  = sum(p.amount or 0 for p in ins_payments.values())
        self._update_kpis(n_paid, n_unpaid, collected, school_year)

        self._populate_student_table(self.all_students, ins_payments)
        self._load_history(ins_payments)

    def _update_kpis(self, n_paid, n_unpaid, collected, school_year):
        # Clear and rebuild KPI row
        for i in reversed(range(self.kpi_row.count())):
            w = self.kpi_row.itemAt(i).widget()
            if w: w.setParent(None)

        total = n_paid + n_unpaid
        pct = f'{100*n_paid//total:.0f}%' if total else '0%'

        kpis = [
            ('🛡️  Assurances encaissées',  f'{collected:,.0f} MAD', TEAL,    TEAL_LIGHT),
            ('✅  Élèves assurés',           n_paid,                  SUCCESS, SUCCESS_LIGHT),
            ('❌  Sans assurance',           n_unpaid,                DANGER,  DANGER_LIGHT),
            ('📊  Taux de couverture',       pct,                     PRIMARY, PRIMARY_LIGHT),
        ]
        for label, value, accent, light in kpis:
            self.kpi_row.addWidget(_mini_kpi(label, value, accent, light))

    def _populate_student_table(self, students, ins_payments):
        self.student_table.setRowCount(len(students))
        paid_count = 0
        for row, s in enumerate(students):
            p = ins_payments.get(s.id)
            is_paid = p is not None
            if is_paid:
                paid_count += 1

            status_text  = '✅  Payée'  if is_paid else '❌  Non payée'
            status_color = SUCCESS      if is_paid else DANGER
            pay_date     = p.payment_date.strftime('%d/%m/%Y') if (p and p.payment_date) else '—'
            action_text  = '✅  Déjà payée' if is_paid else '🛡️  Payer'
            action_color = '#9CA3AF'    if is_paid else TEAL

            row_data = [
                (s.last_name,                         TEXT_MAIN, True),
                (s.first_name,                        TEXT_MAIN, False),
                (s.class_name or '—',                 PRIMARY,   False),
                (f'{s.insurance_amount or 500:.0f} MAD', TEAL,   True),
                (status_text,                         status_color, False),
                (pay_date,                            TEXT_SUB,  False),
                (action_text,                         action_color, True),
            ]
            bg = SUCCESS_LIGHT if is_paid else None
            for col, (text, color, bold) in enumerate(row_data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                if bg:
                    item.setBackground(QColor(bg))
                self.student_table.setItem(row, col, item)
            self.student_table.setRowHeight(row, 42)

        self.student_status_lbl.setText(
            f'{paid_count} assurés  •  {len(students) - paid_count} non assurés  •  '
            f'{len(students)} total'
        )

    def _load_history(self, ins_payments):
        self.all_history_payments = list(ins_payments.values())
        self._populate_history_table(self.all_history_payments)

    def _populate_history_table(self, payments):
        from models.database import Receipt
        payments_sorted = sorted(payments, key=lambda p: p.payment_date or datetime.min, reverse=True)
        self.history_table.setRowCount(len(payments_sorted))
        total = 0.0
        for row, p in enumerate(payments_sorted):
            student = self.session.query(Student).filter_by(id=p.student_id).first()
            name    = f'{student.first_name} {student.last_name}' if student else '—'
            cls     = student.class_name if student else '—'
            rec_num = p.receipt_number or '—'
            row_data = [
                (rec_num,                                          '#6B7280', False),
                (name,                                             TEXT_MAIN, True),
                (cls,                                              PRIMARY,   False),
                (f'{p.amount:,.0f} MAD',                          TEAL,      True),
                (p.school_year or '—',                            TEXT_SUB,  False),
                (p.payment_date.strftime('%d/%m/%Y  %H:%M')
                 if p.payment_date else '—',                       TEXT_SUB,  False),
                ('✅  Enregistré',                                  SUCCESS,   False),
            ]
            for col, (text, color, bold) in enumerate(row_data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.history_table.setItem(row, col, item)
            self.history_table.setRowHeight(row, 42)
            total += p.amount or 0
        self.hist_status_lbl.setText(
            f'{len(payments_sorted)} paiements d\'assurance  •  '
            f'Total: {total:,.0f} MAD'
        )

    # ── Filters ───────────────────────────────────────────────────────────────
    def _filter(self):
        school_year = self._get_school_year()
        text        = self.search.text().lower()
        stat        = self.status_filter.currentData()
        cls         = self.class_filter.currentData()

        filtered = []
        for s in self.all_students:
            is_paid = s.id in self._ins_payments
            if text and text not in (s.first_name or '').lower() \
                    and text not in (s.last_name or '').lower() \
                    and text not in (s.class_name or '').lower():
                continue
            if stat == 'paid' and not is_paid:
                continue
            if stat == 'unpaid' and is_paid:
                continue
            if cls and s.class_name != cls:
                continue
            filtered.append(s)
        self._populate_student_table(filtered, self._ins_payments)

    def _filter_history(self):
        text = self.hist_search.text().lower()
        filtered = []
        for p in self.all_history_payments:
            student = self.session.query(Student).filter_by(id=p.student_id).first()
            name = (f'{(student.first_name or "")} {(student.last_name or "")}').lower() if student else ''
            rec  = (p.receipt_number or '').lower()
            if text and text not in name and text not in rec:
                continue
            filtered.append(p)
        self._populate_history_table(filtered)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _pay_selected(self):
        row = self.student_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez un élève.')
            return

        # Resolve student from filtered list
        text   = self.search.text().lower()
        stat   = self.status_filter.currentData()
        cls    = self.class_filter.currentData()
        filtered = [
            s for s in self.all_students
            if (not text or text in (s.first_name or '').lower()
                or text in (s.last_name or '').lower()
                or text in (s.class_name or '').lower())
            and (not stat or (stat == 'paid') == (s.id in self._ins_payments))
            and (not cls or s.class_name == cls)
        ]
        if row >= len(filtered):
            return
        student = filtered[row]

        dlg = InsurancePaymentDialog(self, student, self.session)
        dlg.payment_done.connect(self._load_data)
        dlg.exec()

    def _open_receipt(self):
        row = self.history_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez un paiement.')
            return
        rec_num = self.history_table.item(row, 0).text()
        from models.database import Receipt
        receipt = self.session.query(Receipt).filter_by(receipt_number=rec_num).first()
        if receipt and receipt.pdf_path and os.path.exists(receipt.pdf_path):
            import subprocess, platform
            if platform.system() == 'Linux':
                subprocess.Popen(['xdg-open', receipt.pdf_path])
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', receipt.pdf_path])
            else:
                try: os.startfile(receipt.pdf_path)
                except Exception: pass
        else:
            QMessageBox.warning(self, 'Introuvable', 'Le PDF de ce reçu est introuvable.')

    def refresh(self):
        self._load_data()
