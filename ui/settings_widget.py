"""
settings_widget.py — SGS v4  MODULE 10
Parameters module — fully fixed:
  - All settings saved to Setting table in DB
  - school_year field (critical for payment/insurance scoping)
  - Loaded on startup via get_setting() helper
  - Visual confirmation after save
  - school_year change triggers a warning (affects all scoped data)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFormLayout, QMessageBox, QFrame, QDoubleSpinBox,
    QScrollArea, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from models.database import Setting
from themes.style import (
    PRIMARY, PRIMARY_LIGHT, SUCCESS, SUCCESS_LIGHT, DANGER, DANGER_LIGHT,
    WARNING, WARNING_LIGHT, BORDER, TEXT_MAIN, TEXT_SUB
)

BTN = (f'QPushButton {{ background:{PRIMARY}; color:white; border:none; border-radius:8px; '
       f'padding:11px 28px; font-weight:700; font-size:14px; }}'
       f'QPushButton:hover {{ background:#4338CA; }}')
BTN_SEC = ('QPushButton { background:#F3F4F6; color:#374151; border:1px solid #E5E7EB; '
           'border-radius:8px; padding:9px 20px; font-weight:500; }'
           'QPushButton:hover { background:#E5E7EB; }')
FIELD = (f'QLineEdit, QDoubleSpinBox, QComboBox {{'
         f'background:white; border:1.5px solid {BORDER}; border-radius:8px; '
         f'color:{TEXT_MAIN}; padding:0 12px; font-size:13px; min-height:40px; }}'
         f'QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color:{PRIMARY}; }}'
         f'QComboBox QAbstractItemView {{ background:white; border:1.5px solid #C7D2FE; '
         f'border-radius:10px; color:{TEXT_MAIN}; padding:4px; outline:none; }}'
         f'QComboBox QAbstractItemView::item {{ padding:9px 14px; border-radius:6px; '
         f'margin:1px 4px; }}'
         f'QComboBox QAbstractItemView::item:hover {{ background:{PRIMARY_LIGHT}; }}')


# ── Public helper — used across the app ───────────────────────────────────────
def get_setting(session, key: str, default: str = '') -> str:
    """Load a setting from DB. Used by any module needing settings at runtime."""
    try:
        s = session.query(Setting).filter_by(key=key).first()
        return s.value if s else default
    except Exception:
        return default


def set_setting(session, key: str, value: str):
    """Upsert a setting in DB and commit."""
    s = session.query(Setting).filter_by(key=key).first()
    if s:
        s.value = str(value)
    else:
        session.add(Setting(key=key, value=str(value)))
    session.commit()


# ── UI helpers ────────────────────────────────────────────────────────────────
def _card(title, icon, accent=None):
    accent = accent or PRIMARY
    frame = QFrame()
    frame.setStyleSheet(
        f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}'
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(24, 18, 24, 18)
    layout.setSpacing(14)

    hdr = QHBoxLayout()
    pill = QLabel(icon)
    pill.setFixedSize(38, 38)
    pill.setAlignment(Qt.AlignCenter)
    pill.setStyleSheet(f'background:{PRIMARY_LIGHT}; border-radius:10px; font-size:18px;')
    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(
        f'color:{TEXT_MAIN}; font-size:14px; font-weight:700; background:transparent;'
    )
    hdr.addWidget(pill); hdr.addWidget(title_lbl); hdr.addStretch()
    layout.addLayout(hdr)

    div = QFrame(); div.setFrameShape(QFrame.HLine)
    div.setStyleSheet(f'background:{BORDER}; max-height:1px; border:none;')
    layout.addWidget(div)
    return frame, layout


def _flbl(text):
    l = QLabel(text)
    l.setStyleSheet(
        f'color:#374151; font-size:12px; font-weight:600; '
        f'background:transparent; min-width:180px;'
    )
    return l


def _hint(text):
    l = QLabel(text)
    l.setStyleSheet('color:#9CA3AF; font-size:11px; background:transparent;')
    return l


# ── Main SettingsWidget ───────────────────────────────────────────────────────
class SettingsWidget(QWidget):
    """
    Paramètres module — fully operational.
    Every field is persisted to the Setting table and loaded on init.
    school_year is the most critical field — it scopes all payments/insurance.
    """
    def __init__(self, session):
        super().__init__()
        self.session = session
        self._dirty = False
        self.setStyleSheet('background:transparent;')
        self._setup_ui()
        self._load_settings()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border:none; background:transparent; }')

        container = QWidget(); container.setStyleSheet('background:transparent;')
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 32)
        layout.setSpacing(20)

        # Page header
        page_title = QLabel('⚙️  Paramètres de l\'application')
        page_title.setStyleSheet(
            f'color:{TEXT_MAIN}; font-size:20px; font-weight:800; background:transparent;'
        )
        page_sub = QLabel(
            'Configurez les informations de votre établissement, l\'année scolaire et les tarifs.'
        )
        page_sub.setStyleSheet(f'color:{TEXT_SUB}; font-size:13px; background:transparent;')
        layout.addWidget(page_title)
        layout.addWidget(page_sub)

        # ── 1. SCHOOL YEAR (most critical) ────────────────────────────────────
        yr_card, yr_layout = _card('Année Scolaire', '📅', PRIMARY)
        yr_form = QFormLayout(); yr_form.setSpacing(12); yr_form.setLabelAlignment(Qt.AlignRight)
        yr_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)

        self.school_year = QComboBox()
        years = ['2022-23', '2023-24', '2024-25', '2025-26', '2026-27']
        self.school_year.addItems(years)
        self.school_year.setMinimumWidth(160)
        self.school_year.setStyleSheet(FIELD)
        self.school_year.currentTextChanged.connect(self._mark_dirty)

        yr_form.addRow(_flbl('Année scolaire en cours :'), self.school_year)

        warning_banner = QFrame()
        warning_banner.setStyleSheet(
            f'QFrame {{ background:{WARNING_LIGHT}; border:1px solid {WARNING}33; '
            f'border-radius:10px; border-left:4px solid {WARNING}; }}'
        )
        wb_layout = QHBoxLayout(warning_banner)
        wb_layout.setContentsMargins(14, 10, 14, 10)
        wb_lbl = QLabel(
            '⚠️  L\'année scolaire est utilisée pour scoper les paiements, assurances et '
            'mensualités. Modifier ce paramètre affecte tous les modules.'
        )
        wb_lbl.setWordWrap(True)
        wb_lbl.setStyleSheet(f'color:#92400E; font-size:11px; background:transparent;')
        wb_layout.addWidget(wb_lbl)

        yr_layout.addLayout(yr_form)
        yr_layout.addWidget(warning_banner)
        layout.addWidget(yr_card)

        # ── 2. SCHOOL INFO ────────────────────────────────────────────────────
        info_card, info_layout = _card('Informations de l\'École', '🏫')
        info_form = QFormLayout(); info_form.setSpacing(12)
        info_form.setLabelAlignment(Qt.AlignRight)
        info_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.school_name    = QLineEdit(); self.school_name.setStyleSheet(FIELD)
        self.school_name.setPlaceholderText('Nom de l\'établissement')
        self.school_address = QLineEdit(); self.school_address.setStyleSheet(FIELD)
        self.school_address.setPlaceholderText('Adresse complète')
        self.school_phone   = QLineEdit(); self.school_phone.setStyleSheet(FIELD)
        self.school_phone.setPlaceholderText('0522 000 000')
        self.school_email   = QLineEdit(); self.school_email.setStyleSheet(FIELD)
        self.school_email.setPlaceholderText('contact@ecole.ma')
        self.school_city    = QLineEdit(); self.school_city.setStyleSheet(FIELD)
        self.school_city.setPlaceholderText('Casablanca')
        self.school_director = QLineEdit(); self.school_director.setStyleSheet(FIELD)
        self.school_director.setPlaceholderText('Nom du directeur')

        for widget in (self.school_name, self.school_address, self.school_phone,
                       self.school_email, self.school_city, self.school_director):
            widget.textChanged.connect(self._mark_dirty)

        for label, widget, hint_text in [
            ('Nom de l\'école :',      self.school_name,    'Affiché sur les reçus et bulletins'),
            ('Adresse :',              self.school_address,  ''),
            ('Téléphone :',            self.school_phone,    ''),
            ('Email :',                self.school_email,    ''),
            ('Ville :',                self.school_city,     ''),
            ('Directeur :',            self.school_director, 'Affiché sur les bulletins de paie'),
        ]:
            col = QVBoxLayout(); col.setSpacing(3)
            col.addWidget(widget)
            if hint_text:
                col.addWidget(_hint(hint_text))
            w = QWidget(); w.setLayout(col); w.setStyleSheet('background:transparent;')
            info_form.addRow(_flbl(label), w)
        info_layout.addLayout(info_form)
        layout.addWidget(info_card)

        # ── 3. DEFAULT FEES ───────────────────────────────────────────────────
        fees_card, fees_layout = _card('Tarifs par Défaut', '💰')
        fees_form = QFormLayout(); fees_form.setSpacing(12)
        fees_form.setLabelAlignment(Qt.AlignRight)

        def _spin(max_val=99999, suffix=' MAD', decimals=2, step=100):
            s = QDoubleSpinBox()
            s.setRange(0, max_val); s.setSuffix(suffix)
            s.setDecimals(decimals); s.setSingleStep(step)
            s.setStyleSheet(FIELD)
            s.valueChanged.connect(self._mark_dirty)
            return s

        self.default_monthly_fee = _spin()
        self.default_transport_fee = _spin()
        self.default_insurance_fee = _spin()

        for label, widget, hint_text in [
            ('Mensualité par défaut :',     self.default_monthly_fee,
             'Montant pré-rempli à l\'ajout d\'un élève'),
            ('Transport mensuel défaut :',  self.default_transport_fee,
             'Montant pré-rempli pour les abonnés transport'),
            ('Assurance annuelle défaut :', self.default_insurance_fee,
             'Montant d\'assurance par défaut (annuel, par élève)'),
        ]:
            col = QVBoxLayout(); col.setSpacing(3)
            col.addWidget(widget); col.addWidget(_hint(hint_text))
            w = QWidget(); w.setLayout(col); w.setStyleSheet('background:transparent;')
            fees_form.addRow(_flbl(label), w)
        fees_layout.addLayout(fees_form)
        layout.addWidget(fees_card)

        # ── 4. RECEIPT SETTINGS ───────────────────────────────────────────────
        rec_card, rec_layout = _card('Paramètres des Reçus', '🧾')
        rec_form = QFormLayout(); rec_form.setSpacing(12)
        rec_form.setLabelAlignment(Qt.AlignRight)
        rec_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.receipt_prefix = QLineEdit(); self.receipt_prefix.setStyleSheet(FIELD)
        self.receipt_prefix.setPlaceholderText('REC')
        self.receipt_footer = QLineEdit(); self.receipt_footer.setStyleSheet(FIELD)
        self.receipt_footer.setPlaceholderText('Merci de votre confiance.')

        for widget in (self.receipt_prefix, self.receipt_footer):
            widget.textChanged.connect(self._mark_dirty)

        for label, widget, hint_text in [
            ('Préfixe N° reçu :',  self.receipt_prefix,  'ex: REC → REC-000001'),
            ('Pied de page reçu :', self.receipt_footer,  'Texte bas de page sur chaque reçu PDF'),
        ]:
            col = QVBoxLayout(); col.setSpacing(3)
            col.addWidget(widget); col.addWidget(_hint(hint_text))
            w = QWidget(); w.setLayout(col); w.setStyleSheet('background:transparent;')
            rec_form.addRow(_flbl(label), w)
        rec_layout.addLayout(rec_form)
        layout.addWidget(rec_card)

        # ── 5. USER ACCOUNTS INFO ─────────────────────────────────────────────
        cred_card = QFrame()
        cred_card.setStyleSheet(
            f'QFrame {{ background:{PRIMARY_LIGHT}; border:1px solid #C7D2FE; border-radius:14px; }}'
        )
        ccl = QVBoxLayout(cred_card); ccl.setContentsMargins(24, 18, 24, 18); ccl.setSpacing(10)
        ct = QLabel('🔐  Comptes utilisateurs')
        ct.setStyleSheet(f'color:{PRIMARY}; font-size:13px; font-weight:700; background:transparent;')
        ccl.addWidget(ct)
        for user, role, pwd in [
            ('admin',      'Administrateur', 'admin123'),
            ('comptable',  'Comptable',      'compta123'),
            ('secretaire', 'Secrétaire',     'secr123'),
        ]:
            row = QHBoxLayout()
            ul = QLabel(f'<b>{user}</b>')
            ul.setStyleSheet(f'color:{TEXT_MAIN}; font-size:12px; background:transparent; min-width:100px;')
            rl = QLabel(role)
            rl.setStyleSheet(f'color:{TEXT_SUB}; font-size:12px; background:transparent; min-width:120px;')
            pl = QLabel(f'Mot de passe: <code>{pwd}</code>')
            pl.setStyleSheet('color:#6D28D9; font-size:12px; background:transparent;')
            row.addWidget(ul); row.addWidget(rl); row.addWidget(pl); row.addStretch()
            w = QWidget(); w.setLayout(row); w.setStyleSheet('background:transparent;')
            ccl.addWidget(w)
        layout.addWidget(cred_card)

        # ── Save button row ───────────────────────────────────────────────────
        save_row = QHBoxLayout()

        # Unsaved changes indicator
        self.dirty_lbl = QLabel('● Modifications non enregistrées')
        self.dirty_lbl.setStyleSheet(
            f'color:{WARNING}; font-size:12px; font-weight:600; background:transparent;'
        )
        self.dirty_lbl.setVisible(False)

        reset_btn = QPushButton('↺  Recharger')
        reset_btn.setFixedHeight(46)
        reset_btn.setStyleSheet(BTN_SEC)
        reset_btn.clicked.connect(self._load_settings)

        save_btn = QPushButton('💾  Enregistrer les paramètres')
        save_btn.setFixedHeight(46)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(BTN)
        save_btn.clicked.connect(self._save_settings)

        save_row.addWidget(self.dirty_lbl)
        save_row.addStretch()
        save_row.addWidget(reset_btn)
        save_row.addWidget(save_btn)
        layout.addLayout(save_row)

        # Version footer
        ver = QLabel('SGS v4.0  ·  Système de Gestion Scolaire  ·  © 2025 — Tous droits réservés')
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet('color:#D1D5DB; font-size:11px; background:transparent;')
        layout.addWidget(ver)
        layout.addStretch()

        scroll.setWidget(container)
        ol = QVBoxLayout(self); ol.setContentsMargins(0, 0, 0, 0); ol.addWidget(scroll)

    # ── Load / Save ───────────────────────────────────────────────────────────
    def _load_settings(self):
        """Load all settings from DB. Safe defaults used if key missing."""
        def get(key, default=''):
            return get_setting(self.session, key, default)

        # School year
        saved_yr = get('school_year', '2024-25')
        idx = self.school_year.findText(saved_yr)
        self.school_year.blockSignals(True)
        if idx >= 0:
            self.school_year.setCurrentIndex(idx)
        else:
            # Year not in list — add it
            self.school_year.addItem(saved_yr)
            self.school_year.setCurrentText(saved_yr)
        self.school_year.blockSignals(False)

        # School info
        self.school_name.setText(get('school_name', 'Le Schéma'))
        self.school_address.setText(get('school_address', ''))
        self.school_phone.setText(get('school_phone', ''))
        self.school_email.setText(get('school_email', ''))
        self.school_city.setText(get('school_city', ''))
        self.school_director.setText(get('school_director', ''))

        # Fees
        try: self.default_monthly_fee.setValue(float(get('default_monthly_fee', '0')))
        except: self.default_monthly_fee.setValue(0)
        try: self.default_transport_fee.setValue(float(get('default_transport_fee', '300')))
        except: self.default_transport_fee.setValue(300)
        try: self.default_insurance_fee.setValue(float(get('default_insurance_fee', '500')))
        except: self.default_insurance_fee.setValue(500)

        # Backward compat with old keys
        if self.default_transport_fee.value() == 0:
            try: self.default_transport_fee.setValue(float(get('transport_fee', '300')))
            except: pass
        if self.default_insurance_fee.value() == 0:
            try: self.default_insurance_fee.setValue(float(get('insurance_fee', '500')))
            except: pass

        # Receipt
        self.receipt_prefix.setText(get('receipt_prefix', 'REC'))
        self.receipt_footer.setText(
            get('receipt_footer', 'Merci de votre confiance — Le Schéma.')
        )

        self._dirty = False
        self.dirty_lbl.setVisible(False)

    def _save_settings(self):
        """Persist all settings to DB with a single commit."""
        try:
            new_year = self.school_year.currentText()
            old_year = get_setting(self.session, 'school_year', '')
            year_changed = (old_year != new_year and old_year != '')

            # All key/value pairs to save
            settings_map = {
                'school_year':          new_year,
                'school_name':          self.school_name.text().strip(),
                'school_address':       self.school_address.text().strip(),
                'school_phone':         self.school_phone.text().strip(),
                'school_email':         self.school_email.text().strip(),
                'school_city':          self.school_city.text().strip(),
                'school_director':      self.school_director.text().strip(),
                'default_monthly_fee':  str(self.default_monthly_fee.value()),
                'default_transport_fee':str(self.default_transport_fee.value()),
                'default_insurance_fee':str(self.default_insurance_fee.value()),
                # Backward compat aliases
                'insurance_fee':        str(self.default_insurance_fee.value()),
                'transport_fee':        str(self.default_transport_fee.value()),
                'receipt_prefix':       self.receipt_prefix.text().strip() or 'REC',
                'receipt_footer':       self.receipt_footer.text().strip(),
            }

            for key, value in settings_map.items():
                s = self.session.query(Setting).filter_by(key=key).first()
                if s:
                    s.value = value
                else:
                    self.session.add(Setting(key=key, value=value))

            self.session.commit()
            self._dirty = False
            self.dirty_lbl.setVisible(False)

            # Success feedback
            if year_changed:
                QMessageBox.warning(
                    self, '⚠️  Année scolaire modifiée',
                    f'L\'année scolaire a été changée de «{old_year}» à «{new_year}».\n\n'
                    f'Tous les paiements, assurances et mensualités seront désormais '
                    f'scopés sur l\'année «{new_year}».\n\n'
                    f'Redémarrez l\'application pour que les changements soient pleinement '
                    f'appliqués dans tous les modules.'
                )
            else:
                msg = QMessageBox(self)
                msg.setWindowTitle('✅  Paramètres sauvegardés')
                msg.setText(
                    f'<b>Paramètres enregistrés avec succès !</b><br><br>'
                    f'<span style="color:#6B7280; font-size:12px;">'
                    f'Année scolaire : <b>{new_year}</b><br>'
                    f'École : <b>{self.school_name.text()}</b></span>'
                )
                msg.setStyleSheet(
                    f'QMessageBox {{ background:white; }}'
                    f'QLabel {{ color:{TEXT_MAIN}; font-size:13px; }}'
                )
                msg.exec()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Erreur', f'Impossible de sauvegarder :\n{str(e)}')

    def _mark_dirty(self):
        self._dirty = True
        self.dirty_lbl.setVisible(True)
