import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QDateEdit, QTextEdit, QMessageBox, QFileDialog, QFrame, QScrollArea, QDoubleSpinBox,
    QHeaderView, QAbstractItemView, QRadioButton, QButtonGroup, QGroupBox, QApplication)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QPixmap, QColor, QFont, QBrush
from datetime import datetime, date

from models.database import get_session, Student, MonthRecord, Payment, SCHOOL_MONTHS
from themes.style import (CLASSES, DIALOG_CSS, TABLE_CSS, PRIMARY, PRIMARY_LIGHT,
    SUCCESS, SUCCESS_LIGHT, DANGER, DANGER_LIGHT, WARNING, WARNING_LIGHT,
    NAN_COLOR, NAN_TEXT, BORDER, TEXT_MAIN, TEXT_SUB,
    REINSCRIPTION_OPTIONS, REINSCRIPTION_LABELS, REINSCRIPTION_COLORS)

BTN      = f'QPushButton {{ background:{PRIMARY}; color:white; border:none; border-radius:8px; padding:9px 20px; font-weight:600; font-size:13px; }} QPushButton:hover {{ background:#4338CA; }}'
BTN_SEC  = 'QPushButton { background:#F3F4F6; color:#374151; border:1px solid #E5E7EB; border-radius:8px; padding:9px 20px; font-weight:500; } QPushButton:hover { background:#E5E7EB; }'
BTN_DANGER = f'QPushButton {{ background:{DANGER_LIGHT}; color:#DC2626; border:1px solid #FECACA; border-radius:8px; padding:9px 20px; font-weight:600; }} QPushButton:hover {{ background:#FECACA; }}'
BTN_SUCCESS = f'QPushButton {{ background:{SUCCESS_LIGHT}; color:#059669; border:1px solid #A7F3D0; border-radius:8px; padding:9px 20px; font-weight:600; }} QPushButton:hover {{ background:#A7F3D0; }}'

COMBO_CSS = (
    f'QComboBox {{ background:white; border:1.5px solid {BORDER}; border-radius:10px; color:{TEXT_MAIN}; '
    f'padding:0 12px; font-size:13px; min-width:140px; height:40px; }}'
    f'QComboBox QAbstractItemView {{ background:white; border:1.5px solid #C7D2FE; border-radius:10px; '
    f'color:{TEXT_MAIN}; padding:4px; outline:none; }}'
    f'QComboBox QAbstractItemView::item {{ padding:9px 14px; border-radius:6px; margin:1px 4px; color:{TEXT_MAIN}; }}'
    f'QComboBox QAbstractItemView::item:hover {{ background:#F5F3FF; color:{PRIMARY}; }}'
    f'QComboBox QAbstractItemView::item:selected {{ background:{PRIMARY_LIGHT}; color:{PRIMARY}; font-weight:600; }}'
)


def flbl(text):
    l = QLabel(text)
    l.setStyleSheet('color:#374151; font-size:12px; font-weight:600; background:transparent;')
    return l

def section_label(text):
    l = QLabel(text)
    l.setStyleSheet('color:#9CA3AF; font-size:10px; font-weight:700; letter-spacing:1px; background:transparent; margin-top:6px;')
    return l

def chip(text, fg, bg):
    c = QLabel(text)
    c.setStyleSheet(f'color:{fg}; background:{bg}; border-radius:10px; padding:4px 12px; font-size:11px; font-weight:600;')
    return c


