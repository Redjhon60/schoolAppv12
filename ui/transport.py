import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QMessageBox, QSpinBox, QHeaderView, QAbstractItemView, QTabWidget, QFrame)
from PySide6.QtCore import Qt
from models.database import Bus, Employee, Student
from themes.style import (DIALOG_CSS, TABLE_CSS, PRIMARY, PRIMARY_LIGHT, INFO, INFO_LIGHT,
    SUCCESS, SUCCESS_LIGHT, BORDER, TEXT_MAIN, TEXT_SUB)

BTN     = f'QPushButton {{ background: {PRIMARY}; color: white; border: none; border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px; }} QPushButton:hover {{ background: #4338CA; }}'
BTN_SEC = 'QPushButton { background: #F3F4F6; color: #374151; border: 1px solid #E5E7EB; border-radius: 8px; padding: 9px 20px; font-weight: 500; font-size: 13px; } QPushButton:hover { background: #E5E7EB; }'
BTN_DANGER = 'QPushButton { background: #FEE2E2; color: #DC2626; border: 1px solid #FECACA; border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px; } QPushButton:hover { background: #FECACA; }'
TAB_CSS = f"QTabWidget::pane {{ border: none; background: transparent; }} QTabBar::tab {{ background: transparent; color: {TEXT_SUB}; border: none; border-bottom: 2px solid transparent; padding: 10px 24px; font-size: 13px; font-weight: 500; margin-right: 4px; }} QTabBar::tab:selected {{ color: {PRIMARY}; border-bottom: 2px solid {PRIMARY}; font-weight: 700; }} QTabBar::tab:hover:!selected {{ color: {TEXT_MAIN}; background: #F9FAFB; border-radius: 8px 8px 0 0; }}"

def flbl(t):
    l = QLabel(t); l.setStyleSheet('color: #374151; font-size: 12px; font-weight: 600; background: transparent;')
    return l


class BusDialog(QDialog):
    def __init__(self, parent=None, bus=None, session=None):
        super().__init__(parent)
        self.bus = bus; self.session = session
        self.setWindowTitle('Modifier bus' if bus else 'Nouveau bus')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 540, 420)
        self.setStyleSheet(DIALOG_CSS + 'QDialog { background: #F7F8FC; }')
        self._setup_ui()
        if bus: self._populate(bus)

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        hdr = QFrame(); hdr.setStyleSheet(f'QFrame {{ background: #3B82F6; }}'); hdr.setFixedHeight(58)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        ht = QLabel('🚌  ' + ('Modifier bus' if self.bus else 'Ajouter un bus'))
        ht.setStyleSheet('color: white; font-size: 15px; font-weight: 700; background: transparent;')
        hl.addWidget(ht); outer.addWidget(hdr)

        content = QWidget(); content.setStyleSheet('background: transparent;')
        cl = QVBoxLayout(content); cl.setContentsMargins(28,22,28,16); cl.setSpacing(0)
        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)

        self.name = QLineEdit(); self.name.setPlaceholderText('Ex: Bus 1, Navette Centre...')
        self.plate = QLineEdit(); self.plate.setPlaceholderText('Ex: 12345 A 6')
        self.capacity = QSpinBox(); self.capacity.setRange(1, 100); self.capacity.setValue(30)
        self.driver_combo = QComboBox()
        self.driver_combo.addItem('— Aucun chauffeur —', None)
        if self.session:
            for d in self.session.query(Employee).filter_by(role='driver', active=True).all():
                self.driver_combo.addItem(f'{d.first_name} {d.last_name}', d.id)
        self.route = QTextEdit(); self.route.setMaximumHeight(60)
        self.route.setPlaceholderText('Décrire la route et les arrêts...')

        form.addRow(flbl('Nom du bus:'),      self.name)
        form.addRow(flbl('Immatriculation:'), self.plate)
        form.addRow(flbl('Capacité (places):'), self.capacity)
        form.addRow(flbl('Chauffeur:'),       self.driver_combo)
        form.addRow(flbl('Route / Arrêts:'),  self.route)
        cl.addLayout(form); outer.addWidget(content, 1)

        footer = QFrame(); footer.setStyleSheet(f'QFrame {{ background: white; border-top: 1px solid {BORDER}; }}'); footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24,0,24,0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        save   = QPushButton('💾  Enregistrer'); save.setStyleSheet(BTN); save.clicked.connect(self.accept)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(save)
        outer.addWidget(footer)

    def _populate(self, b):
        self.name.setText(b.name or ''); self.plate.setText(b.plate or '')
        self.capacity.setValue(b.capacity or 30); self.route.setText(b.route or '')
        if b.driver_id:
            idx = self.driver_combo.findData(b.driver_id)
            if idx >= 0: self.driver_combo.setCurrentIndex(idx)

    def get_data(self):
        return {'name': self.name.text().strip(), 'plate': self.plate.text().strip(),
                'capacity': self.capacity.value(), 'driver_id': self.driver_combo.currentData(),
                'route': self.route.toPlainText()}


