import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QAbstractItemView, QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from models.database import Schedule, Employee
from themes.style import (CLASSES, DIALOG_CSS, TABLE_CSS, PRIMARY, PRIMARY_LIGHT,
    BORDER, TEXT_MAIN, TEXT_SUB)

BTN     = f'QPushButton {{ background: {PRIMARY}; color: white; border: none; border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px; }} QPushButton:hover {{ background: #4338CA; }}'
BTN_SEC = 'QPushButton { background: #F3F4F6; color: #374151; border: 1px solid #E5E7EB; border-radius: 8px; padding: 9px 20px; font-weight: 500; font-size: 13px; } QPushButton:hover { background: #E5E7EB; }'
BTN_DANGER = 'QPushButton { background: #FEE2E2; color: #DC2626; border: 1px solid #FECACA; border-radius: 8px; padding: 9px 18px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: #FECACA; }'

DAYS  = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
SLOTS = ['08:00','09:00','10:00','11:00','12:00','14:00','15:00','16:00','17:00']
SLOT_LABELS = [f'{SLOTS[i]}–{SLOTS[i+1]}' for i in range(len(SLOTS)-1)]

# Soft pastel palette for subjects
SUBJECT_PALETTE = [
    ('#EEF2FF', '#4F46E5'), ('#D1FAE5', '#059669'), ('#FEF3C7', '#B45309'),
    ('#FEE2E2', '#DC2626'), ('#EDE9FE', '#6D28D9'), ('#CCFBF1', '#0D9488'),
    ('#FCE7F3', '#BE185D'), ('#DBEAFE', '#1D4ED8'), ('#F3F4F6', '#374151'),
]

def flbl(t):
    l = QLabel(t); l.setStyleSheet('color: #374151; font-size: 12px; font-weight: 600; background: transparent;')
    return l


class ScheduleDialog(QDialog):
    def __init__(self, parent=None, schedule=None, session=None):
        super().__init__(parent)
        self.session = session; self.schedule = schedule
        self.setWindowTitle('Modifier cours' if schedule else 'Ajouter un cours')
        from ui.main_window import responsive_dialog; responsive_dialog(self, 540, 440)
        self.setStyleSheet(DIALOG_CSS + 'QDialog { background: #F7F8FC; }')
        self._setup_ui()
        if schedule: self._populate(schedule)

    def _setup_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        hdr = QFrame(); hdr.setStyleSheet(f'QFrame {{ background: {PRIMARY}; }}'); hdr.setFixedHeight(58)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)
        ht = QLabel('📅  ' + ('Modifier cours' if self.schedule else 'Ajouter un cours'))
        ht.setStyleSheet('color: white; font-size: 15px; font-weight: 700; background: transparent;')
        hl.addWidget(ht); outer.addWidget(hdr)

        content = QWidget(); content.setStyleSheet('background: transparent;')
        cl = QVBoxLayout(content); cl.setContentsMargins(28,22,28,16)
        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)

        self.class_combo = QComboBox(); self.class_combo.addItems(CLASSES)
        self.day_combo   = QComboBox(); self.day_combo.addItems(DAYS)
        self.time_start  = QComboBox(); self.time_start.addItems(SLOTS[:-1])
        self.time_end    = QComboBox(); self.time_end.addItems(SLOTS[1:])
        self.time_end.setCurrentIndex(1)
        self.subject     = QLineEdit(); self.subject.setPlaceholderText('Ex: Mathématiques, Français, SVT...')
        self.teacher_combo = QComboBox(); self.teacher_combo.addItem('— Aucun enseignant —', None)
        if self.session:
            for t in self.session.query(Employee).filter_by(role='teacher', active=True).all():
                self.teacher_combo.addItem(f'{t.first_name} {t.last_name}', t.id)
        self.room = QLineEdit(); self.room.setPlaceholderText('Ex: Salle A12, Laboratoire...')

        form.addRow(flbl('Classe:'),      self.class_combo)
        form.addRow(flbl('Jour:'),        self.day_combo)
        form.addRow(flbl('Heure début:'), self.time_start)
        form.addRow(flbl('Heure fin:'),   self.time_end)
        form.addRow(flbl('Matière:'),     self.subject)
        form.addRow(flbl('Enseignant:'),  self.teacher_combo)
        form.addRow(flbl('Salle:'),       self.room)
        cl.addLayout(form); outer.addWidget(content, 1)

        footer = QFrame(); footer.setStyleSheet(f'QFrame {{ background: white; border-top: 1px solid {BORDER}; }}'); footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(24,0,24,0); fl.setSpacing(10)
        cancel = QPushButton('Annuler'); cancel.setStyleSheet(BTN_SEC); cancel.clicked.connect(self.reject)
        save   = QPushButton('💾  Enregistrer'); save.setStyleSheet(BTN); save.clicked.connect(self.accept)
        fl.addStretch(); fl.addWidget(cancel); fl.addWidget(save)
        outer.addWidget(footer)

    def _populate(self, s):
        self.class_combo.setCurrentText(s.class_name or '')
        self.day_combo.setCurrentText(s.day or '')
        if s.time_start: self.time_start.setCurrentText(s.time_start)
        if s.time_end:   self.time_end.setCurrentText(s.time_end)
        self.subject.setText(s.subject or '')
        if s.teacher_id:
            idx = self.teacher_combo.findData(s.teacher_id)
            if idx >= 0: self.teacher_combo.setCurrentIndex(idx)
        self.room.setText(s.room or '')

    def get_data(self):
        return {'class_name': self.class_combo.currentText(), 'day': self.day_combo.currentText(),
                'time_start': self.time_start.currentText(), 'time_end': self.time_end.currentText(),
                'subject': self.subject.text().strip(), 'teacher_id': self.teacher_combo.currentData(),
                'room': self.room.text().strip()}


class TimetableWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setStyleSheet('background: transparent;')
        self._setup_ui()
        self._load_timetable()

    def _setup_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(28,24,28,24); layout.setSpacing(16)

        # Toolbar
        tb = QHBoxLayout(); tb.setSpacing(12)
        self.class_filter = QComboBox(); self.class_filter.addItems(CLASSES)
        self.class_filter.setFixedHeight(40)
        self.class_filter.setStyleSheet(f'QComboBox {{ background: white; border: 1.5px solid {BORDER}; border-radius: 10px; color: {TEXT_MAIN}; padding: 0 14px; font-size: 14px; font-weight: 600; min-width: 120px; }} QComboBox QAbstractItemView {{ background-color: white; border: 1.5px solid #C7D2FE; border-radius: 10px; color: #1A1D2E; padding: 4px; outline: none; }} QComboBox QAbstractItemView::item {{ background-color: transparent; color: #1A1D2E; padding: 9px 14px; min-height: 30px; border-radius: 6px; margin: 1px 4px; }} QComboBox QAbstractItemView::item:hover {{ background-color: #F5F3FF; color: #4F46E5; }} QComboBox QAbstractItemView::item:selected {{ background-color: #EEF2FF; color: #4F46E5; font-weight: 600; }}')
        self.class_filter.currentTextChanged.connect(self._load_timetable)

        add_btn = QPushButton('＋  Ajouter un cours')
        add_btn.setFixedHeight(40); add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(BTN); add_btn.clicked.connect(self._add_schedule)

        class_lbl = QLabel('Classe :')
        class_lbl.setStyleSheet(f'color: {TEXT_SUB}; font-size: 13px; background: transparent;')
        tb.addWidget(class_lbl); tb.addWidget(self.class_filter); tb.addStretch(); tb.addWidget(add_btn)
        layout.addLayout(tb)

        # Grid card
        grid_card = QFrame()
        grid_card.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 14px; }}')
        gcl = QVBoxLayout(grid_card); gcl.setContentsMargins(0,0,0,0)

        self.grid = QTableWidget()
        self.grid.setRowCount(len(SLOT_LABELS))
        self.grid.setColumnCount(len(DAYS))
        self.grid.setHorizontalHeaderLabels(DAYS)
        self.grid.setVerticalHeaderLabels(SLOT_LABELS)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.grid.verticalHeader().setDefaultSectionSize(64)
        self.grid.verticalHeader().setStyleSheet(f'''
            QHeaderView::section {{
                background: #F9FAFB; color: #6B7280; padding: 8px;
                font-size: 10px; font-weight: 600;
                border: none; border-bottom: 1px solid {BORDER};
                border-right: 1px solid {BORDER};
                min-width: 90px;
            }}
        ''')
        self.grid.horizontalHeader().setStyleSheet(f'''
            QHeaderView::section {{
                background: #F9FAFB; color: #374151; padding: 10px;
                font-size: 12px; font-weight: 700;
                border: none; border-bottom: 2px solid {BORDER};
                border-right: 1px solid {BORDER};
                letter-spacing: 0.3px;
            }}
        ''')
        self.grid.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.grid.setSelectionMode(QAbstractItemView.NoSelection)
        self.grid.setStyleSheet(f'''
            QTableWidget {{ background: white; border: none; gridline-color: {BORDER}; outline: none; }}
            QTableWidget::item {{ padding: 4px; border-bottom: 1px solid {BORDER}; border-right: 1px solid {BORDER}; }}
        ''')
        self.grid.setShowGrid(True)
        gcl.addWidget(self.grid)
        layout.addWidget(grid_card, 2)

        # List
        list_hdr = QHBoxLayout()
        list_lbl = QLabel('Détail des cours')
        list_lbl.setStyleSheet(f'color: {TEXT_MAIN}; font-size: 14px; font-weight: 700; background: transparent;')
        del_btn = QPushButton('🗑️  Supprimer le cours sélectionné')
        del_btn.setStyleSheet(BTN_DANGER); del_btn.clicked.connect(self._delete_schedule)
        list_hdr.addWidget(list_lbl); list_hdr.addStretch(); list_hdr.addWidget(del_btn)
        layout.addLayout(list_hdr)

        lcard = QFrame(); lcard.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {BORDER}; border-radius: 12px; }}')
        lcl = QVBoxLayout(lcard); lcl.setContentsMargins(0,0,0,0)
        self.list_table = QTableWidget(); self.list_table.setColumnCount(6)
        self.list_table.setHorizontalHeaderLabels(['Jour','Horaire','Matière','Enseignant','Salle','Classe'])
        self.list_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.list_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.list_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_table.setAlternatingRowColors(True)
        self.list_table.verticalHeader().setVisible(False)
        self.list_table.setShowGrid(False)
        self.list_table.setMaximumHeight(200)
        self.list_table.setStyleSheet(TABLE_CSS)
        lcl.addWidget(self.list_table)
        layout.addWidget(lcard)
        self.all_schedules = []

    def _load_timetable(self, class_name=None):
        class_name = class_name or self.class_filter.currentText()
        self.all_schedules = self.session.query(Schedule).filter_by(class_name=class_name).all()

        # Clear grid
        for r in range(len(SLOT_LABELS)):
            for c in range(len(DAYS)):
                item = QTableWidgetItem('')
                item.setBackground(QColor('#FAFBFD'))
                self.grid.setItem(r, c, item)

        color_map = {}
        pal_idx = 0

        for s in self.all_schedules:
            if s.day not in DAYS or not s.time_start: continue
            col = DAYS.index(s.day)
            for ridx, slot in enumerate(SLOT_LABELS):
                if slot.startswith(s.time_start):
                    subj = s.subject or ''
                    if subj not in color_map:
                        color_map[subj] = SUBJECT_PALETTE[pal_idx % len(SUBJECT_PALETTE)]
                        pal_idx += 1
                    bg, fg = color_map[subj]
                    teacher = self.session.query(Employee).filter_by(id=s.teacher_id).first() if s.teacher_id else None
                    t_name = f'{teacher.first_name} {teacher.last_name}' if teacher else ''
                    text = subj + (f'\n👤 {t_name}' if t_name else '') + (f'\n📍 {s.room}' if s.room else '')
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QColor(bg))
                    item.setForeground(QColor(fg))
                    f = QFont(); f.setPointSize(9); f.setBold(True)
                    item.setFont(f)
                    self.grid.setItem(ridx, col, item)
                    break

        # List
        self.list_table.setRowCount(len(self.all_schedules))
        for row, s in enumerate(self.all_schedules):
            teacher = self.session.query(Employee).filter_by(id=s.teacher_id).first() if s.teacher_id else None
            t_name = f'{teacher.first_name} {teacher.last_name}' if teacher else '—'
            self.list_table.setItem(row, 0, QTableWidgetItem(s.day or ''))
            self.list_table.setItem(row, 1, QTableWidgetItem(f'{s.time_start} – {s.time_end}'))
            self.list_table.setItem(row, 2, QTableWidgetItem(s.subject or ''))
            self.list_table.setItem(row, 3, QTableWidgetItem(t_name))
            self.list_table.setItem(row, 4, QTableWidgetItem(s.room or ''))
            self.list_table.setItem(row, 5, QTableWidgetItem(s.class_name or ''))
            self.list_table.setRowHeight(row, 40)

    def _add_schedule(self):
        dlg = ScheduleDialog(self, session=self.session)
        if dlg.exec():
            self.session.add(Schedule(**dlg.get_data())); self.session.commit(); self._load_timetable()

    def _delete_schedule(self):
        row = self.list_table.currentRow()
        if row < 0: QMessageBox.information(self, 'Sélection', 'Sélectionnez un cours.'); return
        s = self.all_schedules[row]
        if QMessageBox.question(self, 'Confirmation', f'Supprimer le cours « {s.subject} » ?',
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.session.delete(s); self.session.commit(); self._load_timetable()