class StudentDialog(QDialog):
    def __init__(self, parent=None, student=None):
        super().__init__(parent)
        self.student = student
        self.photo_path = getattr(student, 'photo', None)
        self.setWindowTitle('Modifier élève' if student else 'Nouvel élève')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 740, 740)
        self.setStyleSheet(DIALOG_CSS + 'QDialog { background:#F7F8FC; }')
        self._setup_ui()
        if student:
            self._populate(student)

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        # Coloured header
        hdr = QFrame(); hdr.setStyleSheet(f'QFrame {{ background:{PRIMARY}; }}'); hdr.setFixedHeight(58)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        ht = QLabel('👤  ' + ('Modifier élève' if self.student else 'Ajouter un élève'))
        ht.setStyleSheet('color:white; font-size:15px; font-weight:700; background:transparent;')
        hl.addWidget(ht)
        outer.addWidget(hdr)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border:none; background:#F7F8FC; }')
        content = QWidget(); content.setStyleSheet('background:transparent;')
        form = QFormLayout(content)
        form.setContentsMargins(28,22,28,16); form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # ── Section: Identity ─────────────────────────────────────
        form.addRow('', section_label('INFORMATIONS PERSONNELLES'))
        self.first_name = QLineEdit(); self.first_name.setPlaceholderText('Prénom')
        self.last_name  = QLineEdit(); self.last_name.setPlaceholderText('Nom (majuscules)')
        self.gender = QComboBox(); self.gender.addItems(['', 'Masculin', 'Féminin'])
        self.birth_date = QDateEdit(); self.birth_date.setCalendarPopup(True)
        self.birth_date.setDate(QDate(2010, 1, 1)); self.birth_date.setDisplayFormat('dd/MM/yyyy')
        self.class_name = QComboBox(); self.class_name.addItems([''] + CLASSES)
        self.address = QTextEdit(); self.address.setMaximumHeight(52)
        self.parent_name     = QLineEdit()
        self.parent_phone    = QLineEdit(); self.parent_phone.setPlaceholderText('0600000000')
        self.emergency_phone = QLineEdit()

        form.addRow(flbl('Prénom *:'),          self.first_name)
        form.addRow(flbl('Nom *:'),             self.last_name)
        form.addRow(flbl('Sexe:'),              self.gender)
        form.addRow(flbl('Date de naissance:'), self.birth_date)
        form.addRow(flbl('Classe:'),            self.class_name)
        form.addRow(flbl('Adresse:'),           self.address)
        form.addRow(flbl('Parent / Tuteur:'),   self.parent_name)
        form.addRow(flbl('Tél. parent:'),       self.parent_phone)
        form.addRow(flbl('Tél. urgence:'),      self.emergency_phone)

        # ── Section: Financial ────────────────────────────────────
        form.addRow('', section_label('INFORMATIONS FINANCIÈRES'))

        self.monthly_fee = QDoubleSpinBox()
        self.monthly_fee.setRange(0,99999); self.monthly_fee.setSuffix(' MAD')
        self.monthly_fee.setDecimals(0); self.monthly_fee.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        form.addRow(flbl('Frais mensuel:'), self.monthly_fee)

        self.insurance_amount = QDoubleSpinBox()
        self.insurance_amount.setRange(0,99999); self.insurance_amount.setSuffix(' MAD')
        self.insurance_amount.setDecimals(0)
        form.addRow(flbl('Frais assurance:'), self.insurance_amount)

        self.insurance_paid_cb = QCheckBox('Assurance déjà payée')
        form.addRow('', self.insurance_paid_cb)

        # Transport group
        tg = QGroupBox('🚌  Transport scolaire')
        tg.setStyleSheet('QGroupBox { border:1.5px solid #EAEDF3; border-radius:10px; margin-top:12px; padding:14px 14px 10px 14px; background:white; font-weight:600; color:#374151; font-size:12px; } QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; color:#4F46E5; background:white; font-size:11px; }')
        tl = QVBoxLayout(tg); tl.setSpacing(8)

        radio_row = QHBoxLayout(); radio_row.setSpacing(24)
        self.transport_yes = QRadioButton('✅  Oui — avec transport')
        self.transport_no  = QRadioButton('❌  Non — pas de transport (NA)')
        self.transport_no.setChecked(True)
        self.transport_grp = QButtonGroup(self)
        self.transport_grp.addButton(self.transport_yes, 1)
        self.transport_grp.addButton(self.transport_no,  0)
        radio_row.addWidget(self.transport_yes); radio_row.addWidget(self.transport_no); radio_row.addStretch()
        tl.addLayout(radio_row)

        fee_row = QHBoxLayout(); fee_row.setSpacing(12)
        self.transport_fee = QDoubleSpinBox()
        self.transport_fee.setRange(0,9999); self.transport_fee.setSuffix(' MAD')
        self.transport_fee.setDecimals(0); self.transport_fee.setEnabled(False)
        self.transport_fee.setFixedWidth(140)
        fee_lbl = QLabel('Montant mensuel:')
        fee_lbl.setStyleSheet('color:#374151; font-size:12px; background:transparent;')
        fee_row.addWidget(fee_lbl); fee_row.addWidget(self.transport_fee); fee_row.addStretch()
        tl.addLayout(fee_row)
        self.transport_yes.toggled.connect(lambda c: self.transport_fee.setEnabled(c))
        form.addRow('', tg)

        # ── Section: Re-inscription ───────────────────────────────
        form.addRow('', section_label('RE-INSCRIPTION ANNÉE SUIVANTE'))
        self.reinscription = QComboBox()
        for k, v in REINSCRIPTION_LABELS.items():
            self.reinscription.addItem(v, k)
        form.addRow(flbl('Statut:'), self.reinscription)

        self.notes = QTextEdit(); self.notes.setMaximumHeight(52)
        form.addRow(flbl('Notes:'), self.notes)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background:white; border-top:1px solid {BORDER}; }}')
        footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24,0,24,0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        save   = QPushButton('💾  Enregistrer'); save.setStyleSheet(BTN); save.clicked.connect(self._save)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(save)
        outer.addWidget(footer)

    def _populate(self, s):
        self.first_name.setText(s.first_name or '')
        self.last_name.setText(s.last_name or '')
        if s.gender: self.gender.setCurrentText(s.gender)
        if s.birth_date:
            self.birth_date.setDate(QDate(s.birth_date.year, s.birth_date.month, s.birth_date.day))
        if s.class_name:
            idx = self.class_name.findText(s.class_name)
            if idx >= 0: self.class_name.setCurrentIndex(idx)
        self.address.setText(s.address or '')
        self.parent_name.setText(s.parent_name or '')
        self.parent_phone.setText(s.parent_phone or '')
        self.emergency_phone.setText(s.emergency_phone or '')
        self.monthly_fee.setValue(s.monthly_fee or 0)
        self.insurance_amount.setValue(getattr(s, 'insurance_amount', 0) or 0)
        self.insurance_paid_cb.setChecked(s.insurance_paid or False)
        self.notes.setText((s.notes or '').replace(f'MAT:{(s.notes or "").split("|")[0].replace("MAT:","")}', '').strip('|') if s.notes and s.notes.startswith('MAT:') else s.notes or '')

        has_t = getattr(s, 'has_transport', False) or False
        tf    = getattr(s, 'transport_fee', 0) or 0
        if has_t:
            self.transport_yes.setChecked(True)
            self.transport_fee.setValue(tf)
            self.transport_fee.setEnabled(True)
        else:
            self.transport_no.setChecked(True)

        rs = getattr(s, 'reinscription_status', 'pending') or 'pending'
        idx = self.reinscription.findData(rs)
        if idx >= 0: self.reinscription.setCurrentIndex(idx)

    def _save(self):
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            QMessageBox.warning(self, 'Champs manquants', 'Le prénom et le nom sont obligatoires.')
            return
        if not self.class_name.currentText():
            QMessageBox.warning(self, 'Classe manquante', 'Veuillez sélectionner une classe.')
            return
        self.accept()

    def get_data(self):
        bd = self.birth_date.date()
        has_transport = self.transport_yes.isChecked()
        return {
            'first_name': self.first_name.text().strip(),
            'last_name':  self.last_name.text().strip().upper(),
            'gender':     self.gender.currentText() or None,
            'birth_date': date(bd.year(), bd.month(), bd.day()),
            'class_name': self.class_name.currentText() or None,
            'address':    self.address.toPlainText() or None,
            'parent_name':     self.parent_name.text().strip() or None,
            'parent_phone':    self.parent_phone.text().strip() or None,
            'emergency_phone': self.emergency_phone.text().strip() or None,
            'monthly_fee':     self.monthly_fee.value(),
            'insurance_amount': self.insurance_amount.value(),
            'insurance_paid':  self.insurance_paid_cb.isChecked(),
            'has_transport':   has_transport,
            'transport_fee':   self.transport_fee.value() if has_transport else 0.0,
            'reinscription_status': self.reinscription.currentData() or 'pending',
            'notes':      self.notes.toPlainText() or None,
        }


