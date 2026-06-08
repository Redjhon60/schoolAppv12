"""
Import Center — unified UI for importing Excel data into any module.
Accessible from the main window sidebar.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog, QMessageBox, QScrollArea, QComboBox, QProgressBar,
    QTextEdit, QDialog, QGridLayout, QSizePolicy, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont

from themes.style import (PRIMARY, PRIMARY_LIGHT, SUCCESS, SUCCESS_LIGHT,
    DANGER, DANGER_LIGHT, WARNING, WARNING_LIGHT, INFO, INFO_LIGHT,
    PURPLE, PURPLE_LIGHT, TEAL, TEAL_LIGHT, BORDER, TEXT_MAIN, TEXT_SUB,
    BG_CARD, NAN_COLOR, NAN_TEXT)

BTN     = f'QPushButton {{ background:{PRIMARY}; color:white; border:none; border-radius:8px; padding:9px 20px; font-weight:600; font-size:13px; }} QPushButton:hover {{ background:#4338CA; }}'
BTN_SEC = 'QPushButton { background:#F3F4F6; color:#374151; border:1px solid #E5E7EB; border-radius:8px; padding:9px 20px; font-weight:500; } QPushButton:hover { background:#E5E7EB; }'

MODULE_CONFIG = {
    'students':   ('📚', 'Élèves',          PRIMARY,   PRIMARY_LIGHT,  'students'),
    'employees':  ('👥', 'Personnel',        SUCCESS,   SUCCESS_LIGHT,  'employees'),
    'expenses':   ('💸', 'Dépenses',         DANGER,    DANGER_LIGHT,   'expenses'),
    'transport':  ('🚌', 'Transport',        INFO,      INFO_LIGHT,     'transport'),
    'timetable':  ('📅', 'Emploi du Temps',  PURPLE,    PURPLE_LIGHT,   'timetable'),
    'payments':   ('💳', 'Paiements',        TEAL,      TEAL_LIGHT,     'payments'),
}


class ImportWorker(QThread):
    """Run the import in a background thread to keep UI responsive."""
    finished  = Signal(object)   # ImportResult
    error     = Signal(str)

    def __init__(self, module, xlsx_path, session, mode):
        super().__init__()
        self.module    = module
        self.xlsx_path = xlsx_path
        self.session   = session
        self.mode      = mode

    def run(self):
        try:
            if self.module == 'students':
                from services.importers.students_importer import import_students
                result = import_students(self.xlsx_path, self.session, self.mode)
            elif self.module == 'employees':
                from services.importers.employees_importer import import_employees
                result = import_employees(self.xlsx_path, self.session, self.mode)
            elif self.module == 'expenses':
                from services.importers.expenses_importer import import_expenses
                result = import_expenses(self.xlsx_path, self.session, self.mode)
            elif self.module == 'transport':
                from services.importers.transport_importer import import_buses
                result = import_buses(self.xlsx_path, self.session, self.mode)
            elif self.module == 'timetable':
                from services.importers.timetable_importer import import_timetable
                result = import_timetable(self.xlsx_path, self.session, self.mode)
            elif self.module == 'payments':
                from services.importers.payments_importer import import_payments
                result = import_payments(self.xlsx_path, self.session, self.mode)
            else:
                self.error.emit(f"Module inconnu: {self.module}")
                return
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ModuleCard(QFrame):
    """Clickable card for one importable module."""
    clicked = Signal(str)

    def __init__(self, key, icon, label, accent, light, parent=None):
        super().__init__(parent)
        self.key = key
        self.setFixedHeight(130)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._accent = accent
        self._light  = light
        self._normal_style = f'''
            QFrame {{ background:white; border:1.5px solid {BORDER};
                border-radius:14px; }}
            QFrame:hover {{ border-color:{accent}; background:{light}; }}
        '''
        self._selected_style = f'''
            QFrame {{ background:{light}; border:2px solid {accent};
                border-radius:14px; }}
        '''
        self.setStyleSheet(self._normal_style)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        top = QHBoxLayout()
        pill = QLabel(icon)
        pill.setFixedSize(40, 40)
        pill.setAlignment(Qt.AlignCenter)
        pill.setStyleSheet(f'background:{light}; border-radius:12px; font-size:20px;')
        top.addWidget(pill); top.addStretch()

        self.check = QLabel('✓')
        self.check.setStyleSheet(f'color:{accent}; font-size:18px; font-weight:800; background:transparent;')
        self.check.setVisible(False)
        top.addWidget(self.check)
        layout.addLayout(top)

        lbl = QLabel(label)
        lbl.setStyleSheet(f'color:{TEXT_MAIN}; font-size:13px; font-weight:700; background:transparent;')
        sub = QLabel('Cliquez pour sélectionner')
        sub.setStyleSheet(f'color:{TEXT_SUB}; font-size:11px; background:transparent;')
        layout.addWidget(lbl); layout.addWidget(sub)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.key)

    def set_selected(self, selected: bool):
        self.setStyleSheet(self._selected_style if selected else self._normal_style)
        self.check.setVisible(selected)


class ImportCenter(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session      = session
        self.selected_mod = None
        self.xlsx_path    = None
        self.worker       = None
        self.cards        = {}
        self.setStyleSheet('background:transparent;')
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border:none; background:transparent; }')

        container = QWidget(); container.setStyleSheet('background:transparent;')
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(28, 24, 28, 28)
        self.main_layout.setSpacing(20)

        # ── Header ────────────────────────────────────────────────
        hdr_col = QVBoxLayout(); hdr_col.setSpacing(4)
        t = QLabel('📥  Centre d\'Import Excel')
        t.setStyleSheet(f'color:{TEXT_MAIN}; font-size:20px; font-weight:800; background:transparent;')
        s = QLabel('Importez vos données depuis des fichiers Excel · Téléchargez les templates pré-remplis')
        s.setStyleSheet(f'color:{TEXT_SUB}; font-size:13px; background:transparent;')
        hdr_col.addWidget(t); hdr_col.addWidget(s)
        self.main_layout.addLayout(hdr_col)

        # ── Info banner ────────────────────────────────────────────
        banner = QFrame()
        banner.setStyleSheet(f'QFrame {{ background:{NAN_COLOR}; border:1px solid #FDE047; border-radius:12px; }}')
        bl = QHBoxLayout(banner); bl.setContentsMargins(16, 10, 16, 10); bl.setSpacing(10)
        bl.addWidget(QLabel('ℹ️')); 
        info_lbl = QLabel(
            'Sélectionnez un module → téléchargez le template → remplissez-le → importez.\n'
            'Les données existantes ne sont jamais écrasées (mode "Ignorer" par défaut).'
        )
        info_lbl.setStyleSheet(f'color:#854D0E; font-size:12px; background:transparent;')
        info_lbl.setWordWrap(True)
        bl.addWidget(info_lbl, 1)
        self.main_layout.addWidget(banner)

        # ── Module grid ────────────────────────────────────────────
        mod_title = QLabel('1.  Choisissez le module à importer')
        mod_title.setStyleSheet(f'color:{TEXT_MAIN}; font-size:14px; font-weight:700; background:transparent;')
        self.main_layout.addWidget(mod_title)

        grid = QGridLayout(); grid.setSpacing(12)
        for idx, (key, (icon, label, accent, light, _)) in enumerate(MODULE_CONFIG.items()):
            card = ModuleCard(key, icon, label, accent, light)
            card.clicked.connect(self._select_module)
            self.cards[key] = card
            grid.addWidget(card, idx // 3, idx % 3)
        self.main_layout.addLayout(grid)

        # ── Step 2: Template download ──────────────────────────────
        step2_frame = QFrame()
        step2_frame.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}')
        s2l = QVBoxLayout(step2_frame); s2l.setContentsMargins(20, 16, 20, 16); s2l.setSpacing(10)
        step2_title = QLabel('2.  Téléchargez le template')
        step2_title.setStyleSheet(f'color:{TEXT_MAIN}; font-size:14px; font-weight:700; background:transparent;')
        s2l.addWidget(step2_title)

        step2_row = QHBoxLayout(); step2_row.setSpacing(10)
        self.template_desc = QLabel('Sélectionnez d\'abord un module ci-dessus.')
        self.template_desc.setStyleSheet(f'color:{TEXT_SUB}; font-size:13px; background:transparent;')
        step2_row.addWidget(self.template_desc, 1)

        self.dl_btn = QPushButton('⬇  Télécharger le Template')
        self.dl_btn.setFixedHeight(40); self.dl_btn.setEnabled(False)
        self.dl_btn.setStyleSheet(BTN_SEC); self.dl_btn.clicked.connect(self._download_template)
        step2_row.addWidget(self.dl_btn)
        s2l.addLayout(step2_row)
        self.main_layout.addWidget(step2_frame)

        # ── Step 3: File picker + options ─────────────────────────
        step3_frame = QFrame()
        step3_frame.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}')
        s3l = QVBoxLayout(step3_frame); s3l.setContentsMargins(20, 16, 20, 16); s3l.setSpacing(12)
        step3_title = QLabel('3.  Choisissez votre fichier Excel')
        step3_title.setStyleSheet(f'color:{TEXT_MAIN}; font-size:14px; font-weight:700; background:transparent;')
        s3l.addWidget(step3_title)

        file_row = QHBoxLayout(); file_row.setSpacing(10)
        self.file_lbl = QLabel('Aucun fichier sélectionné')
        self.file_lbl.setStyleSheet(f'color:{TEXT_SUB}; font-size:12px; background:transparent; font-style:italic;')
        self.file_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        browse_btn = QPushButton('📂  Parcourir…')
        browse_btn.setFixedHeight(38); browse_btn.setStyleSheet(BTN_SEC)
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self.file_lbl, 1); file_row.addWidget(browse_btn)
        s3l.addLayout(file_row)

        # Options row
        opt_row = QHBoxLayout(); opt_row.setSpacing(20)
        mode_lbl = QLabel('En cas de doublon :')
        mode_lbl.setStyleSheet(f'color:#374151; font-size:12px; font-weight:600; background:transparent;')
        self.mode_combo = QComboBox()
        self.mode_combo.addItem('⏭  Ignorer (conserver existant)', 'skip')
        self.mode_combo.addItem('♻️  Mettre à jour', 'update')
        self.mode_combo.setFixedHeight(36)
        self.mode_combo.setStyleSheet(f'''
            QComboBox {{ background:white; border:1.5px solid {BORDER}; border-radius:8px;
                color:{TEXT_MAIN}; padding:0 12px; font-size:13px; min-width:220px; }}
            QComboBox QAbstractItemView {{ background:white; border:1.5px solid #C7D2FE;
                border-radius:10px; color:{TEXT_MAIN}; padding:4px; outline:none; }}
            QComboBox QAbstractItemView::item {{ padding:9px 14px; border-radius:6px;
                margin:1px 4px; color:{TEXT_MAIN}; }}
            QComboBox QAbstractItemView::item:hover {{ background:#F5F3FF; color:{PRIMARY}; }}
            QComboBox QAbstractItemView::item:selected {{ background:{PRIMARY_LIGHT}; color:{PRIMARY}; }}
        ''')
        opt_row.addWidget(mode_lbl); opt_row.addWidget(self.mode_combo); opt_row.addStretch()
        s3l.addLayout(opt_row)
        self.main_layout.addWidget(step3_frame)

        # ── Step 4: Import button + progress ──────────────────────
        step4_frame = QFrame()
        step4_frame.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}')
        s4l = QVBoxLayout(step4_frame); s4l.setContentsMargins(20, 16, 20, 16); s4l.setSpacing(10)
        step4_title = QLabel('4.  Lancez l\'import')
        step4_title.setStyleSheet(f'color:{TEXT_MAIN}; font-size:14px; font-weight:700; background:transparent;')
        s4l.addWidget(step4_title)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self.import_btn = QPushButton('🚀  Lancer l\'import')
        self.import_btn.setFixedHeight(44); self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet(BTN); self.import_btn.clicked.connect(self._run_import)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0); self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(f'QProgressBar {{ border:none; border-radius:3px; background:#F3F4F6; }} QProgressBar::chunk {{ background:{PRIMARY}; border-radius:3px; }}')
        btn_row.addStretch(); btn_row.addWidget(self.import_btn)
        s4l.addLayout(btn_row); s4l.addWidget(self.progress)
        self.main_layout.addWidget(step4_frame)

        # ── Result panel ───────────────────────────────────────────
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet(f'QFrame {{ background:white; border:1px solid {BORDER}; border-radius:14px; }}')
        self.result_frame.setVisible(False)
        rfl = QVBoxLayout(self.result_frame); rfl.setContentsMargins(20, 16, 20, 16); rfl.setSpacing(8)
        result_title = QLabel('📊  Résultat de l\'import')
        result_title.setStyleSheet(f'color:{TEXT_MAIN}; font-size:14px; font-weight:700; background:transparent;')
        rfl.addWidget(result_title)

        self.result_stats_row = QHBoxLayout(); self.result_stats_row.setSpacing(10)
        rfl.addLayout(self.result_stats_row)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(160)
        self.result_text.setStyleSheet(f'QTextEdit {{ background:#F9FAFB; border:1px solid {BORDER}; border-radius:8px; font-family:monospace; font-size:12px; color:{TEXT_MAIN}; padding:8px; }}')
        rfl.addWidget(self.result_text)
        self.main_layout.addWidget(self.result_frame)

        self.main_layout.addStretch()

        scroll.setWidget(container)
        ol = QVBoxLayout(self); ol.setContentsMargins(0,0,0,0); ol.addWidget(scroll)

    # ── Module selection ──────────────────────────────────────────

    def _select_module(self, key):
        self.selected_mod = key
        for k, card in self.cards.items():
            card.set_selected(k == key)

        icon, label, accent, light, _ = MODULE_CONFIG[key]
        self.template_desc.setText(
            f'{icon}  Template <b>{label}</b> prêt — cliquez pour télécharger le fichier Excel vierge.'
        )
        self.dl_btn.setEnabled(True)
        self.dl_btn.setStyleSheet(f'QPushButton {{ background:{accent}; color:white; border:none; border-radius:8px; padding:9px 20px; font-weight:600; font-size:13px; }} QPushButton:hover {{ opacity:0.9; }}')
        self._update_import_btn()

    def _update_import_btn(self):
        ready = bool(self.selected_mod and self.xlsx_path)
        self.import_btn.setEnabled(ready)

    # ── Template download ─────────────────────────────────────────

    def _download_template(self):
        if not self.selected_mod:
            return
        from services.template_generator import TEMPLATE_GENERATORS
        _, default_name, label = TEMPLATE_GENERATORS[self.selected_mod]
        path, _ = QFileDialog.getSaveFileName(
            self, f'Enregistrer le template — {label}',
            default_name, 'Excel (*.xlsx)'
        )
        if not path:
            return
        try:
            from services.template_generator import generate_template
            generate_template(self.selected_mod, path)
            QMessageBox.information(self, '✅ Template téléchargé',
                f'Template enregistré :\n{path}\n\n'
                'Remplissez-le puis importez-le à l\'étape 3.')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la génération :\n{e}')

    # ── File browser ──────────────────────────────────────────────

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Choisir un fichier Excel', '', 'Excel (*.xlsx *.xls)'
        )
        if path:
            self.xlsx_path = path
            fname = os.path.basename(path)
            self.file_lbl.setText(f'📄  {fname}')
            self.file_lbl.setStyleSheet(f'color:{TEXT_MAIN}; font-size:12px; background:transparent; font-style:normal; font-weight:600;')
        self._update_import_btn()

    # ── Import execution ──────────────────────────────────────────

    def _run_import(self):
        if not self.selected_mod or not self.xlsx_path:
            return

        icon, label, accent, light, _ = MODULE_CONFIG[self.selected_mod]

        reply = QMessageBox.question(
            self, 'Confirmer l\'import',
            f'Importer le fichier :\n{os.path.basename(self.xlsx_path)}\n\n'
            f'Module : {icon} {label}\n'
            f'Mode doublons : {self.mode_combo.currentText()}\n\n'
            'Continuer ?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        # UI → loading state
        self.import_btn.setEnabled(False)
        self.import_btn.setText('⏳  Import en cours…')
        self.progress.setVisible(True)
        self.result_frame.setVisible(False)

        mode = self.mode_combo.currentData()
        self.worker = ImportWorker(self.selected_mod, self.xlsx_path, self.session, mode)
        self.worker.finished.connect(self._on_import_done)
        self.worker.error.connect(self._on_import_error)
        self.worker.start()

    def _on_import_done(self, result):
        self.progress.setVisible(False)
        self.import_btn.setEnabled(True)
        self.import_btn.setText('🚀  Lancer l\'import')

        # Clear old stat chips
        for i in reversed(range(self.result_stats_row.count())):
            w = self.result_stats_row.itemAt(i).widget()
            if w: w.setParent(None)

        # Build stat chips
        for text, color, light in [
            (f'✅  {result.inserted} insérés',    SUCCESS, SUCCESS_LIGHT),
            (f'♻️  {result.updated} mis à jour',   PRIMARY, PRIMARY_LIGHT),
            (f'⏭  {result.skipped} ignorés',      TEXT_SUB, '#F3F4F6'),
            (f'❌  {len(result.errors)} erreurs',  DANGER,  DANGER_LIGHT),
        ]:
            chip = QLabel(text)
            chip.setStyleSheet(f'color:{color}; background:{light}; border-radius:10px; padding:5px 14px; font-size:12px; font-weight:700;')
            self.result_stats_row.addWidget(chip)
        self.result_stats_row.addStretch()

        self.result_text.setPlainText(result.summary())
        self.result_frame.setVisible(True)

        if result.inserted > 0 or result.updated > 0:
            QMessageBox.information(self, '✅ Import réussi',
                f'Import terminé avec succès!\n\n'
                f'• {result.inserted} enregistrements insérés\n'
                f'• {result.updated} mis à jour\n'
                f'• {result.skipped} ignorés\n'
                f'• {len(result.errors)} erreurs\n\n'
                'Actualisez la page concernée pour voir les données.')
        else:
            QMessageBox.warning(self, '⚠ Import sans nouvelles données',
                f'Aucune nouvelle donnée insérée.\n\n{result.summary()}')

    def _on_import_error(self, error_msg):
        self.progress.setVisible(False)
        self.import_btn.setEnabled(True)
        self.import_btn.setText('🚀  Lancer l\'import')
        QMessageBox.critical(self, '❌ Erreur d\'import',
            f'Une erreur s\'est produite :\n\n{error_msg}')

    def refresh(self):
        pass  # stateless widget