def _info_card(icon, title, value, accent, light):
    card = QFrame()
    card.setStyleSheet(f'QFrame {{ background: {light}; border: 1px solid {accent}33; border-radius: 12px; border-left: 4px solid {accent}; }}')
    card.setFixedHeight(80)
    cl = QHBoxLayout(card); cl.setContentsMargins(16,12,16,12); cl.setSpacing(12)
    pill = QLabel(icon); pill.setFixedSize(36,36); pill.setAlignment(Qt.AlignCenter)
    pill.setStyleSheet(f'background: white; border-radius: 10px; font-size: 18px;')
    txt = QVBoxLayout(); txt.setSpacing(2)
    val = QLabel(str(value)); val.setStyleSheet(f'color: {accent}; font-size: 20px; font-weight: 800; background: transparent;')
    lbl = QLabel(title); lbl.setStyleSheet(f'color: {TEXT_SUB}; font-size: 11px; font-weight: 500; background: transparent;')
    txt.addWidget(val); txt.addWidget(lbl)
    cl.addWidget(pill); cl.addLayout(txt)
    card._val = val
    return card


class TransportWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setStyleSheet('background: transparent;')
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(28,24,28,24); layout.setSpacing(16)

        tabs = QTabWidget(); tabs.setStyleSheet(TAB_CSS)

        # ── Bus tab ──────────────────────────────────────────────────
        bus_tab = QWidget(); bus_tab.setStyleSheet('background: transparent;')
        bl = QVBoxLayout(bus_tab); bl.setContentsMargins(0,16,0,0); bl.setSpacing(14)

        bus_tb = QHBoxLayout(); bus_tb.setSpacing(10)
        bus_title = QLabel('Flotte de bus'); bus_title.setStyleSheet(f'color: {TEXT_MAIN}; font-size: 15px; font-weight: 700; background: transparent;')
        add_bus = QPushButton('＋  Ajouter un bus'); add_bus.setFixedHeight(40)
        add_bus.setCursor(Qt.PointingHandCursor); add_bus.setStyleSheet(BTN)
        add_bus.clicked.connect(self._add_bus)
        bus_tb.addWidget(bus_title); bus_tb.addStretch(); bus_tb.addWidget(add_bus)
        bl.addLayout(bus_tb)

        # Info cards
        self.bus_info_row = QHBoxLayout(); self.bus_info_row.setSpacing(12)
        self.c_buses    = _info_card('🚌', 'Bus actifs',            0, '#3B82F6', '#DBEAFE')
        self.c_capacity = _info_card('💺', 'Capacité totale',       0, PRIMARY,   PRIMARY_LIGHT)
        self.c_subs     = _info_card('👥', 'Abonnés transport',     0, SUCCESS,   SUCCESS_LIGHT)
        for c in [self.c_buses, self.c_capacity, self.c_subs]:
            self.bus_info_row.addWidget(c)
        bl.addLayout(self.bus_info_row)

        btcard = QFrame(); btcard.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 14px; }}')
        btcl = QVBoxLayout(btcard); btcl.setContentsMargins(0,0,0,0)
        self.bus_table = QTableWidget(); self.bus_table.setColumnCount(5)
        self.bus_table.setHorizontalHeaderLabels(['Nom du bus', 'Immatriculation', 'Capacité', 'Chauffeur', 'Route'])
        self.bus_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bus_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bus_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.bus_table.setAlternatingRowColors(True)
        self.bus_table.verticalHeader().setVisible(False)
        self.bus_table.setShowGrid(False)
        self.bus_table.setStyleSheet(TABLE_CSS)
        btcl.addWidget(self.bus_table)
        bl.addWidget(btcard, 1)

        bus_ab = QHBoxLayout(); bus_ab.setSpacing(8)
        edit_bus = QPushButton('✏️  Modifier'); edit_bus.setStyleSheet(BTN_SEC); edit_bus.clicked.connect(self._edit_bus)
        del_bus  = QPushButton('🗑️  Supprimer'); del_bus.setStyleSheet(BTN_DANGER); del_bus.clicked.connect(self._delete_bus)
        bus_ab.addStretch(); bus_ab.addWidget(edit_bus); bus_ab.addWidget(del_bus)
        bl.addLayout(bus_ab)

        # ── Subscribers tab ──────────────────────────────────────────
        sub_tab = QWidget(); sub_tab.setStyleSheet('background: transparent;')
        sl = QVBoxLayout(sub_tab); sl.setContentsMargins(0,16,0,0); sl.setSpacing(14)

        sub_title = QLabel('Élèves abonnés au transport')
        sub_title.setStyleSheet(f'color: {TEXT_MAIN}; font-size: 15px; font-weight: 700; background: transparent;')
        sl.addWidget(sub_title)

        stcard = QFrame(); stcard.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 14px; }}')
        stcl = QVBoxLayout(stcard); stcl.setContentsMargins(0,0,0,0)
        self.sub_table = QTableWidget(); self.sub_table.setColumnCount(5)
        self.sub_table.setHorizontalHeaderLabels(['Code élève', 'Nom complet', 'Classe', 'Parent / Tuteur', 'Téléphone'])
        self.sub_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sub_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sub_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sub_table.setAlternatingRowColors(True)
        self.sub_table.verticalHeader().setVisible(False)
        self.sub_table.setShowGrid(False)
        self.sub_table.setStyleSheet(TABLE_CSS)
        stcl.addWidget(self.sub_table)
        sl.addWidget(stcard, 1)

        self.sub_count_lbl = QLabel()
        self.sub_count_lbl.setStyleSheet(f'color: #9CA3AF; font-size: 12px; background: transparent;')
        sl.addWidget(self.sub_count_lbl)

        tabs.addTab(bus_tab, '🚌  Gestion des Bus')
        tabs.addTab(sub_tab, '👥  Abonnés Transport')
        layout.addWidget(tabs)

    def _load_data(self):
        self._load_buses()
        self._load_subscribers()

    def _load_buses(self):
        self.all_buses = self.session.query(Bus).filter_by(active=True).all()
        self.bus_table.setRowCount(len(self.all_buses))
        total_cap = 0
        for row, b in enumerate(self.all_buses):
            driver = self.session.query(Employee).filter_by(id=b.driver_id).first() if b.driver_id else None
            driver_name = f'{driver.first_name} {driver.last_name}' if driver else '—'
            self.bus_table.setItem(row, 0, QTableWidgetItem(b.name or ''))
            self.bus_table.setItem(row, 1, QTableWidgetItem(b.plate or ''))
            self.bus_table.setItem(row, 2, QTableWidgetItem(str(b.capacity or 0)))
            self.bus_table.setItem(row, 3, QTableWidgetItem(driver_name))
            self.bus_table.setItem(row, 4, QTableWidgetItem(b.route or ''))
            self.bus_table.setRowHeight(row, 44)
            total_cap += b.capacity or 0
        self.c_buses._val.setText(str(len(self.all_buses)))
        self.c_capacity._val.setText(str(total_cap))

    def _load_subscribers(self):
        students = self.session.query(Student).filter_by(active=True, transport=True).all()
        self.sub_table.setRowCount(len(students))
        for row, s in enumerate(students):
            self.sub_table.setItem(row, 0, QTableWidgetItem(s.code or ''))
            self.sub_table.setItem(row, 1, QTableWidgetItem(f'{s.first_name} {s.last_name}'))
            self.sub_table.setItem(row, 2, QTableWidgetItem(s.class_name or ''))
            self.sub_table.setItem(row, 3, QTableWidgetItem(s.parent_name or ''))
            self.sub_table.setItem(row, 4, QTableWidgetItem(s.parent_phone or ''))
            self.sub_table.setRowHeight(row, 44)
        self.c_subs._val.setText(str(len(students)))
        self.sub_count_lbl.setText(f'{len(students)} élèves abonnés au transport scolaire')

    def _add_bus(self):
        dlg = BusDialog(self, session=self.session)
        if dlg.exec():
            self.session.add(Bus(**dlg.get_data())); self.session.commit(); self._load_buses()

    def _edit_bus(self):
        row = self.bus_table.currentRow()
        if row < 0: QMessageBox.information(self, 'Sélection', 'Sélectionnez un bus.'); return
        b = self.all_buses[row]
        dlg = BusDialog(self, b, self.session)
        if dlg.exec():
            for k, v in dlg.get_data().items(): setattr(b, k, v)
            self.session.commit(); self._load_buses()

    def _delete_bus(self):
        row = self.bus_table.currentRow()
        if row < 0: return
        b = self.all_buses[row]
        if QMessageBox.question(self, 'Confirmation', f'Supprimer le bus « {b.name} » ?',
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            b.active = False; self.session.commit(); self._load_buses()