class MonthManagerDialog(QDialog):
    def __init__(self, parent, student, session):
        super().__init__(parent)
        self.student = student; self.session = session
        self.setWindowTitle(f'Gestion des mois — {student.first_name} {student.last_name}')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 640, 580)
        self.setStyleSheet(DIALOG_CSS + 'QDialog { background:#F7F8FC; }')
        self._setup_ui()

    def _get_year(self):
        s = self.session.query(__import__('models.database', fromlist=['Setting']).Setting).filter_by(key='school_year').first()
        return s.value if s else '2024-25'

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        hdr = QFrame(); hdr.setStyleSheet('QFrame { background:#8B5CF6; }'); hdr.setFixedHeight(58)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        ht = QLabel(f'📅  Mois — {self.student.first_name} {self.student.last_name}')
        ht.setStyleSheet('color:white; font-size:14px; font-weight:700; background:transparent;')
        hl.addWidget(ht); outer.addWidget(hdr)

        content = QWidget(); content.setStyleSheet('background:transparent;')
        cl = QVBoxLayout(content); cl.setContentsMargins(24,18,24,16); cl.setSpacing(12)

        # Info strip
        info = QFrame()
        info.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:10px; }}')
        il = QHBoxLayout(info); il.setContentsMargins(14,10,14,10); il.setSpacing(20)
        for lbl_text, val in [
            ('Code', self.student.code or '—'),
            ('Classe', self.student.class_name or '—'),
            ('Mensuel', f'{self.student.monthly_fee:.0f} MAD'),
            ('Transport', f'{getattr(self.student,"transport_fee",0):.0f} MAD' if getattr(self.student,"has_transport",False) else 'NA'),
        ]:
            col = QVBoxLayout(); col.setSpacing(1)
            tl = QLabel(lbl_text); tl.setStyleSheet(f'color:{TEXT_SUB}; font-size:10px; font-weight:600; letter-spacing:0.5px; background:transparent;')
            vl = QLabel(val); vl.setStyleSheet(f'color:{TEXT_MAIN}; font-size:13px; font-weight:700; background:transparent;')
            col.addWidget(tl); col.addWidget(vl); il.addLayout(col)
        il.addStretch()
        cl.addWidget(info)

        # Legend
        leg = QHBoxLayout(); leg.setSpacing(10)
        for text, fg, bg in [('✅ Payé', SUCCESS, SUCCESS_LIGHT), ('⏳ Impayé', DANGER, DANGER_LIGHT), ('⊘ NAN', '#854D0E', NAN_COLOR)]:
            l = QLabel(text); l.setStyleSheet(f'color:{fg}; background:{bg}; border-radius:8px; padding:3px 10px; font-size:11px; font-weight:600;')
            leg.addWidget(l)
        leg.addStretch(); cl.addLayout(leg)

        # Month grid
        school_year = self._get_year()
        grid_frame = QFrame()
        grid_frame.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:12px; }}')
        gl = QVBoxLayout(grid_frame); gl.setContentsMargins(16,14,16,14); gl.setSpacing(6)

        self.month_combos = {}
        for month in SCHOOL_MONTHS:
            record = self.session.query(MonthRecord).filter_by(
                student_id=self.student.id, month_name=month, school_year=school_year
            ).first()
            if not record:
                record = MonthRecord(student_id=self.student.id, month_name=month,
                    school_year=school_year, status='unpaid', amount=self.student.monthly_fee)
                self.session.add(record)

            row_layout = QHBoxLayout(); row_layout.setSpacing(10)
            lbl = QLabel(month); lbl.setFixedWidth(100)
            lbl.setStyleSheet(f'color:#374151; font-weight:600; font-size:13px; background:transparent;')

            combo = QComboBox()
            combo.addItem('⏳  Impayé', 'unpaid')
            combo.addItem('✅  Payé',   'paid')
            combo.addItem('⊘  NAN (non inscrit)', 'nan')
            idx = {'paid':1,'unpaid':0,'nan':2}.get(record.status, 0)
            combo.setCurrentIndex(idx)
            self._style_combo(combo, record.status)
            combo.currentIndexChanged.connect(lambda _, c=combo: self._style_combo(c, c.currentData()))

            amt_spin = QDoubleSpinBox()
            amt_spin.setRange(0,99999); amt_spin.setSuffix(' MAD')
            amt_spin.setDecimals(0); amt_spin.setValue(record.amount or self.student.monthly_fee)
            amt_spin.setFixedWidth(110)
            amt_spin.setEnabled(record.status != 'nan')
            combo.currentIndexChanged.connect(lambda _, s=amt_spin, c=combo: s.setEnabled(c.currentData() != 'nan'))

            self.month_combos[month] = (combo, amt_spin, record)
            row_layout.addWidget(lbl); row_layout.addWidget(combo)
            row_layout.addStretch(); row_layout.addWidget(amt_spin)
            gl.addLayout(row_layout)

        self.session.flush()
        cl.addWidget(grid_frame)
        outer.addWidget(content, 1)

        footer = QFrame()
        footer.setStyleSheet(f'QFrame {{ background:white; border-top:1px solid {BORDER}; }}')
        footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24,0,24,0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        save   = QPushButton('💾  Enregistrer les statuts'); save.setStyleSheet(BTN); save.clicked.connect(self._save)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(save)
        outer.addWidget(footer)

    def _style_combo(self, combo, status):
        styles = {
            'paid':   (SUCCESS_LIGHT, SUCCESS),
            'unpaid': (DANGER_LIGHT,  DANGER),
            'nan':    (NAN_COLOR,     '#854D0E'),
        }
        bg, fg = styles.get(status, ('#F9FAFB', TEXT_MAIN))
        combo.setStyleSheet(f'''
            QComboBox {{ background:{bg}; color:{fg}; border:1.5px solid {bg}; border-radius:8px;
                padding:6px 12px; font-weight:600; font-size:12px; min-width:210px; }}
            QComboBox QAbstractItemView {{ background:white; color:{TEXT_MAIN}; border:1.5px solid #C7D2FE;
                border-radius:10px; padding:4px; outline:none; }}
            QComboBox QAbstractItemView::item {{ padding:8px 14px; border-radius:6px; margin:1px 4px; color:{TEXT_MAIN}; }}
            QComboBox QAbstractItemView::item:hover {{ background:#F5F3FF; color:{PRIMARY}; }}
            QComboBox QAbstractItemView::item:selected {{ background:{PRIMARY_LIGHT}; color:{PRIMARY}; }}
        ''')

    def _save(self):
        for month, (combo, amt_spin, record) in self.month_combos.items():
            record.status = combo.currentData()
            record.amount = amt_spin.value() if combo.currentData() != 'nan' else 0.0
        self.session.commit()
        QMessageBox.information(self, 'Succès ✅', 'Statuts des mois mis à jour avec succès!')
        self.accept()


class StudentsWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setStyleSheet('background:transparent;')
        self.all_students = []
        self._setup_ui()
        self._load_students()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28,24,28,24); layout.setSpacing(14)

        # ── Toolbar ──────────────────────────────────────────────
        tb = QHBoxLayout(); tb.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText('🔍  Nom, code, parent…')
        self.search.setFixedHeight(40); self.search.setFixedWidth(260)
        self.search.setStyleSheet(f'QLineEdit {{ background:white; border:1.5px solid {BORDER}; border-radius:10px; color:{TEXT_MAIN}; padding:0 14px; font-size:13px; }} QLineEdit:focus {{ border-color:{PRIMARY}; }}')
        self.search.textChanged.connect(self._filter)

        self.cls_filter = QComboBox(); self.cls_filter.setStyleSheet(COMBO_CSS)
        self.cls_filter.addItem('Toutes les classes', '')
        for c in CLASSES: self.cls_filter.addItem(c, c)
        self.cls_filter.currentIndexChanged.connect(self._filter)

        self.reinsc_filter = QComboBox(); self.reinsc_filter.setStyleSheet(COMBO_CSS)
        self.reinsc_filter.addItem('Toutes inscriptions', '')
        self.reinsc_filter.addItem('⏳ En attente', 'pending')
        self.reinsc_filter.addItem('✅ Re-inscrits', 'yes')
        self.reinsc_filter.addItem('❌ Non re-inscrits', 'no')
        self.reinsc_filter.currentIndexChanged.connect(self._filter)

        self.transport_filter = QComboBox(); self.transport_filter.setStyleSheet(COMBO_CSS)
        self.transport_filter.addItem('Tout transport', '')
        self.transport_filter.addItem('🚌 Avec transport', 'yes')
        self.transport_filter.addItem('❌ Sans transport', 'no')
        self.transport_filter.currentIndexChanged.connect(self._filter)

        add_btn = QPushButton('＋  Ajouter un élève')
        add_btn.setFixedHeight(40); add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(BTN); add_btn.clicked.connect(self._add_student)

        tb.addWidget(self.search); tb.addWidget(self.cls_filter)
        tb.addWidget(self.reinsc_filter); tb.addWidget(self.transport_filter)
        tb.addStretch(); tb.addWidget(add_btn)
        layout.addLayout(tb)

        # ── Stats chips ───────────────────────────────────────────
        self.chips_row = QHBoxLayout(); self.chips_row.setSpacing(8)
        layout.addLayout(self.chips_row)

        # ── Table ─────────────────────────────────────────────────
        tcard = QFrame()
        tcard.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}')
        tcl = QVBoxLayout(tcard); tcl.setContentsMargins(0,0,0,0)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            'Code','Nom complet','Classe','Parent / Tél.',
            'Mensuel','Transport','Assurance','Re-inscription','Mois payés','Impayés'
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(TABLE_CSS)
        self.table.doubleClicked.connect(self._edit_student)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        tcl.addWidget(self.table)
        layout.addWidget(tcard, 1)

        # ── Action bar ────────────────────────────────────────────
        ab = QHBoxLayout(); ab.setSpacing(8)
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet('color:#9CA3AF; font-size:12px; background:transparent;')

        edit_btn    = QPushButton('✏️  Modifier')
        edit_btn.setStyleSheet(BTN_SEC); edit_btn.clicked.connect(self._edit_student)
        months_btn  = QPushButton('📅  Mois')
        months_btn.setStyleSheet(BTN_SEC); months_btn.clicked.connect(self._manage_months)
        del_btn     = QPushButton('🗑️  Supprimer')
        del_btn.setStyleSheet(BTN_DANGER); del_btn.clicked.connect(self._delete_student)
        pay_btn     = QPushButton('💳  Paiement')
        pay_btn.setStyleSheet(BTN_SUCCESS); pay_btn.clicked.connect(self._open_payment)

        ab.addWidget(self.status_lbl); ab.addStretch()
        ab.addWidget(edit_btn); ab.addWidget(months_btn)
        ab.addWidget(del_btn); ab.addWidget(pay_btn)
        layout.addLayout(ab)

    # ── Data loading ──────────────────────────────────────────────

    def _generate_code(self):
        year = datetime.now().year
        count = self.session.query(Student).count()
        return f'STU-{year}-{count+1:04d}'

    def _month_stats(self, student_id):
        from sqlalchemy import func
        records = self.session.query(MonthRecord).filter_by(
            student_id=student_id, school_year='2024-25'
        ).all()
        paid   = sum(1 for r in records if r.status == 'paid')
        unpaid = sum(1 for r in records if r.status == 'unpaid')
        nan    = sum(1 for r in records if r.status == 'nan')
        return paid, unpaid, nan

    def _load_students(self):
        self.all_students = self.session.query(Student).filter_by(active=True)\
            .order_by(Student.class_name, Student.last_name).all()
        self._populate_table(self.all_students)
        self._update_chips(self.all_students)

    def _update_chips(self, students):
        for i in reversed(range(self.chips_row.count())):
            w = self.chips_row.itemAt(i).widget()
            if w: w.setParent(None)

        total     = len(students)
        transport = sum(1 for s in students if getattr(s,'has_transport',False))
        no_ins    = sum(1 for s in students if not s.insurance_paid)
        r_yes     = sum(1 for s in students if getattr(s,'reinscription_status','pending') == 'yes')
        r_no      = sum(1 for s in students if getattr(s,'reinscription_status','pending') == 'no')
        r_pend    = sum(1 for s in students if getattr(s,'reinscription_status','pending') == 'pending')

        for text, fg, bg in [
            (f'👥 {total} élèves',          PRIMARY,   PRIMARY_LIGHT),
            (f'🚌 {transport} transport',    '#0369A1', '#DBEAFE'),
            (f'✅ {r_yes} re-inscrits',      '#059669', SUCCESS_LIGHT),
            (f'❌ {r_no} non re-inscrits',   '#DC2626', DANGER_LIGHT),
            (f'⏳ {r_pend} en attente',      '#B45309', WARNING_LIGHT),
        ]:
            self.chips_row.addWidget(chip(text, fg, bg))
        if no_ins:
            self.chips_row.addWidget(chip(f'⚠ {no_ins} sans assurance', '#B45309', WARNING_LIGHT))
        self.chips_row.addStretch()
        self.status_lbl.setText(f'{total} élève(s)  •  Double-clic pour modifier  •  Clic-droit pour actions')

    def _populate_table(self, students):
        self.table.setRowCount(len(students))
        for row, s in enumerate(students):
            paid, unpaid, nan = self._month_stats(s.id)
            billable = paid + unpaid   # nan excluded

            # Transport display
            if getattr(s,'has_transport',False):
                t_text  = f'✅ {getattr(s,"transport_fee",0):.0f} MAD'
                t_color = SUCCESS
            else:
                t_text  = 'NA'; t_color = '#9CA3AF'

            ins_text  = '✅ Payée' if s.insurance_paid else '❌ Non'
            ins_color = SUCCESS if s.insurance_paid else DANGER

            rs       = getattr(s,'reinscription_status','pending') or 'pending'
            rs_text  = REINSCRIPTION_LABELS.get(rs, rs)
            rs_color = REINSCRIPTION_COLORS.get(rs, WARNING)

            # Unpaid urgency color
            unpaid_color = DANGER if unpaid > 3 else (WARNING if unpaid > 0 else SUCCESS)

            row_data = [
                (s.code or '',                          '#6B7280',  False),
                (f'{s.first_name} {s.last_name}',       TEXT_MAIN,  True),
                (s.class_name or '—',                   PRIMARY,    False),
                (f'{s.parent_name or "—"}\n{s.parent_phone or ""}', TEXT_SUB, False),
                (f'{s.monthly_fee:.0f} MAD',            TEXT_MAIN,  False),
                (t_text,                                 t_color,    False),
                (ins_text,                               ins_color,  False),
                (rs_text,                                rs_color,   False),
                (f'{paid}/{billable}',                  SUCCESS,    True),
                (str(unpaid),                            unpaid_color, True),
            ]
            for col, (text, color, bold) in enumerate(row_data):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(color))
                if bold:
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.table.setItem(row, col, item)
            self.table.setRowHeight(row, 44)

    def _filter(self):
        search  = self.search.text().lower().strip()
        cls     = self.cls_filter.currentData() or ''
        reinsc  = self.reinsc_filter.currentData() or ''
        transp  = self.transport_filter.currentData() or ''

        filtered = []
        for s in self.all_students:
            if search and not any(search in (v or '').lower() for v in [
                s.first_name, s.last_name, s.code, s.parent_name, s.parent_phone
            ]):
                continue
            if cls and s.class_name != cls:
                continue
            if reinsc and getattr(s,'reinscription_status','pending') != reinsc:
                continue
            if transp == 'yes' and not getattr(s,'has_transport',False):
                continue
            if transp == 'no' and getattr(s,'has_transport',False):
                continue
            filtered.append(s)

        self._populate_table(filtered)
        self._update_chips(filtered)

    # ── CRUD ──────────────────────────────────────────────────────

    def _get_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sélection', 'Veuillez sélectionner un élève dans la liste.')
            return None
        code_item = self.table.item(row, 0)
        if not code_item: return None
        return self.session.query(Student).filter_by(code=code_item.text()).first()

    def _context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        s = self._get_selected()
        if not s: return
        menu = QMenu(self)
        menu.setStyleSheet(f'QMenu {{ background:white; border:1px solid {BORDER}; border-radius:10px; padding:4px; }} QMenu::item {{ padding:8px 20px; border-radius:6px; color:{TEXT_MAIN}; font-size:13px; }} QMenu::item:selected {{ background:{PRIMARY_LIGHT}; color:{PRIMARY}; }}')
        menu.addAction(f'✏️  Modifier {s.first_name} {s.last_name}',  self._edit_student)
        menu.addAction(f'📅  Gérer les mois',                          self._manage_months)
        menu.addAction(f'💳  Enregistrer un paiement',                 self._open_payment)
        menu.addSeparator()
        menu.addAction(f'🗑️  Supprimer',                               self._delete_student)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _add_student(self):
        dlg = StudentDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            s = Student(**data, code=self._generate_code(), registration_date=date.today())
            self.session.add(s); self.session.flush()

            year_setting = self.session.query(__import__('models.database', fromlist=['Setting']).Setting).filter_by(key='school_year').first()
            school_year  = year_setting.value if year_setting else '2024-25'

            for month in SCHOOL_MONTHS:
                self.session.add(MonthRecord(
                    student_id=s.id, month_name=month,
                    school_year=school_year, status='unpaid',
                    amount=s.monthly_fee
                ))
            self.session.commit()
            self._load_students()
            QMessageBox.information(self, '✅ Succès', f'Élève ajouté!\nCode: {s.code}')

    def _edit_student(self):
        s = self._get_selected()
        if not s: return
        dlg = StudentDialog(self, s)
        if dlg.exec():
            for k, v in dlg.get_data().items():
                setattr(s, k, v)
            self.session.commit()
            self._load_students()

    def _delete_student(self):
        s = self._get_selected()
        if not s: return
        reply = QMessageBox.question(
            self, 'Confirmer la suppression',
            f'Supprimer {s.first_name} {s.last_name} ({s.code})?\n\nCette action est irréversible.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            s.active = False
            self.session.commit()
            self._load_students()

    def _open_payment(self):
        s = self._get_selected()
        if not s: return
        from ui.payment_dialog import PaymentDialog
        dlg = PaymentDialog(self, s, self.session)
        dlg.exec()
        self._load_students()

    def _manage_months(self):
        s = self._get_selected()
        if not s: return
        dlg = MonthManagerDialog(self, s, self.session)
        dlg.exec()
        self._load_students()

    def refresh(self):
        self.session.expire_all()
        self._load_students()
