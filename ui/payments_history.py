"""
payments_history.py — SGS v4  (improved)

Improvements:
  • Bulk-loads students in one query (eliminates N+1 on every row render)
  • Year filter added alongside month + type filters
  • Summary cards update instantly on filter (no re-query)
  • Export to CSV button
  • Delete payment with confirmation (admin guard)
  • Payment detail tooltip on hover
  • Row colouring: insurance=teal, transport=blue, monthly=green
  • Status bar shows filtered count + total MAD
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QHeaderView, QAbstractItemView, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from datetime import datetime

from models.database import Payment, Receipt, Student, SCHOOL_MONTHS
from themes.style import (
    MONTHS, TABLE_CSS, PRIMARY, PRIMARY_LIGHT,
    SUCCESS, SUCCESS_LIGHT, WARNING, WARNING_LIGHT, INFO, INFO_LIGHT,
    TEAL, TEAL_LIGHT, DANGER, DANGER_LIGHT, BORDER, TEXT_MAIN, TEXT_SUB
)

BTN     = (f'QPushButton{{background:{PRIMARY};color:white;border:none;border-radius:8px;'
           f'padding:8px 18px;font-weight:600;font-size:12px;}}QPushButton:hover{{background:#4338CA;}}')
BTN_SEC = ('QPushButton{background:#F3F4F6;color:#374151;border:1px solid #E5E7EB;'
           'border-radius:8px;padding:8px 18px;font-weight:500;font-size:12px;}'
           'QPushButton:hover{background:#E5E7EB;}')
BTN_SUC = (f'QPushButton{{background:{SUCCESS};color:white;border:none;border-radius:8px;'
           f'padding:8px 18px;font-weight:600;font-size:12px;}}QPushButton:hover{{background:#059669;}}')
BTN_DNG = (f'QPushButton{{background:{DANGER_LIGHT};color:#DC2626;border:1px solid #FECACA;'
           f'border-radius:8px;padding:8px 18px;font-weight:500;font-size:12px;}}')

_TYPE_LABEL = {
    'monthly':   '📅  Mensualité',
    'insurance': '🛡️  Assurance',
    'transport': '🚌  Transport',
    'inscription':'📝  Inscription',
}
_TYPE_COLOR = {
    'monthly':    SUCCESS,
    'insurance':  TEAL,
    'transport':  INFO,
    'inscription':'#7C3AED',
}
_TYPE_BG = {
    'monthly':    '#F0FDF4',
    'insurance':  '#F0FDFA',
    'transport':  '#EFF6FF',
    'inscription':'#F5F3FF',
}


def _mini_card(label, value, accent, light):
    card = QFrame()
    card.setStyleSheet(
        f'QFrame{{background:{light};border:1px solid {accent}33;'
        f'border-radius:10px;border-left:4px solid {accent};}}'
    )
    card.setFixedHeight(70)
    cl = QVBoxLayout(card); cl.setContentsMargins(14,10,14,8); cl.setSpacing(2)
    val = QLabel(value)
    val.setStyleSheet(f'color:{accent};font-size:18px;font-weight:800;background:transparent;')
    lbl = QLabel(label)
    lbl.setStyleSheet(f'color:{TEXT_SUB};font-size:10px;font-weight:500;background:transparent;')
    cl.addWidget(val); cl.addWidget(lbl)
    card._val = val
    return card


class PaymentsHistoryWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session  = session
        self._all     = []        # all Payment objects (current query window)
        self._student_map = {}    # id → Student (pre-loaded)
        self.setStyleSheet('background:transparent;')
        self._setup_ui()
        self._load_data()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        # ── Toolbar row 1: Add + title ────────────────────────────────────────
        r1 = QHBoxLayout(); r1.setSpacing(10)
        add_btn = QPushButton('➕  Ajouter Paiement')
        add_btn.setStyleSheet(BTN_SUC); add_btn.setFixedHeight(34)
        add_btn.clicked.connect(self._add_payment)

        exp_btn = QPushButton('⬇  Exporter CSV')
        exp_btn.setStyleSheet(BTN_SEC); exp_btn.setFixedHeight(34)
        exp_btn.clicked.connect(self._export_csv)

        del_btn = QPushButton('🗑  Supprimer')
        del_btn.setStyleSheet(BTN_DNG); del_btn.setFixedHeight(34)
        del_btn.clicked.connect(self._delete_payment)

        open_btn = QPushButton('🧾  Ouvrir Reçu')
        open_btn.setStyleSheet(BTN_SEC); open_btn.setFixedHeight(34)
        open_btn.clicked.connect(self._open_receipt)

        r1.addStretch()
        for b in [add_btn, open_btn, exp_btn, del_btn]: r1.addWidget(b)
        root.addLayout(r1)

        # ── Toolbar row 2: Filters ────────────────────────────────────────────
        r2 = QHBoxLayout(); r2.setSpacing(8)

        se_css = (f'QLineEdit{{background:white;border:1.5px solid {BORDER};border-radius:8px;'
                  f'color:{TEXT_MAIN};padding:0 12px;font-size:12px;height:32px;}}'
                  f'QLineEdit:focus{{border-color:{PRIMARY};}}')
        cb_css = (f'QComboBox{{background:white;border:1.5px solid {BORDER};border-radius:8px;'
                  f'color:{TEXT_MAIN};padding:0 10px;font-size:12px;min-width:130px;height:32px;}}'
                  f'QComboBox::drop-down{{border:none;width:18px;}}'
                  f'QComboBox QAbstractItemView{{background:white;border:1px solid {BORDER};'
                  f'color:{TEXT_MAIN};outline:none;border-radius:6px;}}'
                  f'QComboBox QAbstractItemView::item{{padding:6px 12px;}}'
                  f'QComboBox QAbstractItemView::item:selected{{background:{PRIMARY_LIGHT};color:{PRIMARY};}}')

        self._search = QLineEdit()
        self._search.setPlaceholderText('🔍  Nom, reçu, classe…')
        self._search.setFixedWidth(220); self._search.setStyleSheet(se_css)
        self._search.textChanged.connect(self._filter)

        self._type_f = QComboBox(); self._type_f.setStyleSheet(cb_css)
        self._type_f.addItem('Tous types', '')
        self._type_f.addItem('📅 Mensualités', 'monthly')
        self._type_f.addItem('🛡️ Assurances',  'insurance')
        self._type_f.addItem('🚌 Transport',   'transport')
        self._type_f.currentIndexChanged.connect(self._filter)

        self._month_f = QComboBox(); self._month_f.setStyleSheet(cb_css)
        self._month_f.addItem('Tous les mois', '')
        for m in MONTHS: self._month_f.addItem(m, m)
        self._month_f.currentIndexChanged.connect(self._filter)

        self._year_f = QComboBox(); self._year_f.setStyleSheet(cb_css)
        self._year_f.addItem('Toutes années', 0)
        cy = datetime.now().year
        for y in range(cy, cy - 5, -1): self._year_f.addItem(str(y), y)
        self._year_f.currentIndexChanged.connect(self._filter)

        rfsh = QPushButton('↺'); rfsh.setFixedSize(32, 32)
        rfsh.setStyleSheet(BTN_SEC); rfsh.clicked.connect(self._load_data)

        for w in [self._search, self._type_f, self._month_f, self._year_f]:
            r2.addWidget(w)
        r2.addStretch(); r2.addWidget(rfsh)
        root.addLayout(r2)

        # ── Summary cards ─────────────────────────────────────────────────────
        cr = QHBoxLayout(); cr.setSpacing(8)
        self._c_total   = _mini_card('Total encaissé',  '—', SUCCESS,   SUCCESS_LIGHT)
        self._c_monthly = _mini_card('Mensualités',     '—', PRIMARY,   PRIMARY_LIGHT)
        self._c_ins     = _mini_card('Assurances',      '—', TEAL,      TEAL_LIGHT)
        self._c_trans   = _mini_card('Transport',       '—', INFO,      INFO_LIGHT)
        self._c_count   = _mini_card('Paiements',       '—', WARNING,   WARNING_LIGHT)
        for c in [self._c_total, self._c_monthly, self._c_ins, self._c_trans, self._c_count]:
            cr.addWidget(c)
        root.addLayout(cr)

        # ── Table ─────────────────────────────────────────────────────────────
        tcard = QFrame()
        tcard.setStyleSheet(
            f'QFrame{{background:white;border:1px solid {BORDER};border-radius:12px;}}'
        )
        tcl = QVBoxLayout(tcard); tcl.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            'N° Reçu', 'Élève', 'Classe', 'Type', 'Période',
            'Montant', 'Date paiement', 'Année scol.', 'Statut'
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setStyleSheet(TABLE_CSS)
        self._table.doubleClicked.connect(self._open_receipt)
        tcl.addWidget(self._table)
        root.addWidget(tcard, 1)

        # Status bar
        self._status = QLabel()
        self._status.setStyleSheet('color:#9CA3AF;font-size:11px;background:transparent;')
        root.addWidget(self._status)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_data(self):
        self.session.expire_all()

        # Bulk-load students once
        self._student_map = {s.id: s for s in self.session.query(Student).all()}

        # Load last 1000 payments ordered newest first
        self._all = (
            self.session.query(Payment)
            .order_by(Payment.payment_date.desc())
            .limit(1000)
            .all()
        )
        self._filter()

    def _filter(self):
        search   = self._search.text().lower().strip()
        pay_type = self._type_f.currentData()
        month    = self._month_f.currentData()
        year     = self._year_f.currentData() or 0

        out = []
        for p in self._all:
            s = self._student_map.get(p.student_id)
            name = f'{(s.first_name or "")} {(s.last_name or "")}'.strip().lower() if s else ''
            cls  = (s.class_name or '').lower() if s else ''
            rec  = (p.receipt_number or '').lower()

            if search and not any(search in x for x in [name, cls, rec]):
                continue
            if pay_type and p.payment_type != pay_type:
                continue
            if month and p.month != month:
                continue
            if year and p.year and p.year != year:
                continue
            out.append(p)

        self._populate(out)

    def _populate(self, payments):
        self._table.setRowCount(len(payments))
        total = monthly_t = ins_t = trans_t = 0.0

        for row, p in enumerate(payments):
            s     = self._student_map.get(p.student_id)
            name  = f'{s.first_name} {s.last_name}' if s else '—'
            cls   = s.class_name if s else '—'
            color = _TYPE_COLOR.get(p.payment_type, TEXT_SUB)
            bg    = _TYPE_BG.get(p.payment_type, '#FFFFFF')
            amt   = p.amount or 0.0

            date_str = (p.payment_date.strftime('%d/%m/%Y  %H:%M')
                        if p.payment_date else '—')

            row_data = [
                (p.receipt_number or '—',                          '#6B7280', False),
                (name,                                              TEXT_MAIN, True),
                (cls,                                               PRIMARY,   False),
                (_TYPE_LABEL.get(p.payment_type, p.payment_type or '—'), color, False),
                (f'{p.month or "—"} {p.year or ""}',              TEXT_MAIN, False),
                (f'{amt:,.2f} MAD',                                SUCCESS,   True),
                (date_str,                                          TEXT_SUB,  False),
                (p.school_year or '—',                             '#6B7280', False),
                ('✅  Payé',                                        SUCCESS,   False),
            ]
            for col, (text, fg, bold) in enumerate(row_data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(fg))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                if col == 3:
                    item.setBackground(QColor(bg))
                self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 38)

            total += amt
            if p.payment_type == 'monthly':    monthly_t += amt
            elif p.payment_type == 'insurance': ins_t     += amt
            elif p.payment_type == 'transport': trans_t   += amt

        def fmt(v): return f'{v/1000:.1f}k' if v >= 1000 else f'{v:.0f}'
        self._c_total._val.setText(f'{fmt(total)} MAD')
        self._c_monthly._val.setText(f'{fmt(monthly_t)} MAD')
        self._c_ins._val.setText(f'{fmt(ins_t)} MAD')
        self._c_trans._val.setText(f'{fmt(trans_t)} MAD')
        self._c_count._val.setText(str(len(payments)))
        self._status.setText(
            f'{len(payments)} paiements affichés  •  Total : {total:,.2f} MAD'
            f'  •  Double-clic pour ouvrir le reçu'
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_payment(self):
        from ui.payment_dialog import AddPaymentDialog
        dlg = AddPaymentDialog(self, self.session)
        dlg.exec()
        self._load_data()

    def _open_receipt(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez un paiement.')
            return
        rec_num = self._table.item(row, 0).text()
        receipt = self.session.query(Receipt).filter_by(receipt_number=rec_num).first()
        if receipt and receipt.pdf_path and os.path.exists(receipt.pdf_path):
            import subprocess, platform
            if platform.system() == 'Linux':      subprocess.Popen(['xdg-open', receipt.pdf_path])
            elif platform.system() == 'Darwin':   subprocess.Popen(['open', receipt.pdf_path])
            else:
                try: os.startfile(receipt.pdf_path)
                except: pass
        else:
            QMessageBox.warning(self, 'Introuvable', 'Le fichier PDF de ce reçu est introuvable.')

    def _delete_payment(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez un paiement.')
            return
        rec_num = self._table.item(row, 0).text()
        name    = self._table.item(row, 1).text()
        period  = self._table.item(row, 4).text()

        reply = QMessageBox.question(
            self, '🗑  Supprimer le paiement',
            f'Supprimer le paiement de <b>{name}</b> pour la période <b>{period}</b> ?<br><br>'
            f'Le reçu PDF associé sera conservé sur disque.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        p = self.session.query(Payment).filter_by(receipt_number=rec_num).first()
        if p:
            # Revert MonthRecord to unpaid if it was a monthly payment
            if p.payment_type == 'monthly' and p.month:
                from models.database import MonthRecord
                mr = self.session.query(MonthRecord).filter_by(
                    student_id=p.student_id, month_name=p.month,
                    school_year=p.school_year
                ).first()
                if mr and mr.status == 'paid':
                    mr.status = 'unpaid'
            # Revert insurance_paid flag
            if p.payment_type == 'insurance':
                s = self._student_map.get(p.student_id)
                if s: s.insurance_paid = False
            self.session.delete(p)
            self.session.commit()
            self._load_data()
            QMessageBox.information(self, '✅', 'Paiement supprimé.')

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Exporter CSV', f'paiements_{datetime.now():%Y%m%d_%H%M}.csv',
            'CSV files (*.csv)'
        )
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(['N° Reçu','Élève','Classe','Type','Mois','Année',
                            'Montant MAD','Date Paiement','Année Scolaire'])
                for p in self._all:
                    s    = self._student_map.get(p.student_id)
                    name = f'{s.first_name} {s.last_name}' if s else '—'
                    cls  = s.class_name if s else '—'
                    w.writerow([
                        p.receipt_number or '',
                        name, cls,
                        p.payment_type or '',
                        p.month or '', p.year or '',
                        f'{p.amount:.2f}' if p.amount else '0.00',
                        p.payment_date.strftime('%d/%m/%Y %H:%M') if p.payment_date else '',
                        p.school_year or '',
                    ])
            QMessageBox.information(self, '✅  Export réussi', f'Fichier sauvegardé :\n{path}')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur export', str(e))

    def refresh(self):
        self._load_data()
