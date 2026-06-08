"""
expenses.py — SGS v4  MODULE 5
Full Expense Management:
  - ExpenseCategory: configured once (Loyer, Eau, Électricité, etc.)
  - ExpensePayment:  one per category × month × year
  - Metrics: Expected / Paid / Remaining
  - Duplicate prevention: one ExpensePayment per category per month
  - Profit formula uses ExpensePayment, NOT legacy Expense table
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit,
    QTabWidget, QMessageBox, QScrollArea, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from datetime import datetime, date

from models.database import ExpenseCategory, ExpensePayment, Setting, SCHOOL_MONTHS
from themes.style import (
    DIALOG_CSS, TABLE_CSS, PRIMARY, PRIMARY_LIGHT, SUCCESS, SUCCESS_LIGHT,
    DANGER, DANGER_LIGHT, WARNING, WARNING_LIGHT, INFO, INFO_LIGHT,
    TEAL, TEAL_LIGHT, BORDER, BG_CARD, TEXT_MAIN, TEXT_SUB
)

# ── Shared styles ──────────────────────────────────────────────────────────────
BTN     = (f'QPushButton {{ background:{PRIMARY}; color:white; border:none; '
           f'border-radius:8px; padding:9px 20px; font-weight:600; font-size:13px; }}'
           f'QPushButton:hover {{ background:#4338CA; }}')
BTN_SEC = ('QPushButton { background:#F3F4F6; color:#374151; border:1px solid #E5E7EB; '
           'border-radius:8px; padding:9px 20px; font-weight:500; font-size:13px; }'
           'QPushButton:hover { background:#E5E7EB; }')
BTN_SUC = (f'QPushButton {{ background:{SUCCESS}; color:white; border:none; '
           f'border-radius:8px; padding:9px 20px; font-weight:700; font-size:13px; }}'
           f'QPushButton:hover {{ background:#059669; }}')
BTN_DNG = (f'QPushButton {{ background:{DANGER_LIGHT}; color:#DC2626; '
           f'border:1px solid #FECACA; border-radius:8px; padding:9px 20px; '
           f'font-weight:600; font-size:13px; }}'
           f'QPushButton:hover {{ background:#FECACA; }}')
BTN_DIS = ('QPushButton { background:#D1D5DB; color:#9CA3AF; border:none; '
           'border-radius:8px; padding:9px 20px; font-weight:700; font-size:13px; }')
FIELD   = (f'QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit {{'
           f'background:white; border:1.5px solid {BORDER}; border-radius:10px; '
           f'color:{TEXT_MAIN}; padding:0 12px; font-size:13px; min-height:38px; }}'
           f'QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color:{PRIMARY}; }}'
           f'QTextEdit {{ padding:8px 12px; min-height:56px; }}'
           f'QComboBox QAbstractItemView {{ background:white; border:1.5px solid #C7D2FE; '
           f'border-radius:10px; color:{TEXT_MAIN}; padding:4px; outline:none; }}'
           f'QComboBox QAbstractItemView::item {{ padding:8px 12px; border-radius:6px; margin:1px 4px; }}'
           f'QComboBox QAbstractItemView::item:hover {{ background:{PRIMARY_LIGHT}; }}')
TAB_CSS = f"""
    QTabWidget::pane {{ border:none; background:transparent; }}
    QTabBar::tab {{ background:transparent; color:{TEXT_SUB}; border:none;
        border-bottom:2px solid transparent; padding:10px 24px;
        font-size:13px; font-weight:500; margin-right:4px; }}
    QTabBar::tab:selected {{ color:{PRIMARY}; border-bottom:2px solid {PRIMARY}; font-weight:700; }}
    QTabBar::tab:hover:!selected {{ color:{TEXT_MAIN}; background:#F9FAFB;
        border-radius:8px 8px 0 0; }}
