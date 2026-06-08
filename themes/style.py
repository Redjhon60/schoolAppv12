# ─────────────────────────────────────────────────────────────────────
#  Le Schéma SGS v3 — Modern Light Theme
# ─────────────────────────────────────────────────────────────────────

LIGHT_THEME = """
QWidget {
    background-color: #F7F8FC;
    color: #1A1D2E;
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog { background-color: #F7F8FC; }

#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #EAEDF3;
}
#topbar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #EAEDF3;
    min-height: 58px; max-height: 58px;
    padding: 0 28px;
}

QPushButton#nav_btn {
    background: transparent; border: none; border-radius: 8px;
    color: #6B7280; text-align: left; padding: 10px 14px;
    font-size: 13px; font-weight: 500; margin: 1px 8px;
}
QPushButton#nav_btn:hover { background-color: #F3F4F8; color: #1A1D2E; }
QPushButton#nav_btn:checked {
    background-color: #EEF2FF; color: #4F46E5; font-weight: 600;
}

QFrame#stat_card {
    background-color: #FFFFFF; border: 1px solid #EAEDF3; border-radius: 14px;
}
QFrame#stat_card:hover { border-color: #C7D2FE; background-color: #FAFAFF; }

QPushButton {
    background-color: #4F46E5; color: #FFFFFF; border: none;
    border-radius: 8px; padding: 9px 20px; font-weight: 600; font-size: 13px;
}
QPushButton:hover { background-color: #4338CA; }
QPushButton:pressed { background-color: #3730A3; }
QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }

QPushButton#btn_danger { background-color: #EF4444; color: white; }
QPushButton#btn_danger:hover { background-color: #DC2626; }
QPushButton#btn_success { background-color: #10B981; color: white; }
QPushButton#btn_success:hover { background-color: #059669; }
QPushButton#btn_secondary {
    background-color: #F3F4F6; color: #374151; border: 1px solid #E5E7EB;
}
QPushButton#btn_secondary:hover { background-color: #E5E7EB; }
QPushButton#btn_warning { background-color: #F59E0B; color: white; }
QPushButton#btn_warning:hover { background-color: #D97706; }
QPushButton#btn_nan {
    background-color: #FEF9C3; color: #854D0E; border: 1px solid #FDE047;
    border-radius: 6px; font-size: 11px; padding: 3px 8px;
}

QTableWidget {
    background-color: #FFFFFF; border: 1px solid #EAEDF3;
    border-radius: 12px; gridline-color: #F3F4F8; outline: none;
    selection-background-color: #EEF2FF;
}
QTableWidget::item { padding: 9px 12px; border-bottom: 1px solid #F3F4F8; color: #374151; }
QTableWidget::item:selected { background-color: #EEF2FF; color: #4F46E5; }
QTableWidget::item:alternate { background-color: #FAFBFD; }
QHeaderView::section {
    background-color: #F9FAFB; color: #6B7280; padding: 10px 12px;
    border: none; border-bottom: 2px solid #EAEDF3;
    font-weight: 700; font-size: 11px; letter-spacing: 0.5px;
}

QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF; border: 1.5px solid #E5E7EB;
    border-radius: 8px; color: #1A1D2E; padding: 8px 12px; font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #4F46E5; background-color: #FAFAFF;
}
QLineEdit:hover, QComboBox:hover { border-color: #A5B4FC; }

QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow {
    width: 0; height: 0;
    border-left: 5px solid transparent; border-right: 5px solid transparent;
    border-top: 6px solid #6B7280;
}
QComboBox::down-arrow:hover { border-top-color: #4F46E5; }

QComboBox QAbstractItemView {
    background-color: #FFFFFF; border: 1.5px solid #C7D2FE;
    border-radius: 10px; color: #1A1D2E; padding: 4px; outline: none;
    show-decoration-selected: 1;
}
QComboBox QAbstractItemView::item {
    background-color: transparent; color: #1A1D2E;
    padding: 9px 14px; min-height: 30px; border-radius: 6px; margin: 1px 4px;
}
QComboBox QAbstractItemView::item:hover { background-color: #F5F3FF; color: #4F46E5; }
QComboBox QAbstractItemView::item:selected {
    background-color: #EEF2FF; color: #4F46E5; font-weight: 600;
}

QScrollBar:vertical { background: transparent; width: 6px; }
QScrollBar::handle:vertical { background: #D1D5DB; border-radius: 3px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #9CA3AF; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 6px; }
QScrollBar::handle:horizontal { background: #D1D5DB; border-radius: 3px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QTabWidget::pane { border: 1px solid #EAEDF3; border-radius: 12px; background: #FFFFFF; top: -1px; }
QTabBar::tab {
    background: transparent; color: #6B7280; border: none;
    border-bottom: 2px solid transparent; padding: 10px 22px;
    font-size: 13px; font-weight: 500; margin-right: 4px;
}
QTabBar::tab:selected { color: #4F46E5; border-bottom: 2px solid #4F46E5; font-weight: 700; }
QTabBar::tab:hover:!selected { color: #374151; background: #F9FAFB; border-radius: 8px 8px 0 0; }

QGroupBox {
    border: 1.5px solid #EAEDF3; border-radius: 12px; margin-top: 18px;
    padding: 16px 16px 12px 16px; background: #FFFFFF; font-weight: 600; color: #374151;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left; left: 14px;
    padding: 0 8px; color: #4F46E5; background: #FFFFFF; font-size: 12px; font-weight: 700;
}

QCheckBox { color: #374151; spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 17px; height: 17px; border-radius: 5px;
    border: 1.5px solid #D1D5DB; background: #FFFFFF;
}
QCheckBox::indicator:hover { border-color: #4F46E5; }
QCheckBox::indicator:checked { background-color: #4F46E5; border-color: #4F46E5; }

QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QStatusBar { background: #FFFFFF; color: #9CA3AF; border-top: 1px solid #EAEDF3; font-size: 11px; }
QMessageBox { background-color: #FFFFFF; }
QMessageBox QLabel { color: #374151; }
"""

