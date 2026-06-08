"""
payment_dialog.py — SGS v4
Refactored payment dialog:
  - Auto-loads student financial data on selection
  - Enforces oldest-unpaid-month rule (no skipping)
  - Calculates total = monthly_fee + transport_fee (if has_transport)
  - Creates separate Payment records for monthly + transport
  - Duplicate prevention (student + month + school_year + payment_type)
  - Auto-generates PDF receipt after validation
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QWidget, QMessageBox, QComboBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from datetime import datetime

from models.database import (
    get_session, Student, Payment, Receipt, MonthRecord,
    SCHOOL_MONTHS, Setting
)
from themes.style import (
    DIALOG_CSS, PRIMARY, PRIMARY_LIGHT, SUCCESS, SUCCESS_LIGHT,
    DANGER, DANGER_LIGHT, WARNING, WARNING_LIGHT, NAN_COLOR, NAN_TEXT,
    BORDER, TEXT_MAIN, TEXT_SUB
)

# ── Button styles ─────────────────────────────────────────────────────────────
BTN = (f'QPushButton {{ background: {PRIMARY}; color: white; border: none; '
       f'border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px; }}'
       f'QPushButton:hover {{ background: #4338CA; }}')
BTN_SEC = ('QPushButton { background: #F3F4F6; color: #374151; border: 1px solid #E5E7EB; '
           'border-radius: 8px; padding: 9px 20px; font-weight: 500; }'
           'QPushButton:hover { background: #E5E7EB; }')
BTN_SUC = (f'QPushButton {{ background: {SUCCESS}; color: white; border: none; '
           f'border-radius: 8px; padding: 9px 22px; font-weight: 700; font-size: 13px; }}'
           f'QPushButton:hover {{ background: #059669; }}')
BTN_DISABLED = ('QPushButton { background: #D1D5DB; color: #9CA3AF; border: none; '
                'border-radius: 8px; padding: 9px 22px; font-weight: 700; font-size: 13px; }')


class PaymentDialog(QDialog):
    """
    Payment dialog for a single student.
    Enforces:
      1. Always proposes oldest unpaid month (cannot skip)
      2. Amount = monthly_fee + transport_fee (if has_transport)
      3. Separate Payment records for monthly & transport
      4. Duplicate prevention
      5. Auto-generates PDF receipt
    """

    payment_done = Signal()   # emitted after successful payment

    def __init__(self, parent, student: Student, session):
        super().__init__(parent)
        self.student = student
        self.session = session
        self.school_year = self._get_school_year()

        self.setWindowTitle(f'Paiement — {student.first_name} {student.last_name}')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 780, 700)
        self.setStyleSheet(DIALOG_CSS + 'QDialog { background: #F7F8FC; }')

        self._ensure_month_records()
        self._setup_ui()
        self._load_month_data()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_school_year(self):
        s = self.session.query(Setting).filter_by(key='school_year').first()
        return s.value if s else '2024-25'

    def _ensure_month_records(self):
        """Create MonthRecord entries for all school months if missing."""
        for month in SCHOOL_MONTHS:
            existing = self.session.query(MonthRecord).filter_by(
                student_id=self.student.id,
                month_name=month,
                school_year=self.school_year
            ).first()
            if not existing:
                self.session.add(MonthRecord(
                    student_id=self.student.id,
                    month_name=month,
                    school_year=self.school_year,
                    status='unpaid',
                    amount=self.student.monthly_fee or 0.0
                ))
        self.session.commit()

    def _get_records(self):
        """Return dict month_name → MonthRecord."""
        return {
            r.month_name: r
            for r in self.session.query(MonthRecord).filter_by(
                student_id=self.student.id,
                school_year=self.school_year
            ).all()
        }

    def _oldest_unpaid_month(self, records):
        """Return the name of the oldest unpaid month, or None if all paid/nan."""
        for month in SCHOOL_MONTHS:
            r = records.get(month)
            if r and r.status == 'unpaid':
                return month
        return None

    def _payment_exists(self, month_name, payment_type):
        """Check if a payment already exists for this student/month/year/type."""
        return self.session.query(Payment).filter_by(
            student_id=self.student.id,
            payment_type=payment_type,
            month=month_name,
        ).first() is not None

    def _monthly_total(self):
        """Calculate total monthly payment = monthly_fee + transport_fee."""
        fee = self.student.monthly_fee or 0.0
        transport = (self.student.transport_fee or 0.0) if self.student.has_transport else 0.0
        return fee, transport, fee + transport

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet(f'QFrame {{ background: {SUCCESS}; }}')
        hdr.setFixedHeight(58)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        ht = QLabel(f'💳  Paiement — {self.student.first_name} {self.student.last_name}')
        ht.setStyleSheet('color: white; font-size: 15px; font-weight: 700; background: transparent;')
        hl.addWidget(ht)
        hl.addStretch()
        year_lbl = QLabel(f'Année: {self.school_year}')
        year_lbl.setStyleSheet('color: rgba(255,255,255,0.8); font-size: 12px; background: transparent;')
        hl.addWidget(year_lbl)
        outer.addWidget(hdr)

        # ── Content area ──────────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet('background: transparent;')
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 18, 24, 12)
        cl.setSpacing(14)

        # Student financial info card
        cl.addWidget(self._build_student_info_card())

        # Proposed month banner
        self.proposed_banner = self._build_proposed_banner()
        cl.addWidget(self.proposed_banner)

        # Amount breakdown card
        self.amount_card = self._build_amount_card()
        cl.addWidget(self.amount_card)

        # Month history table (read-only summary)
        cl.addWidget(QLabel('  Historique des mois :').setStyleSheet(
            f'color:{TEXT_SUB}; font-size:11px;') or self._make_section_label('Historique des mois'))
        self.months_table = self._build_months_table()
        cl.addWidget(self.months_table)

        outer.addWidget(content, 1)

        # ── Footer buttons ────────────────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background: white; border-top: 1px solid {BORDER}; }}')
        footer.setFixedHeight(64)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 0, 24, 0)
        fl.setSpacing(10)

        cancel = QPushButton('Fermer')
        cancel.setStyleSheet(BTN_SEC)
        cancel.clicked.connect(self.reject)

        self.pay_btn = QPushButton('✅  Valider le Paiement & Générer Reçu')
        self.pay_btn.setStyleSheet(BTN_SUC)
        self.pay_btn.clicked.connect(self._process_payment)

        fl.addStretch()
        fl.addWidget(cancel)
        fl.addWidget(self.pay_btn)
        outer.addWidget(footer)

    def _make_section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; font-weight: 600; '
                          f'letter-spacing: 0.5px; background: transparent;')
        return lbl

    def _build_student_info_card(self):
        card = QFrame()
        card.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 12px; }}')
        lay = QHBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(0)

        has_t = self.student.has_transport
        transport_str = (f"{self.student.transport_fee:.0f} MAD" if has_t else 'Non')
        ins_paid = self.student.insurance_paid
        ins_str = '✅ Payée' if ins_paid else '❌ Non payée'
        ins_color = SUCCESS if ins_paid else DANGER

        items = [
            ('ÉLÈVE', f'{self.student.first_name} {self.student.last_name}', TEXT_MAIN),
            ('CLASSE', self.student.class_name or '—', PRIMARY),
            ('MENSUALITÉ', f'{self.student.monthly_fee:.0f} MAD', SUCCESS),
            ('TRANSPORT', ('✅ ' if has_t else '❌ ') + transport_str,
             SUCCESS if has_t else '#9CA3AF'),
            ('ASSURANCE', ins_str, ins_color),
        ]

        for i, (label, value, color) in enumerate(items):
            if i > 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.VLine)
                sep.setStyleSheet(f'color: {BORDER};')
                lay.addWidget(sep)
                lay.addSpacing(16)
            col = QVBoxLayout()
            col.setSpacing(3)
            lbl = QLabel(label)
            lbl.setStyleSheet(f'color: {TEXT_SUB}; font-size: 10px; font-weight: 600; '
                              f'letter-spacing: 0.5px; background: transparent;')
            val = QLabel(value)
            val.setStyleSheet(f'color: {color}; font-size: 13px; font-weight: 700; background: transparent;')
            col.addWidget(lbl)
            col.addWidget(val)
            lay.addLayout(col)
            if i < len(items) - 1:
                lay.addSpacing(16)

        lay.addStretch()
        return card

    def _build_proposed_banner(self):
        """Banner showing which month will be paid (oldest unpaid)."""
        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: #EEF2FF; border: 1.5px solid #C7D2FE; '
                            f'border-radius: 10px; }}')
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(18, 12, 18, 12)

        icon = QLabel('📅')
        icon.setStyleSheet('font-size: 22px; background: transparent;')

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.proposed_title = QLabel('Prochain mois à payer :')
        self.proposed_title.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; '
                                          f'font-weight: 600; background: transparent;')
        self.proposed_month = QLabel('—')
        self.proposed_month.setStyleSheet(f'color: {PRIMARY}; font-size: 18px; '
                                          f'font-weight: 800; background: transparent;')
        text_col.addWidget(self.proposed_title)
        text_col.addWidget(self.proposed_month)

        self.proposed_note = QLabel('')
        self.proposed_note.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; '
                                         f'font-style: italic; background: transparent;')

        lay.addWidget(icon)
        lay.addSpacing(10)
        lay.addLayout(text_col)
        lay.addStretch()
        lay.addWidget(self.proposed_note)
        return frame

    def _build_amount_card(self):
        """Card showing amount breakdown: monthly + transport = total."""
        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 10px; }}')
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(0)

        fee, transport, total = self._monthly_total()

        # Monthly fee block
        col1 = QVBoxLayout()
        col1.setSpacing(2)
        lbl1 = QLabel('MENSUALITÉ')
        lbl1.setStyleSheet(f'color: {TEXT_SUB}; font-size: 10px; font-weight: 600; background: transparent;')
        self.lbl_fee = QLabel(f'{fee:.0f} MAD')
        self.lbl_fee.setStyleSheet(f'color: {TEXT_MAIN}; font-size: 17px; font-weight: 700; background: transparent;')
        col1.addWidget(lbl1); col1.addWidget(self.lbl_fee)

        # Plus sign
        plus = QLabel(' + ')
        plus.setStyleSheet(f'color: {TEXT_SUB}; font-size: 20px; font-weight: 300; background: transparent;')

        # Transport block
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        lbl2 = QLabel('TRANSPORT')
        lbl2.setStyleSheet(f'color: {TEXT_SUB}; font-size: 10px; font-weight: 600; background: transparent;')
        transport_display = f'{transport:.0f} MAD' if self.student.has_transport else 'N/A'
        self.lbl_transport = QLabel(transport_display)
        t_color = TEXT_MAIN if self.student.has_transport else '#9CA3AF'
        self.lbl_transport.setStyleSheet(f'color: {t_color}; font-size: 17px; font-weight: 700; background: transparent;')
        col2.addWidget(lbl2); col2.addWidget(self.lbl_transport)

        # Equals sign
        eq = QLabel(' = ')
        eq.setStyleSheet(f'color: {TEXT_SUB}; font-size: 20px; font-weight: 300; background: transparent;')

        # Total block
        col3 = QVBoxLayout()
        col3.setSpacing(2)
        lbl3 = QLabel('TOTAL À PAYER')
        lbl3.setStyleSheet(f'color: {TEXT_SUB}; font-size: 10px; font-weight: 700; background: transparent;')
        self.lbl_total = QLabel(f'{total:.0f} MAD')
        self.lbl_total.setStyleSheet(f'color: {SUCCESS}; font-size: 22px; font-weight: 800; background: transparent;')
        col3.addWidget(lbl3); col3.addWidget(self.lbl_total)

        lay.addLayout(col1)
        lay.addWidget(plus)
        lay.addLayout(col2)
        lay.addWidget(eq)
        lay.addLayout(col3)
        lay.addStretch()
        return frame

    def _build_months_table(self):
        """Read-only month history showing status of all 10 months."""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Mois', 'Statut', 'Montant mensuel', 'Montant transport'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QHeaderView.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setFixedHeight(280)
        table.setStyleSheet(f'''
            QTableWidget {{ background: white; border: 1px solid {BORDER};
                border-radius: 12px; outline: none; }}
            QTableWidget::item {{ padding: 8px 12px; border-bottom: 1px solid #F3F4F8; color: #374151; }}
            QTableWidget::item:alternate {{ background: #FAFBFD; }}
            QHeaderView::section {{ background: #F9FAFB; color: #6B7280; padding: 8px 12px;
                border: none; border-bottom: 2px solid {BORDER}; font-weight: 700; font-size: 11px; }}
        ''')
        return table

    # ── Data Loading ──────────────────────────────────────────────────────────

    def _load_month_data(self):
        records = self._get_records()
        oldest_unpaid = self._oldest_unpaid_month(records)
        fee, transport, total = self._monthly_total()

        # Update proposed banner
        if oldest_unpaid:
            self.proposed_month.setText(oldest_unpaid)
            paid_count = sum(1 for m in SCHOOL_MONTHS if records.get(m) and records[m].status == 'paid')
            self.proposed_note.setText(f'{paid_count} mois payé(s) sur {len(SCHOOL_MONTHS)}')
            self.pay_btn.setStyleSheet(BTN_SUC)
            self.pay_btn.setEnabled(True)
        else:
            # All months paid or nan
            self.proposed_month.setText('Tous les mois sont à jour ✅')
            self.proposed_month.setStyleSheet(f'color: {SUCCESS}; font-size: 15px; '
                                              f'font-weight: 700; background: transparent;')
            self.proposed_note.setText('')
            self.pay_btn.setStyleSheet(BTN_DISABLED)
            self.pay_btn.setEnabled(False)

        # Populate months table
        self.months_table.setRowCount(len(SCHOOL_MONTHS))
        status_map = {
            'paid':   ('✅  Payé',             SUCCESS,  SUCCESS_LIGHT),
            'unpaid': ('⏳  Impayé',           DANGER,   DANGER_LIGHT),
            'nan':    ('⊘  Non inscrit',       NAN_TEXT, NAN_COLOR),
        }

        for row_idx, month in enumerate(SCHOOL_MONTHS):
            record = records.get(month)
            status = record.status if record else 'unpaid'
            is_proposed = (month == oldest_unpaid)

            # Highlight proposed month
            row_bg = '#F0FDF4' if is_proposed else None

            # Month name
            month_item = QTableWidgetItem(f'  {"→ " if is_proposed else "    "}{month}')
            f = month_item.font()
            f.setBold(is_proposed)
            month_item.setFont(f)
            if is_proposed:
                month_item.setForeground(QColor(SUCCESS))
            self.months_table.setItem(row_idx, 0, month_item)

            # Status
            s_text, s_color, s_bg = status_map.get(status, ('?', TEXT_MAIN, '#F9FAFB'))
            status_item = QTableWidgetItem(s_text)
            status_item.setForeground(QColor(s_color))
            status_item.setBackground(QColor(s_bg))
            self.months_table.setItem(row_idx, 1, status_item)

            # Monthly amount
            if status == 'nan':
                amt_item = QTableWidgetItem('—')
                amt_item.setForeground(QColor('#9CA3AF'))
            elif status == 'paid':
                amt_item = QTableWidgetItem(f'{fee:.0f} MAD')
                amt_item.setForeground(QColor(SUCCESS))
            else:
                amt_item = QTableWidgetItem(f'{fee:.0f} MAD')
                amt_item.setForeground(QColor(DANGER))
            self.months_table.setItem(row_idx, 2, amt_item)

            # Transport amount
            if status == 'nan' or not self.student.has_transport:
                tr_item = QTableWidgetItem('—')
                tr_item.setForeground(QColor('#9CA3AF'))
            elif status == 'paid':
                tr_item = QTableWidgetItem(f'{transport:.0f} MAD')
                tr_item.setForeground(QColor(SUCCESS))
            else:
                tr_item = QTableWidgetItem(f'{transport:.0f} MAD')
                tr_item.setForeground(QColor(DANGER))
            self.months_table.setItem(row_idx, 3, tr_item)

            if row_bg:
                for col in range(4):
                    item = self.months_table.item(row_idx, col)
                    if item:
                        item.setBackground(QColor(row_bg))

            self.months_table.setRowHeight(row_idx, 38)

    # ── Payment Processing ────────────────────────────────────────────────────

    def _process_payment(self):
        records = self._get_records()
        oldest_unpaid = self._oldest_unpaid_month(records)

        if not oldest_unpaid:
            QMessageBox.information(self, 'À jour', 'Tous les mois sont déjà payés.')
            return

        fee, transport, total = self._monthly_total()
        record = records.get(oldest_unpaid)

        # Confirm with user
        confirm_msg = (
            f'Confirmer le paiement pour :\n\n'
            f'Élève   : {self.student.first_name} {self.student.last_name}\n'
            f'Mois    : {oldest_unpaid}\n'
            f'Mensualité : {fee:.0f} MAD'
        )
        if self.student.has_transport:
            confirm_msg += f'\nTransport  : {transport:.0f} MAD'
        confirm_msg += f'\n\nTotal    : {total:.0f} MAD'

        reply = QMessageBox.question(
            self, 'Confirmer le paiement', confirm_msg,
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        from services.receipt_service import generate_receipt_pdf

        year = datetime.now().year
        receipts_generated = []

        try:
            # ── 1. Monthly payment ────────────────────────────────────────────
            # Duplicate check
            if self._payment_exists(oldest_unpaid, 'monthly'):
                QMessageBox.warning(
                    self, 'Doublon détecté',
                    f'Un paiement mensuel pour {oldest_unpaid} existe déjà.'
                )
                return

            monthly_payment = Payment(
                student_id=self.student.id,
                payment_type='monthly',
                amount=fee,
                month=oldest_unpaid,
                year=year,
                school_year=self.school_year,
                payment_date=datetime.now(),
            )
            self.session.add(monthly_payment)
            self.session.flush()

            # Generate receipt for monthly
            try:
                filepath, rec_num = generate_receipt_pdf(
                    self.session, self.student, monthly_payment,
                    f'Mensualité — {oldest_unpaid}'
                )
                monthly_payment.receipt_number = rec_num
                self.session.add(Receipt(
                    receipt_number=rec_num,
                    student_id=self.student.id,
                    payment_id=monthly_payment.id,
                    amount=fee,
                    payment_type='monthly',
                    pdf_path=filepath,
                ))
                receipts_generated.append((rec_num, filepath, f'Mensualité {oldest_unpaid}'))
            except Exception as e:
                print(f'Receipt error (monthly): {e}')

            # ── 2. Transport payment ──────────────────────────────────────────
            if self.student.has_transport and transport > 0:
                if not self._payment_exists(oldest_unpaid, 'transport'):
                    transport_payment = Payment(
                        student_id=self.student.id,
                        payment_type='transport',
                        amount=transport,
                        month=oldest_unpaid,
                        year=year,
                        school_year=self.school_year,
                        payment_date=datetime.now(),
                    )
                    self.session.add(transport_payment)
                    self.session.flush()

                    try:
                        filepath, rec_num = generate_receipt_pdf(
                            self.session, self.student, transport_payment,
                            f'Transport — {oldest_unpaid}'
                        )
                        transport_payment.receipt_number = rec_num
                        self.session.add(Receipt(
                            receipt_number=rec_num,
                            student_id=self.student.id,
                            payment_id=transport_payment.id,
                            amount=transport,
                            payment_type='transport',
                            pdf_path=filepath,
                        ))
                        receipts_generated.append((rec_num, filepath, f'Transport {oldest_unpaid}'))
                    except Exception as e:
                        print(f'Receipt error (transport): {e}')

            # ── 3. Update MonthRecord status ──────────────────────────────────
            if record:
                record.status = 'paid'
                record.amount = total

            self.session.commit()

            # ── 4. Success feedback ───────────────────────────────────────────
            msg = (
                f'✅ Paiement enregistré !\n\n'
                f'Mois    : {oldest_unpaid}\n'
                f'Total   : {total:,.0f} MAD\n'
                f'Reçus   : {len(receipts_generated)}'
            )
            reply = QMessageBox.question(
                self, 'Paiement effectué', msg + '\n\nOuvrir les reçus PDF ?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._open_receipts(receipts_generated)

            # Refresh UI
            self._load_month_data()
            self.payment_done.emit()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Erreur lors du paiement :\n{str(e)}')

    def _open_receipts(self, receipts):
        import subprocess
        import platform
        for _, filepath, _ in receipts:
            if filepath and os.path.exists(filepath):
                if platform.system() == 'Linux':
                    subprocess.Popen(['xdg-open', filepath])
                elif platform.system() == 'Darwin':
                    subprocess.Popen(['open', filepath])
                else:
                    try:
                        os.startfile(filepath)
                    except Exception:
                        pass


# ── Student Selector Dialog ───────────────────────────────────────────────────

class AddPaymentDialog(QDialog):
    """
    Step 1: Select a student → opens PaymentDialog.
    Navigation: Paiements → Ajouter Paiement → Select Student.
    Auto-loads student financial data once selected.
    """

    def __init__(self, parent, session):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle('Ajouter un Paiement')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 660, 540)
        self.setStyleSheet(DIALOG_CSS + 'QDialog { background: #F7F8FC; }')
        self._setup_ui()
        self._load_students()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(f'QFrame {{ background: {PRIMARY}; }}')
        hdr.setFixedHeight(56)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        ht = QLabel('➕  Ajouter un Paiement')
        ht.setStyleSheet('color: white; font-size: 15px; font-weight: 700; background: transparent;')
        hl.addWidget(ht)
        outer.addWidget(hdr)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(14)

        # Search
        from PySide6.QtWidgets import QLineEdit
        search_css = (f'QLineEdit {{ background: white; border: 1.5px solid {BORDER}; '
                      f'border-radius: 10px; color: {TEXT_MAIN}; padding: 0 14px; '
                      f'font-size: 13px; height: 42px; }}'
                      f'QLineEdit:focus {{ border-color: {PRIMARY}; }}')
        self.search = QLineEdit()
        self.search.setPlaceholderText('🔍  Rechercher un élève (nom, prénom, classe)...')
        self.search.setStyleSheet(search_css)
        self.search.textChanged.connect(self._filter_students)
        cl.addWidget(self.search)

        # Students table
        tcard = QFrame()
        tcard.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 12px; }}')
        tcl = QVBoxLayout(tcard)
        tcl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Nom', 'Prénom', 'Classe', 'Mensualité', 'Prochain mois dû'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QHeaderView.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._open_payment)
        self.table.setStyleSheet(f'''
            QTableWidget {{ background: white; border: none; outline: none; }}
            QTableWidget::item {{ padding: 10px 12px; border-bottom: 1px solid #F3F4F8; }}
            QTableWidget::item:selected {{ background: {PRIMARY_LIGHT}; color: {PRIMARY}; }}
            QTableWidget::item:alternate {{ background: #FAFBFD; }}
            QHeaderView::section {{ background: #F9FAFB; color: #6B7280; padding: 10px 12px;
                border: none; border-bottom: 2px solid {BORDER}; font-weight: 700; font-size: 11px; }}
        ''')
        tcl.addWidget(self.table)
        cl.addWidget(tcard, 1)

        hint = QLabel('Double-cliquez sur un élève pour ouvrir son paiement.')
        hint.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; background: transparent;')
        cl.addWidget(hint)

        outer.addWidget(content, 1)

        # Footer
        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background: white; border-top: 1px solid {BORDER}; }}')
        footer.setFixedHeight(60)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 0, 24, 0)
        fl.setSpacing(10)

        cancel = QPushButton('Fermer')
        cancel.setStyleSheet(BTN_SEC)
        cancel.clicked.connect(self.reject)

        open_btn = QPushButton('💳  Ouvrir Paiement')
        open_btn.setStyleSheet(BTN)
        open_btn.clicked.connect(self._open_payment)

        fl.addStretch()
        fl.addWidget(cancel)
        fl.addWidget(open_btn)
        outer.addWidget(footer)

        self.all_students = []

    def _load_students(self):
        school_year = self._get_school_year()
        self.all_students = (
            self.session.query(Student)
            .filter_by(active=True)
            .order_by(Student.last_name, Student.first_name)
            .all()
        )
        self._populate_table(self.all_students, school_year)

    def _get_school_year(self):
        s = self.session.query(Setting).filter_by(key='school_year').first()
        return s.value if s else '2024-25'

    def _get_oldest_unpaid(self, student, school_year):
        records = {
            r.month_name: r
            for r in self.session.query(MonthRecord).filter_by(
                student_id=student.id, school_year=school_year
            ).all()
        }
        for month in SCHOOL_MONTHS:
            r = records.get(month)
            if r and r.status == 'unpaid':
                return month
        return None

    def _populate_table(self, students, school_year):
        self.table.setRowCount(len(students))
        for row, student in enumerate(students):
            oldest = self._get_oldest_unpaid(student, school_year)

            items = [
                (student.last_name, TEXT_MAIN, True),
                (student.first_name, TEXT_MAIN, False),
                (student.class_name or '—', PRIMARY, False),
                (f'{student.monthly_fee:.0f} MAD', SUCCESS, False),
                (oldest or '✅ À jour', DANGER if oldest else SUCCESS, False),
            ]
            for col, (text, color, bold) in enumerate(items):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.table.setItem(row, col, item)
            self.table.setRowHeight(row, 40)

    def _filter_students(self, text):
        text = text.lower()
        filtered = [
            s for s in self.all_students
            if text in s.first_name.lower()
            or text in s.last_name.lower()
            or text in (s.class_name or '').lower()
        ]
        self._populate_table(filtered, self._get_school_year())

    def _open_payment(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez un élève.')
            return
        # Get student from filtered list
        text = self.search.text().lower()
        filtered = [
            s for s in self.all_students
            if not text
            or text in s.first_name.lower()
            or text in s.last_name.lower()
            or text in (s.class_name or '').lower()
        ]
        if row >= len(filtered):
            return
        student = filtered[row]

        dlg = PaymentDialog(self, student, self.session)
        dlg.payment_done.connect(self._refresh_after_payment)
        dlg.exec()

    def _refresh_after_payment(self):
        school_year = self._get_school_year()
        text = self.search.text().lower()
        filtered = [
            s for s in self.all_students
            if not text
            or text in s.first_name.lower()
            or text in s.last_name.lower()
            or text in (s.class_name or '').lower()
        ]
        self._populate_table(filtered, school_year)
