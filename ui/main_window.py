"""
main_window.py — SGS v4
• Collapsible / expandable sidebar (240 px ↔ 58 px) with smooth animation
• All dialogs centred on screen and sized relative to available screen space
• Topbar with breadcrumb, refresh button, and sidebar toggle
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy,
    QApplication, QDialog
)
from PySide6.QtCore    import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui     import QPixmap, QIcon

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'school_logo.png')
ICON_PATH = os.path.join(BASE_DIR, 'assets', 'school_logo.ico')

SIDEBAR_EXPANDED  = 240
SIDEBAR_COLLAPSED = 58
ANIM_DURATION_MS  = 220   # sidebar slide duration

# ── Responsive dialog helper ──────────────────────────────────────────────────

def responsive_dialog(dlg: QDialog,
                      preferred_w: int,
                      preferred_h: int,
                      max_frac_w: float = 0.90,
                      max_frac_h: float = 0.88):
    """
    Centre a QDialog on the primary screen and cap its size so it always fits.
    Call this instead of setMinimumSize / setFixedSize on every dialog.
    """
    screen = QApplication.primaryScreen()
    if screen:
        avail  = screen.availableGeometry()
        max_w  = int(avail.width()  * max_frac_w)
        max_h  = int(avail.height() * max_frac_h)
        w = min(preferred_w, max_w)
        h = min(preferred_h, max_h)
        dlg.setMinimumSize(min(w, 420), min(h, 340))
        dlg.resize(w, h)
        # Centre on screen
        cx = avail.x() + (avail.width()  - w) // 2
        cy = avail.y() + (avail.height() - h) // 2
        dlg.move(cx, cy)
    else:
        dlg.resize(preferred_w, preferred_h)


# ── Nav button ────────────────────────────────────────────────────────────────

class NavButton(QPushButton):
    """
    Sidebar navigation button.
    In expanded mode shows "  icon   Label".
    In collapsed mode shows only the icon, centred.
    """
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setObjectName('nav_btn')
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self._icon  = icon_text
        self._label = label
        self._expanded = True
        self._update_text()

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._update_text()

    def _update_text(self):
        if self._expanded:
            self.setText(f'  {self._icon}   {self._label}')
            self.setStyleSheet('')       # let stylesheet handle alignment
        else:
            self.setText(self._icon)
            self.setStyleSheet(
                'QPushButton#nav_btn { text-align: center; padding: 0; font-size: 18px; }'
            )
        self.setToolTip('' if self._expanded else self._label)


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle('Le Schéma SGS v4')
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        # Respect screen size — default to 90 % of available area
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            w = int(avail.width()  * 0.92)
            h = int(avail.height() * 0.92)
            self.resize(w, h)
            self.setMinimumSize(900, 600)
            cx = avail.x() + (avail.width()  - w) // 2
            cy = avail.y() + (avail.height() - h) // 2
            self.move(cx, cy)
        else:
            self.setMinimumSize(1100, 700)

        from models.database import get_session
        self.session = get_session()
        self._pages = {}
        self._sidebar_expanded = True
        self._init_ui()
        try:
            self._navigate(0)
        except Exception as _e:
            import traceback as _tb
            print('Dashboard load error:\n', _tb.format_exc())

    def closeEvent(self, e):
        self.session.close()
        super().closeEvent(e)

    # ── UI construction ───────────────────────────────────────────────────────

    def _init_ui(self):
        from themes.style import LIGHT_THEME
        self.setStyleSheet(LIGHT_THEME)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══ SIDEBAR ══════════════════════════════════════════════════════════
        self.sidebar = QFrame()
        self.sidebar.setObjectName('sidebar')
        self.sidebar.setFixedWidth(SIDEBAR_EXPANDED)
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        # ── Logo zone ─────────────────────────────────────────────────────
        self.logo_zone = QWidget()
        self.logo_zone.setFixedHeight(64)
        self.logo_zone.setStyleSheet(
            'background: transparent; border-bottom: 1px solid #EAEDF3;'
        )
        lz = QHBoxLayout(self.logo_zone)
        lz.setContentsMargins(12, 0, 12, 0)
        lz.setSpacing(10)

        self.logo_lbl = QLabel()
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH).scaled(
                36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.logo_lbl.setPixmap(pix)
        self.logo_lbl.setFixedSize(38, 38)
        self.logo_lbl.setAlignment(Qt.AlignCenter)

        txt_col = QVBoxLayout(); txt_col.setSpacing(1)
        self.app_name_lbl = QLabel('Le Schéma')
        self.app_name_lbl.setStyleSheet(
            'color:#1A1D2E; font-size:14px; font-weight:700; background:transparent;'
        )
        self.app_sub_lbl = QLabel('Gestion Scolaire v4')
        self.app_sub_lbl.setStyleSheet(
            'color:#9CA3AF; font-size:10px; background:transparent;'
        )
        txt_col.addWidget(self.app_name_lbl)
        txt_col.addWidget(self.app_sub_lbl)

        lz.addWidget(self.logo_lbl)
        lz.addLayout(txt_col)
        lz.addStretch()
        sb.addWidget(self.logo_zone)
        sb.addSpacing(8)

        # ── Navigation items ──────────────────────────────────────────────
        NAV_MAIN = [
            ('🏠', 'Tableau de Bord',   0),
            ('🎓', 'Élèves',            1),
            ('💳', 'Paiements',         2),
            ('🛡️', 'Assurances',         3),
            ('👥', 'Personnel',         4),
            ('💸', 'Dépenses',          5),
        ]
        NAV_ADMIN = [
            ('🚌', 'Transport',         6),
            ('📅', 'Emploi du Temps',   7),
            ('📊', 'Rapports',          8),
            ('📥', 'Import Excel',      9),
            ('⚙️',  'Paramètres',        10),
        ]

        self.sec_main_lbl  = self._section_sep('MENU PRINCIPAL')
        self.sec_admin_lbl = self._section_sep('ADMINISTRATION')

        sb.addWidget(self.sec_main_lbl)
        self.nav_btns = []

        for icon, label, idx in NAV_MAIN:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            sb.addWidget(btn)
            self.nav_btns.append((idx, btn))

        sb.addSpacing(4)
        sb.addWidget(self.sec_admin_lbl)

        for icon, label, idx in NAV_ADMIN:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            sb.addWidget(btn)
            self.nav_btns.append((idx, btn))

        sb.addStretch()

        # ── User card ─────────────────────────────────────────────────────
        self.user_card = QFrame()
        self.user_card.setStyleSheet(
            'QFrame { background:#F7F8FC; border-top:1px solid #EAEDF3; }'
        )
        self.user_card.setFixedHeight(68)
        uc = QHBoxLayout(self.user_card)
        uc.setContentsMargins(12, 10, 12, 10)
        uc.setSpacing(10)

        role_icons = {'admin': '👑', 'comptable': '💼', 'secretaire': '📋'}
        self.avatar = QLabel(role_icons.get(self.user.role, '👤'))
        self.avatar.setFixedSize(36, 36)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet(
            'background:#EEF2FF; border-radius:18px; font-size:17px;'
        )

        info_col = QVBoxLayout(); info_col.setSpacing(1)
        self.uname_lbl = QLabel(self.user.full_name or self.user.username)
        self.uname_lbl.setStyleSheet(
            'color:#1A1D2E; font-weight:600; font-size:12px; background:transparent;'
        )
        urole = QLabel(self.user.role.capitalize())
        urole.setStyleSheet('color:#9CA3AF; font-size:10px; background:transparent;')
        info_col.addWidget(self.uname_lbl)
        info_col.addWidget(urole)

        logout = QPushButton('↩')
        logout.setFixedSize(30, 30)
        logout.setToolTip('Déconnexion')
        logout.setCursor(Qt.PointingHandCursor)
        logout.setStyleSheet(
            'QPushButton { background:transparent; color:#9CA3AF; border:none; '
            'font-size:16px; border-radius:6px; }'
            'QPushButton:hover { background:#FEE2E2; color:#EF4444; }'
        )
        logout.clicked.connect(self._logout)

        self.user_text_widget = QWidget()
        self.user_text_widget.setStyleSheet('background:transparent;')
        utw_l = QHBoxLayout(self.user_text_widget)
        utw_l.setContentsMargins(0, 0, 0, 0)
        utw_l.setSpacing(8)
        utw_l.addLayout(info_col)
        utw_l.addStretch()
        utw_l.addWidget(logout)

        uc.addWidget(self.avatar)
        uc.addWidget(self.user_text_widget, 1)
        sb.addWidget(self.user_card)

        # ══ CONTENT AREA ══════════════════════════════════════════════════════
        content = QWidget()
        content.setStyleSheet('background:#F7F8FC;')
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # ── Topbar ────────────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setObjectName('topbar')
        topbar.setFixedHeight(56)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 24, 0)
        tb.setSpacing(10)

        # Sidebar toggle button (hamburger / arrow)
        self.toggle_btn = QPushButton('◀')
        self.toggle_btn.setFixedSize(36, 36)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setToolTip('Réduire le menu')
        self.toggle_btn.setStyleSheet(
            'QPushButton { background:#F3F4F6; color:#4F46E5; border:1px solid #E5E7EB; '
            'border-radius:8px; font-size:14px; font-weight:700; }'
            'QPushButton:hover { background:#EEF2FF; border-color:#C7D2FE; }'
        )
        self.toggle_btn.clicked.connect(self._toggle_sidebar)

        # Page title + breadcrumb
        title_col = QVBoxLayout(); title_col.setSpacing(1)
        self.page_title = QLabel('Tableau de Bord')
        self.page_title.setStyleSheet(
            'color:#1A1D2E; font-size:16px; font-weight:700; background:transparent;'
        )
        self.breadcrumb = QLabel('SGS v4  ›  Tableau de Bord')
        self.breadcrumb.setStyleSheet(
            'color:#9CA3AF; font-size:10px; background:transparent;'
        )
        title_col.addWidget(self.page_title)
        title_col.addWidget(self.breadcrumb)

        from datetime import datetime
        date_lbl = QLabel(datetime.now().strftime('%A %d %B %Y'))
        date_lbl.setStyleSheet(
            'color:#9CA3AF; font-size:11px; background:transparent;'
        )

        refresh_btn = QPushButton('↺  Actualiser')
        refresh_btn.setFixedHeight(32)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(
            'QPushButton { background:#F3F4F6; color:#374151; border:1px solid #E5E7EB; '
            'border-radius:8px; padding:0 14px; font-size:11px; font-weight:500; }'
            'QPushButton:hover { background:#E5E7EB; }'
        )
        refresh_btn.clicked.connect(self._refresh_current)

        tb.addWidget(self.toggle_btn)
        tb.addSpacing(6)
        tb.addLayout(title_col)
        tb.addStretch()
        tb.addWidget(date_lbl)
        tb.addSpacing(12)
        tb.addWidget(refresh_btn)

        # ── Stacked pages ─────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet('background:transparent;')

        cl.addWidget(topbar)
        cl.addWidget(self.stack, 1)

        root.addWidget(self.sidebar)
        root.addWidget(content, 1)

        # ── Status bar ─────────────────────────────────────────────────────
        from PySide6.QtWidgets import QStatusBar
        from datetime import datetime as _dt
        status_bar = QStatusBar()
        status_bar.setStyleSheet(
            'QStatusBar { background: white; color: #9CA3AF; '
            'border-top: 1px solid #EAEDF3; font-size: 11px; padding: 0 16px; }'
        )
        self._status_lbl = QLabel(
            f'SGS v4  •  {self.user.full_name or self.user.username}  •  '
            f'{_dt.now().strftime("%H:%M")}  •  Ctrl+1-6 navigation rapide'
        )
        self._status_lbl.setStyleSheet('color:#9CA3AF; font-size:11px; background:transparent;')
        status_bar.addWidget(self._status_lbl)
        self.setStatusBar(status_bar)

        # ── Keyboard shortcuts ─────────────────────────────────────────────
        from PySide6.QtGui import QShortcut, QKeySequence
        for seq, idx in [('Ctrl+1',0),('Ctrl+2',1),('Ctrl+3',2),
                          ('Ctrl+4',3),('Ctrl+5',4),('Ctrl+6',5)]:
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(lambda i=idx: self._navigate(i))
        QShortcut(QKeySequence('Ctrl+R'), self).activated.connect(self._refresh_current)
        QShortcut(QKeySequence('Ctrl+B'), self).activated.connect(self._toggle_sidebar)

        # Animation for sidebar width
        self._sidebar_anim = QPropertyAnimation(self.sidebar, b'minimumWidth')
        self._sidebar_anim.setDuration(ANIM_DURATION_MS)
        self._sidebar_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._sidebar_anim2 = QPropertyAnimation(self.sidebar, b'maximumWidth')
        self._sidebar_anim2.setDuration(ANIM_DURATION_MS)
        self._sidebar_anim2.setEasingCurve(QEasingCurve.InOutCubic)

    # ── Section separator helper ──────────────────────────────────────────────

    def _section_sep(self, text):
        lbl = QLabel(f'  {text}')
        lbl.setStyleSheet(
            'color:#9CA3AF; font-size:9px; font-weight:700; '
            'letter-spacing:1px; padding:6px 18px 2px 18px; background:transparent;'
        )
        return lbl

    # ── Sidebar toggle ────────────────────────────────────────────────────────

    def _toggle_sidebar(self):
        expanding = not self._sidebar_expanded
        target    = SIDEBAR_EXPANDED if expanding else SIDEBAR_COLLAPSED

        # Animate both min and max width simultaneously
        for anim in (self._sidebar_anim, self._sidebar_anim2):
            anim.stop()
            anim.setStartValue(self.sidebar.width())
            anim.setEndValue(target)
            anim.start()

        self._sidebar_expanded = expanding

        # Update toggle button icon
        self.toggle_btn.setText('◀' if expanding else '▶')
        self.toggle_btn.setToolTip(
            'Réduire le menu' if expanding else 'Développer le menu'
        )

        # Show/hide text labels after animation (use timer to let animation finish)
        QTimer.singleShot(ANIM_DURATION_MS + 10, self._apply_collapsed_state)

    def _apply_collapsed_state(self):
        expanded = self._sidebar_expanded
        # Nav buttons
        for _, btn in self.nav_btns:
            btn.set_expanded(expanded)
        # Section labels
        self.sec_main_lbl.setVisible(expanded)
        self.sec_admin_lbl.setVisible(expanded)
        # Logo text
        self.app_name_lbl.setVisible(expanded)
        self.app_sub_lbl.setVisible(expanded)
        # User card text
        self.user_text_widget.setVisible(expanded)
        # Avatar tooltip in collapsed mode
        if not expanded:
            self.avatar.setToolTip(
                f'{self.user.full_name or self.user.username} ({self.user.role})'
            )

    # ── Page factory ──────────────────────────────────────────────────────────

    def _get_page(self, idx):
        if idx in self._pages:
            return self._pages[idx]

        try:
            if   idx == 0:
                from ui.dashboard        import DashboardWidget;           w = DashboardWidget(self.session)
            elif idx == 1:
                from ui.students         import StudentsWidget;            w = StudentsWidget(self.session)
            elif idx == 2:
                from ui.payments_history import PaymentsHistoryWidget;     w = PaymentsHistoryWidget(self.session)
            elif idx == 3:
                from ui.insurance_dialog import InsuranceManagementWidget; w = InsuranceManagementWidget(self.session)
            elif idx == 4:
                from ui.employees        import EmployeesWidget;           w = EmployeesWidget(self.session)
            elif idx == 5:
                from ui.expenses         import ExpensesWidget;            w = ExpensesWidget(self.session)
            elif idx == 6:
                from ui.transport        import TransportWidget;           w = TransportWidget(self.session)
            elif idx == 7:
                from ui.timetable        import TimetableWidget;           w = TimetableWidget(self.session)
            elif idx == 8:
                from ui.reports          import ReportsWidget;             w = ReportsWidget(self.session)
            elif idx == 9:
                from ui.import_center    import ImportCenter;              w = ImportCenter(self.session)
            elif idx == 10:
                from ui.settings_widget  import SettingsWidget;           w = SettingsWidget(self.session)
            else:
                w = QLabel(f'Page {idx}')
        except Exception as _e:
            import traceback as _tb
            err_txt = _tb.format_exc()
            print(f'[MainWindow] Page {idx} load error:\n{err_txt}')
            # Show an inline error widget instead of crashing
            w = QWidget()
            el = QVBoxLayout(w)
            el.setContentsMargins(40, 40, 40, 40)
            el.setSpacing(12)
            title = QLabel('⚠️  Erreur de chargement')
            title.setStyleSheet('color:#EF4444; font-size:18px; font-weight:700;')
            msg = QLabel(f'{_e}')
            msg.setWordWrap(True)
            msg.setStyleSheet('color:#6B7280; font-size:13px;')
            detail = QLabel(err_txt)
            detail.setWordWrap(True)
            detail.setStyleSheet(
                'color:#9CA3AF; font-size:10px; font-family:monospace; '
                'background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px; padding:12px;'
            )
            retry = QPushButton('↺  Réessayer')
            retry.setFixedWidth(140)
            retry.setStyleSheet(
                'QPushButton{background:#4F46E5;color:white;border:none;'
                'border-radius:8px;padding:8px 16px;font-weight:600;}'
                'QPushButton:hover{background:#4338CA;}'
            )
            retry.clicked.connect(lambda: self._retry_page(idx))
            el.addWidget(title)
            el.addWidget(msg)
            el.addWidget(detail)
            el.addWidget(retry)
            el.addStretch()

        self.stack.addWidget(w)
        self._pages[idx] = w
        return w

    def _retry_page(self, idx):
        """Remove cached error page and reload."""
        if idx in self._pages:
            old = self._pages.pop(idx)
            self.stack.removeWidget(old)
            old.deleteLater()
        self._navigate(idx)

    # ── Navigation ────────────────────────────────────────────────────────────

    _PAGE_TITLES = [
        'Tableau de Bord', 'Gestion des Élèves', 'Historique Paiements',
        'Gestion des Assurances', 'Personnel & Enseignants', 'Dépenses',
        'Transport', 'Emploi du Temps', 'Rapports & Exports',
        'Import Excel', 'Paramètres',
    ]

    def _navigate(self, idx):
        for i, btn in self.nav_btns:
            btn.setChecked(i == idx)
        title = self._PAGE_TITLES[idx] if idx < len(self._PAGE_TITLES) else f'Page {idx}'
        self.page_title.setText(title)
        self.breadcrumb.setText(f'SGS v4  ›  {title}')
        self.stack.setCurrentWidget(self._get_page(idx))

    # ── Refresh current page ──────────────────────────────────────────────────

    def _refresh_current(self):
        idx = next((i for i, btn in self.nav_btns if btn.isChecked()), 0)
        if idx in self._pages:
            w = self._pages[idx]
            if   hasattr(w, 'refresh'):        w.refresh()
            elif hasattr(w, '_load_data'):     w._load_data()
            elif hasattr(w, '_load_students'): w._load_students()

    # ── Logout ────────────────────────────────────────────────────────────────

    def _logout(self):
        self.session.close()
        self.close()
        from ui.login_window import LoginWindow
        self._login = LoginWindow(self._relogin)
        self._login.show()

    def _relogin(self, user):
        self._login.close()
        from models.database import get_session
        self.session = get_session()
        self.user    = user
        self._pages.clear()
        while self.stack.count():
            self.stack.removeWidget(self.stack.widget(0))
        self._sidebar_expanded = True
        self._apply_collapsed_state()
        self._navigate(0)
        self.show()