DARK_THEME = LIGHT_THEME  # alias

# ── Design tokens ─────────────────────────────────────────────────────
PRIMARY       = '#4F46E5'
PRIMARY_LIGHT = '#EEF2FF'
PRIMARY_DARK  = '#3730A3'
SUCCESS       = '#10B981'
SUCCESS_LIGHT = '#D1FAE5'
DANGER        = '#EF4444'
DANGER_LIGHT  = '#FEE2E2'
WARNING       = '#F59E0B'
WARNING_LIGHT = '#FEF3C7'
INFO          = '#3B82F6'
INFO_LIGHT    = '#DBEAFE'
PURPLE        = '#8B5CF6'
PURPLE_LIGHT  = '#EDE9FE'
PINK          = '#EC4899'
PINK_LIGHT    = '#FCE7F3'
TEAL          = '#14B8A6'
TEAL_LIGHT    = '#CCFBF1'
NAN_COLOR     = '#FEF9C3'   # yellow tint for NAN months
NAN_TEXT      = '#854D0E'

BG_PAGE   = '#F7F8FC'
BG_CARD   = '#FFFFFF'
BG_SUBTLE = '#F9FAFB'
BORDER    = '#EAEDF3'
TEXT_MAIN = '#1A1D2E'
TEXT_SUB  = '#6B7280'
TEXT_MUTED= '#9CA3AF'

TABLE_CSS = f"""
    QTableWidget {{
        background-color: {BG_CARD}; border: 1px solid {BORDER};
        border-radius: 12px; gridline-color: #F3F4F8; outline: none;
    }}
    QTableWidget::item {{ padding: 9px 12px; border-bottom: 1px solid #F3F4F8; color: #374151; }}
    QTableWidget::item:selected {{ background-color: {PRIMARY_LIGHT}; color: {PRIMARY}; }}
    QTableWidget::item:alternate {{ background-color: #FAFBFD; }}
    QHeaderView::section {{
        background-color: #F9FAFB; color: #6B7280; padding: 10px 12px;
        border: none; border-bottom: 2px solid {BORDER};
        font-weight: 700; font-size: 11px; letter-spacing: 0.5px;
    }}
"""

DIALOG_CSS = f"""
    QDialog {{ background-color: {BG_CARD}; }}
    QLabel {{ color: {TEXT_SUB}; font-size: 12px; background: transparent; }}
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QDoubleSpinBox, QSpinBox {{
        background-color: {BG_CARD}; border: 1.5px solid {BORDER};
        border-radius: 8px; color: {TEXT_MAIN}; padding: 8px 12px; font-size: 13px;
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus,
    QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: {PRIMARY}; }}
    QComboBox QAbstractItemView {{
        background-color: #FFFFFF; color: {TEXT_MAIN}; border: 1.5px solid #C7D2FE;
        border-radius: 10px; padding: 4px; outline: none; show-decoration-selected: 1;
    }}
    QComboBox QAbstractItemView::item {{
        background-color: transparent; color: {TEXT_MAIN};
        padding: 9px 14px; min-height: 30px; border-radius: 6px; margin: 1px 4px;
    }}
    QComboBox QAbstractItemView::item:hover {{ background-color: #F5F3FF; color: {PRIMARY}; }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: {PRIMARY_LIGHT}; color: {PRIMARY}; font-weight: 600;
    }}
    QCheckBox {{ color: {TEXT_MAIN}; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 17px; height: 17px; border-radius: 5px;
        border: 1.5px solid #D1D5DB; background: white;
    }}
    QCheckBox::indicator:checked {{ background-color: {PRIMARY}; border-color: {PRIMARY}; }}
    QScrollArea {{ border: none; background: transparent; }}
"""

CLASSES = [
    'PS', 'MS', 'GS', 'CP', 'CE1', 'CE2', 'CM1', 'CM2',
    '6EME', '1AC', '2AC', '3AC', 'TC', '1BAC', '1BAC SM', '2BAC'
]

SCHOOL_MONTHS = [
    'Septembre', 'Octobre', 'Novembre', 'Décembre',
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin'
]

MONTHS = SCHOOL_MONTHS  # alias for imports

EXPENSE_CATEGORIES = [
    'Électricité', 'Eau', 'Loyer', 'Matériel', 'Fournitures',
    'Maintenance', 'Communication', 'Autre'
]

REINSCRIPTION_OPTIONS = ['pending', 'yes', 'no']
REINSCRIPTION_LABELS = {'pending': '⏳ En attente', 'yes': '✅ Oui', 'no': '❌ Non'}
REINSCRIPTION_COLORS = {'pending': WARNING, 'yes': SUCCESS, 'no': DANGER}