"""

def _get_school_year(session) -> str:
    s = session.query(Setting).filter_by(key='school_year').first()
    return s.value if s else '2024-25'

def _flbl(text):
    l = QLabel(text)
    l.setStyleSheet('color:#374151; font-size:12px; font-weight:600; background:transparent;')
    return l

def _mini_kpi(label, value, accent, light):
    card = QFrame()
    card.setStyleSheet(f'QFrame {{ background:{light}; border:1px solid {accent}33; '
                       f'border-radius:12px; border-left:4px solid {accent}; }}')
    card.setFixedHeight(80)
    cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 10); cl.setSpacing(3)
    val_lbl = QLabel(str(value))
    val_lbl.setStyleSheet(f'color:{accent}; font-size:20px; font-weight:800; background:transparent;')
    lbl = QLabel(label)
    lbl.setStyleSheet(f'color:{TEXT_SUB}; font-size:11px; font-weight:500; background:transparent;')
    cl.addWidget(val_lbl); cl.addWidget(lbl)
    card._val = val_lbl
    return card


# ── Category Dialog ───────────────────────────────────────────────────────────

class CategoryDialog(QDialog):
    """Add or edit an ExpenseCategory."""
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.setWindowTitle('Modifier catégorie' if category else 'Nouvelle catégorie')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 520, 380)
        self.setStyleSheet(DIALOG_CSS + f'QDialog {{ background:#F7F8FC; }}{FIELD}')
        self._setup_ui()
        if category:
            self._populate(category)

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        hdr = QFrame(); hdr.setStyleSheet(f'QFrame {{ background:{PRIMARY}; }}')
        hdr.setFixedHeight(54)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        ht = QLabel(f'{"Modifier" if self.category else "Nouvelle"} catégorie de dépense')
        ht.setStyleSheet('color:white; font-size:14px; font-weight:700; background:transparent;')
        hl.addWidget(ht)
        outer.addWidget(hdr)

        content = QWidget(); content.setStyleSheet('background:transparent;')
        form = QFormLayout(content)
        form.setContentsMargins(28,24,28,16); form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.name = QLineEdit(); self.name.setPlaceholderText('ex: Loyer, Eau, Électricité...')
        self.etype = QComboBox()
        self.etype.addItem('Fixe (montant prévisible)', 'fixed')
        self.etype.addItem('Variable (montant fluctuant)', 'variable')
        self.monthly_amount = QDoubleSpinBox()
        self.monthly_amount.setRange(0, 999999); self.monthly_amount.setSuffix(' MAD')
        self.monthly_amount.setDecimals(2)
        self.notes = QTextEdit(); self.notes.setMaximumHeight(70)
        self.active_cb = QCheckBox('Catégorie active')
        self.active_cb.setChecked(True)
        self.active_cb.setStyleSheet(f'color:{TEXT_MAIN}; font-size:13px; background:transparent;')

        form.addRow(_flbl('Nom *:'),            self.name)
        form.addRow(_flbl('Type:'),             self.etype)
        form.addRow(_flbl('Montant mensuel:'),  self.monthly_amount)
        form.addRow(_flbl('Notes:'),            self.notes)
        form.addRow(_flbl(''),                  self.active_cb)
        outer.addWidget(content, 1)

        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background:white; border-top:1px solid {BORDER}; }}')
        footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24,0,24,0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        save = QPushButton('💾  Enregistrer'); save.setStyleSheet(BTN); save.clicked.connect(self._save)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(save)
        outer.addWidget(footer)

    def _populate(self, c):
        self.name.setText(c.name or '')
        idx = self.etype.findData(c.expense_type or 'fixed')
        if idx >= 0: self.etype.setCurrentIndex(idx)
        self.monthly_amount.setValue(c.monthly_amount or 0)
        self.notes.setText(c.notes or '')
        self.active_cb.setChecked(bool(c.active))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, 'Erreur', 'Le nom est obligatoire.')
            return
        self.accept()

    def get_data(self):
        return {
            'name':           self.name.text().strip(),
            'expense_type':   self.etype.currentData(),
            'monthly_amount': self.monthly_amount.value(),
            'notes':          self.notes.toPlainText().strip(),
            'active':         self.active_cb.isChecked(),
        }


# ── Pay Expense Dialog ────────────────────────────────────────────────────────

class PayExpenseDialog(QDialog):
    """
    Pay one ExpenseCategory for a given month.
    Prevents duplicates: one ExpensePayment per category × month × year.
    """
    def __init__(self, parent, category: ExpenseCategory, session,
                 month: str = None, year: int = None):
        super().__init__(parent)
        self.category = category
        self.session  = session
        self.month    = month or SCHOOL_MONTHS[0]
        self.year     = year  or datetime.now().year
        self.setWindowTitle(f'Payer — {category.name}')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 520, 420)
        self.setStyleSheet(DIALOG_CSS + f'QDialog {{ background:#F7F8FC; }}{FIELD}')
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        hdr = QFrame(); hdr.setStyleSheet(f'QFrame {{ background:{DANGER}; }}')
        hdr.setFixedHeight(54)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        ht = QLabel(f'💸  Paiement — {self.category.name}')
        ht.setStyleSheet('color:white; font-size:14px; font-weight:700; background:transparent;')
        hl.addWidget(ht)
        outer.addWidget(hdr)

        content = QWidget(); content.setStyleSheet('background:transparent;')
        cl = QVBoxLayout(content); cl.setContentsMargins(28,22,28,16); cl.setSpacing(14)

        # Category info card
        info = QFrame()
        info.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:12px; }}')
        il = QVBoxLayout(info); il.setContentsMargins(18,14,18,14); il.setSpacing(8)
        for label, value, color in [
            ('Catégorie',      self.category.name,                           TEXT_MAIN),
            ('Type',           'Fixe' if self.category.expense_type=='fixed' else 'Variable', TEXT_SUB),
            ('Montant prévu',  f'{self.category.monthly_amount:.0f} MAD',   PRIMARY),
        ]:
            rh = QHBoxLayout(); rh.setContentsMargins(0,0,0,0)
            lb = QLabel(label+' :')
            lb.setStyleSheet(f'color:{TEXT_SUB}; font-size:12px; font-weight:600; '
                             f'min-width:110px; background:transparent;')
            vb = QLabel(value)
            vb.setStyleSheet(f'color:{color}; font-size:13px; font-weight:700; background:transparent;')
            rh.addWidget(lb); rh.addWidget(vb); rh.addStretch()
            il.addLayout(rh)
        cl.addWidget(info)

        # Month / Year / Amount
        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)

        self.month_combo = QComboBox()
        self.month_combo.addItems(SCHOOL_MONTHS)
        idx = self.month_combo.findText(self.month)
        if idx >= 0: self.month_combo.setCurrentIndex(idx)
        self.month_combo.currentTextChanged.connect(self._check_duplicate)

        self.year_input = QLineEdit(str(self.year))
        self.year_input.setMaximumWidth(110)
        self.year_input.textChanged.connect(self._check_duplicate)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999)
        self.amount_spin.setSuffix(' MAD')
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(self.category.monthly_amount or 0)

        self.notes_input = QLineEdit(); self.notes_input.setPlaceholderText('Note optionnelle...')

        form.addRow(_flbl('Mois:'),    self.month_combo)
        form.addRow(_flbl('Année:'),   self.year_input)
        form.addRow(_flbl('Montant:'), self.amount_spin)
        form.addRow(_flbl('Notes:'),   self.notes_input)
        cl.addLayout(form)

        # Duplicate warning banner (hidden by default)
        self.dup_banner = QFrame()
        self.dup_banner.setStyleSheet(
            f'QFrame {{ background:{WARNING_LIGHT}; border:1.5px solid {WARNING}; border-radius:10px; }}'
        )
        dbl = QHBoxLayout(self.dup_banner); dbl.setContentsMargins(14,10,14,10)
        self.dup_lbl = QLabel('⚠️  Paiement déjà enregistré pour ce mois.')
        self.dup_lbl.setStyleSheet(f'color:#92400E; font-size:12px; font-weight:600; background:transparent;')
        dbl.addWidget(self.dup_lbl)
        self.dup_banner.setVisible(False)
        cl.addWidget(self.dup_banner)
        cl.addStretch()
        outer.addWidget(content, 1)

        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background:white; border-top:1px solid {BORDER}; }}')
        footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24,0,24,0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        self.pay_btn = QPushButton('✅  Valider Paiement')
        self.pay_btn.setStyleSheet(BTN_SUC)
        self.pay_btn.clicked.connect(self._pay)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(self.pay_btn)
        outer.addWidget(footer)

        self._check_duplicate()

    def _check_duplicate(self):
        month = self.month_combo.currentText()
        try:
            year = int(self.year_input.text())
        except ValueError:
            year = 0
        exists = self.session.query(ExpensePayment).filter_by(
            expense_category_id=self.category.id, month=month, year=year
        ).first() is not None
        self.dup_banner.setVisible(exists)
        self.pay_btn.setEnabled(not exists)
        self.pay_btn.setStyleSheet(BTN_DIS if exists else BTN_SUC)

    def _pay(self):
        month = self.month_combo.currentText()
        try:
            year = int(self.year_input.text())
        except ValueError:
            QMessageBox.warning(self, 'Erreur', 'Année invalide.'); return
        amount = self.amount_spin.value()

        # Final duplicate guard
        if self.session.query(ExpensePayment).filter_by(
            expense_category_id=self.category.id, month=month, year=year
        ).first():
            QMessageBox.warning(self, 'Doublon',
                f'Un paiement pour {self.category.name} / {month} {year} existe déjà.')
            return

        ep = ExpensePayment(
            expense_category_id = self.category.id,
            month        = month,
            year         = year,
            amount       = amount,
            payment_date = datetime.now(),
            notes        = self.notes_input.text().strip(),
        )
        self.session.add(ep)
        self.session.commit()
        QMessageBox.information(
            self, 'Succès',
            f'✅ Paiement enregistré !\n\n'
            f'Catégorie : {self.category.name}\n'
            f'Mois      : {month} {year}\n'
            f'Montant   : {amount:.2f} MAD'
        )
        self.accept()


# ── Main ExpensesWidget ───────────────────────────────────────────────────────

class ExpensesWidget(QWidget):
    """
    Two-tab expense management:
      Tab 1 — Current month: shows all categories with Expected / Paid / Remaining
      Tab 2 — Categories: add/edit expense categories
    """
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setStyleSheet('background:transparent;')
        self._setup_ui()
        self._load_data()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title
        tr = QHBoxLayout()
        title = QLabel('💸  Gestion des Dépenses')
        title.setStyleSheet(
            f'color:{TEXT_MAIN}; font-size:16px; font-weight:800; background:transparent;'
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

        # Month / Year selector
        sel_row = QHBoxLayout(); sel_row.setSpacing(10)
        month_lbl = QLabel('Mois sélectionné :')
        month_lbl.setStyleSheet(f'color:{TEXT_SUB}; font-size:12px; font-weight:600; background:transparent;')
        self.month_combo = QComboBox()
        self.month_combo.addItems(SCHOOL_MONTHS)
        self.month_combo.setCurrentIndex(
            self._cur_month_idx()
        )
        combo_css = (f'QComboBox {{ background:white; border:1.5px solid {BORDER}; '
                     f'border-radius:10px; color:{TEXT_MAIN}; padding:0 12px; '
                     f'font-size:13px; min-width:160px; height:40px; }}'
                     f'QComboBox QAbstractItemView {{ background:white; border:1.5px solid #C7D2FE; '
                     f'border-radius:10px; color:{TEXT_MAIN}; padding:4px; outline:none; }}'
                     f'QComboBox QAbstractItemView::item {{ padding:8px 12px; border-radius:6px; '
                     f'margin:1px 4px; }}'
                     f'QComboBox QAbstractItemView::item:hover {{ background:{PRIMARY_LIGHT}; }}')
        self.month_combo.setStyleSheet(combo_css)
        self.month_combo.currentIndexChanged.connect(self._load_data)

        self.year_combo = QComboBox()
        cur_year = datetime.now().year
        for y in range(cur_year - 2, cur_year + 2):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentIndex(2)
        self.year_combo.setStyleSheet(combo_css)
        self.year_combo.currentIndexChanged.connect(self._load_data)

        sel_row.addWidget(month_lbl)
        sel_row.addWidget(self.month_combo)
        sel_row.addWidget(self.year_combo)
        sel_row.addStretch()
        layout.addLayout(sel_row)

        # Tabs
        tabs = QTabWidget(); tabs.setStyleSheet(TAB_CSS)

        # ── Tab 1 : Monthly expenses status ───────────────────────────────────
        tab1 = QWidget(); tab1.setStyleSheet('background:transparent;')
        t1l = QVBoxLayout(tab1); t1l.setContentsMargins(0,14,0,0); t1l.setSpacing(12)

        tcard = QFrame()
        tcard.setStyleSheet(
            f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}'
        )
        tcl = QVBoxLayout(tcard); tcl.setContentsMargins(0,0,0,0)
        self.month_table = QTableWidget()
        self.month_table.setColumnCount(6)
        self.month_table.setHorizontalHeaderLabels(
            ['Catégorie', 'Type', 'Montant prévu', 'Montant payé', 'Reste', 'Statut']
        )
        self.month_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.month_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.month_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.month_table.setAlternatingRowColors(True)
        self.month_table.verticalHeader().setVisible(False)
        self.month_table.setShowGrid(False)
        self.month_table.setStyleSheet(TABLE_CSS)
        self.month_table.doubleClicked.connect(self._pay_selected)
        tcl.addWidget(self.month_table)
        t1l.addWidget(tcard, 1)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet('color:#9CA3AF; font-size:12px; background:transparent;')
        pay_btn = QPushButton('💸  Payer la dépense sélectionnée')
        pay_btn.setStyleSheet(BTN)
        pay_btn.clicked.connect(self._pay_selected)
        btn_row.addWidget(self.status_lbl); btn_row.addStretch(); btn_row.addWidget(pay_btn)
        t1l.addLayout(btn_row)

        # ── Tab 2 : Categories management ─────────────────────────────────────
        tab2 = QWidget(); tab2.setStyleSheet('background:transparent;')
        t2l = QVBoxLayout(tab2); t2l.setContentsMargins(0,14,0,0); t2l.setSpacing(12)

        tb2 = QHBoxLayout(); tb2.setSpacing(10)
        add_cat_btn = QPushButton('＋  Ajouter catégorie'); add_cat_btn.setStyleSheet(BTN)
        add_cat_btn.clicked.connect(self._add_category)
        tb2.addStretch(); tb2.addWidget(add_cat_btn)
        t2l.addLayout(tb2)

        ccard = QFrame()
        ccard.setStyleSheet(
            f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}'
        )
        ccl = QVBoxLayout(ccard); ccl.setContentsMargins(0,0,0,0)
        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(5)
        self.cat_table.setHorizontalHeaderLabels(
            ['Nom', 'Type', 'Montant mensuel prévu', 'Statut', 'Nb paiements']
        )
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cat_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cat_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cat_table.setAlternatingRowColors(True)
        self.cat_table.verticalHeader().setVisible(False)
        self.cat_table.setShowGrid(False)
        self.cat_table.setStyleSheet(TABLE_CSS)
        ccl.addWidget(self.cat_table)
        t2l.addWidget(ccard, 1)

        cat_btn_row = QHBoxLayout(); cat_btn_row.setSpacing(8)
        edit_btn = QPushButton('✏️  Modifier'); edit_btn.setStyleSheet(BTN_SEC)
        edit_btn.clicked.connect(self._edit_category)
        del_btn = QPushButton('🗑️  Désactiver'); del_btn.setStyleSheet(BTN_DNG)
        del_btn.clicked.connect(self._toggle_category)
        cat_btn_row.addStretch(); cat_btn_row.addWidget(edit_btn); cat_btn_row.addWidget(del_btn)
        t2l.addLayout(cat_btn_row)

        # ── Tab 3 : Full payment history ──────────────────────────────────────
        tab3 = QWidget(); tab3.setStyleSheet('background:transparent;')
        t3l = QVBoxLayout(tab3); t3l.setContentsMargins(0,14,0,0); t3l.setSpacing(12)

        hcard = QFrame()
        hcard.setStyleSheet(
            f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}'
        )
        hcl = QVBoxLayout(hcard); hcl.setContentsMargins(0,0,0,0)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ['Catégorie', 'Mois', 'Année', 'Montant payé', 'Date', 'Notes']
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setShowGrid(False)
        self.history_table.setStyleSheet(TABLE_CSS)
        hcl.addWidget(self.history_table)
        t3l.addWidget(hcard, 1)

        self.hist_lbl = QLabel()
        self.hist_lbl.setStyleSheet('color:#9CA3AF; font-size:12px; background:transparent;')
        t3l.addWidget(self.hist_lbl)

        tabs.addTab(tab1, '📅  Dépenses du Mois')
        tabs.addTab(tab2, '⚙️  Catégories')
        tabs.addTab(tab3, '📋  Historique Complet')
        layout.addWidget(tabs, 1)

        self.all_categories = []

    def _cur_month_idx(self):
        m = datetime.now().month
        month_order = [9,10,11,12,1,2,3,4,5,6]
        try:
            return month_order.index(m)
        except ValueError:
            return 0

    # ── Data Loading ──────────────────────────────────────────────────────────
    def _load_data(self):
        self.session.expire_all()
        self.all_categories = (
            self.session.query(ExpenseCategory)
            .order_by(ExpenseCategory.name)
            .all()
        )
        month = self.month_combo.currentText()
        year  = self.year_combo.currentData() or datetime.now().year
        self._populate_month_table(month, year)
        self._populate_category_table()
        self._populate_history_table()
        self._update_kpis(month, year)

    def _update_kpis(self, month, year):
        for i in reversed(range(self.kpi_row.count())):
            w = self.kpi_row.itemAt(i).widget()
            if w: w.setParent(None)

        active_cats = [c for c in self.all_categories if c.active]
        expected = sum(c.monthly_amount or 0 for c in active_cats)

        # Paid for selected month
        payments_this_month = self.session.query(ExpensePayment).filter_by(
            month=month, year=year
        ).all()
        paid = sum(p.amount or 0 for p in payments_this_month)
        remaining = max(0.0, expected - paid)

        # Total paid (all time)
        all_payments = self.session.query(ExpensePayment).all()
        total_all = sum(p.amount or 0 for p in all_payments)

        kpis = [
            ('📋  Prévu ce mois',      f'{expected:,.0f} MAD',   PRIMARY,  PRIMARY_LIGHT),
            ('💸  Payé ce mois',       f'{paid:,.0f} MAD',       DANGER,   DANGER_LIGHT),
            ('🔖  Restant ce mois',    f'{remaining:,.0f} MAD',  WARNING,  WARNING_LIGHT),
            ('📊  Total historique',   f'{total_all:,.0f} MAD',  INFO,     INFO_LIGHT),
        ]
        for label, value, accent, light in kpis:
            self.kpi_row.addWidget(_mini_kpi(label, value, accent, light))

    def _populate_month_table(self, month, year):
        active_cats = [c for c in self.all_categories if c.active]
        self.month_table.setRowCount(len(active_cats))

        total_expected = total_paid = 0.0
        paid_count = unpaid_count = 0

        for row, cat in enumerate(active_cats):
            # Find payment for this category × month × year
            payment = self.session.query(ExpensePayment).filter_by(
                expense_category_id=cat.id, month=month, year=year
            ).first()

            expected_amt = cat.monthly_amount or 0
            paid_amt     = payment.amount if payment else 0
            remaining    = max(0.0, expected_amt - paid_amt)
            is_paid      = payment is not None
            status_text  = '✅  Payé'   if is_paid else '⏳  Non payé'
            status_color = SUCCESS      if is_paid else DANGER
            type_str     = 'Fixe' if cat.expense_type == 'fixed' else 'Variable'

            total_expected += expected_amt
            total_paid     += paid_amt
            if is_paid: paid_count += 1
            else:        unpaid_count += 1

            row_data = [
                (cat.name,                TEXT_MAIN, True),
                (type_str,                TEXT_SUB,  False),
                (f'{expected_amt:,.0f} MAD', PRIMARY, False),
                (f'{paid_amt:,.0f} MAD' if is_paid else '—', SUCCESS if is_paid else '#9CA3AF', False),
                (f'{remaining:,.0f} MAD' if remaining > 0 else '—', WARNING if remaining > 0 else SUCCESS, False),
                (status_text,             status_color, True),
            ]
            bg = SUCCESS_LIGHT if is_paid else None
            for col, (text, color, bold) in enumerate(row_data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                if bg:
                    item.setBackground(QColor(bg))
                self.month_table.setItem(row, col, item)
            self.month_table.setRowHeight(row, 44)

        self.status_lbl.setText(
            f'{paid_count} payées  •  {unpaid_count} non payées  •  '
            f'Prévu: {total_expected:,.0f} MAD  •  Payé: {total_paid:,.0f} MAD  •  '
            f'Reste: {max(0, total_expected-total_paid):,.0f} MAD'
        )

    def _populate_category_table(self):
        self.cat_table.setRowCount(len(self.all_categories))
        for row, cat in enumerate(self.all_categories):
            n_payments = len(cat.payments)
            is_active = bool(cat.active)
            row_data = [
                (cat.name,                            TEXT_MAIN if is_active else '#9CA3AF', True),
                ('Fixe' if cat.expense_type=='fixed' else 'Variable', TEXT_SUB, False),
                (f'{cat.monthly_amount:,.0f} MAD',   PRIMARY if is_active else '#9CA3AF', False),
                ('✅ Active' if is_active else '⏸️ Inactive',
                 SUCCESS if is_active else '#9CA3AF',  False),
                (str(n_payments),                     TEXT_SUB, False),
            ]
            for col, (text, color, bold) in enumerate(row_data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.cat_table.setItem(row, col, item)
            self.cat_table.setRowHeight(row, 42)

    def _populate_history_table(self):
        payments = (
            self.session.query(ExpensePayment)
            .order_by(ExpensePayment.year.desc(), ExpensePayment.payment_date.desc())
            .limit(500).all()
        )
        self.history_table.setRowCount(len(payments))
        total = 0.0
        for row, p in enumerate(payments):
            cat_name = p.category.name if p.category else '—'
            row_data = [
                (cat_name,                             TEXT_MAIN, True),
                (p.month or '—',                       TEXT_MAIN, False),
                (str(p.year or ''),                    TEXT_SUB,  False),
                (f'{p.amount:,.2f} MAD',               DANGER,    True),
                (p.payment_date.strftime('%d/%m/%Y %H:%M')
                 if p.payment_date else '—',            TEXT_SUB,  False),
                (p.notes or '—',                       TEXT_SUB,  False),
            ]
            for col, (text, color, bold) in enumerate(row_data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.history_table.setItem(row, col, item)
            self.history_table.setRowHeight(row, 42)
            total += p.amount or 0
        self.hist_lbl.setText(f'{len(payments)} paiements  •  Total: {total:,.2f} MAD')

    # ── Actions ───────────────────────────────────────────────────────────────
    def _get_selected_category(self):
        row = self.month_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez une dépense.')
            return None
        active_cats = [c for c in self.all_categories if c.active]
        return active_cats[row] if row < len(active_cats) else None

    def _pay_selected(self):
        cat = self._get_selected_category()
        if not cat: return
        month = self.month_combo.currentText()
        year  = self.year_combo.currentData() or datetime.now().year
        dlg = PayExpenseDialog(self, cat, self.session, month, year)
        if dlg.exec():
            self._load_data()

    def _add_category(self):
        dlg = CategoryDialog(self)
        if dlg.exec():
            cat = ExpenseCategory(**dlg.get_data())
            self.session.add(cat)
            self.session.commit()
            self._load_data()

    def _edit_category(self):
        row = self.cat_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez une catégorie.')
            return
        cat = self.all_categories[row]
        dlg = CategoryDialog(self, cat)
        if dlg.exec():
            for k, v in dlg.get_data().items():
                setattr(cat, k, v)
            self.session.commit()
            self._load_data()

    def _toggle_category(self):
        row = self.cat_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Sélectionnez une catégorie.')
            return
        cat = self.all_categories[row]
        action = 'activer' if not cat.active else 'désactiver'
        if QMessageBox.question(
            self, 'Confirmation',
            f'{action.capitalize()} la catégorie "{cat.name}" ?',
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            cat.active = not cat.active
            self.session.commit()
            self._load_data()
