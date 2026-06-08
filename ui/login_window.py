import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QFrame, QGraphicsOpacityEffect, QApplication)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QColor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'school_logo.png')


class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setWindowTitle('Le Schéma — Connexion')
        from PySide6.QtWidgets import QApplication
        _scr = QApplication.primaryScreen()
        if _scr:
            _a = _scr.availableGeometry()
            _w = min(960, int(_a.width()  * 0.92))
            _h = min(620, int(_a.height() * 0.88))
            self.setFixedSize(_w, _h)
            self.move(_a.x() + (_a.width() - _w) // 2,
                      _a.y() + (_a.height() - _h) // 2)
        else:
            self.setFixedSize(960, 620)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._drag_pos = None
        self._setup_ui()
        self._animate_in()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def _setup_ui(self):
        self.setStyleSheet('QWidget { font-family: "Segoe UI", Inter, Arial, sans-serif; }')

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left panel — visual brand ────────────────────────────────
        left = QFrame()
        left.setFixedWidth(440)
        left.setStyleSheet('''
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #4F46E5, stop:0.5 #7C3AED, stop:1 #6D28D9);
            }
        ''')
        ll = QVBoxLayout(left)
        ll.setContentsMargins(50, 50, 50, 50)
        ll.setSpacing(0)

        # Close / drag button top right
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet('''
            QPushButton { background: rgba(255,255,255,0.15); color: white;
                border: none; border-radius: 14px; font-size: 12px; }
            QPushButton:hover { background: rgba(255,255,255,0.3); }
        ''')
        close_btn.clicked.connect(sys.exit)
        top_bar.addWidget(close_btn)
        ll.addLayout(top_bar)
        ll.addStretch()

        # Logo
        logo_lbl = QLabel()
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH).scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet('background: transparent;')

        school_lbl = QLabel('Le Schéma')
        school_lbl.setAlignment(Qt.AlignCenter)
        school_lbl.setStyleSheet('color: white; font-size: 32px; font-weight: 800; background: transparent; letter-spacing: 1px;')

        motto_lbl = QLabel('Innover · Créer · Exceller')
        motto_lbl.setAlignment(Qt.AlignCenter)
        motto_lbl.setStyleSheet('color: rgba(255,255,255,0.7); font-size: 14px; background: transparent; letter-spacing: 2px;')

        # Feature pills
        pills_row = QHBoxLayout()
        pills_row.setSpacing(8)
        pills_row.setAlignment(Qt.AlignCenter)
        for pill_text in ['🎓 Élèves', '💳 Paiements', '📊 Rapports']:
            pill = QLabel(pill_text)
            pill.setStyleSheet('''
                color: rgba(255,255,255,0.85); background: rgba(255,255,255,0.15);
                border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: 600;
            ''')
            pills_row.addWidget(pill)

        ll.addWidget(logo_lbl)
        ll.addSpacing(16)
        ll.addWidget(school_lbl)
        ll.addSpacing(8)
        ll.addWidget(motto_lbl)
        ll.addSpacing(28)
        ll.addLayout(pills_row)
        ll.addStretch()

        version = QLabel('v1.0.0 · 2025/2026')
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet('color: rgba(255,255,255,0.4); font-size: 10px; background: transparent;')
        ll.addWidget(version)

        # ── Right panel — form ───────────────────────────────────────
        right = QFrame()
        right.setStyleSheet('QFrame { background: #FFFFFF; }')
        rl = QVBoxLayout(right)
        rl.setContentsMargins(60, 0, 60, 0)
        rl.setAlignment(Qt.AlignCenter)

        welcome = QLabel('Bon retour 👋')
        welcome.setStyleSheet('color: #1A1D2E; font-size: 26px; font-weight: 800; background: transparent;')

        subtitle = QLabel('Connectez-vous à votre espace de travail')
        subtitle.setStyleSheet('color: #6B7280; font-size: 13px; background: transparent;')

        def field_label(text):
            l = QLabel(text)
            l.setStyleSheet('color: #374151; font-size: 12px; font-weight: 600; background: transparent;')
            return l

        INPUT = '''
            QLineEdit {
                background: #F9FAFB; border: 1.5px solid #E5E7EB;
                border-radius: 10px; color: #1A1D2E;
                padding: 12px 15px; font-size: 14px;
            }
            QLineEdit:focus { border-color: #4F46E5; background: #FAFAFF; }
            QLineEdit:hover { border-color: #A5B4FC; }
        '''

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('admin')
        self.username_input.setFixedHeight(48)
        self.username_input.setStyleSheet(INPUT)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('••••••••')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(48)
        self.password_input.setStyleSheet(INPUT)
        self.password_input.returnPressed.connect(self._do_login)

        self.remember_cb = QCheckBox('Se souvenir de moi')
        self.remember_cb.setStyleSheet('''
            QCheckBox { color: #6B7280; font-size: 12px; background: transparent; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
                border: 1.5px solid #D1D5DB; background: white; }
            QCheckBox::indicator:checked { background: #4F46E5; border-color: #4F46E5; }
        ''')

        self.login_btn = QPushButton('Se connecter →')
        self.login_btn.setFixedHeight(50)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #4F46E5, stop:1 #7C3AED);
                color: white; border: none; border-radius: 10px;
                font-size: 15px; font-weight: 700; letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #4338CA, stop:1 #6D28D9);
            }
            QPushButton:pressed { background: #3730A3; }
        ''')
        self.login_btn.clicked.connect(self._do_login)

        self.error_label = QLabel('')
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet('''
            color: #EF4444; font-size: 12px; background: #FEE2E2;
            border-radius: 8px; padding: 8px; background: transparent;
        ''')

        # Hint credentials
        hint_frame = QFrame()
        hint_frame.setStyleSheet('QFrame { background: #F9FAFB; border-radius: 10px; border: 1px solid #EAEDF3; }')
        hl = QVBoxLayout(hint_frame)
        hl.setContentsMargins(14, 10, 14, 10)
        hl.setSpacing(3)
        for text, style in [
            ('Identifiants par défaut:', 'color:#6B7280; font-size:11px; font-weight:700; background:transparent;'),
            ('admin / admin123  ·  comptable / compta123', 'color:#9CA3AF; font-size:11px; background:transparent;'),
        ]:
            lbl = QLabel(text); lbl.setStyleSheet(style)
            hl.addWidget(lbl)

        rl.addStretch()
        rl.addWidget(welcome)
        rl.addSpacing(4)
        rl.addWidget(subtitle)
        rl.addSpacing(32)
        rl.addWidget(field_label('Nom d\'utilisateur'))
        rl.addSpacing(6)
        rl.addWidget(self.username_input)
        rl.addSpacing(16)
        rl.addWidget(field_label('Mot de passe'))
        rl.addSpacing(6)
        rl.addWidget(self.password_input)
        rl.addSpacing(12)
        rl.addWidget(self.remember_cb)
        rl.addSpacing(20)
        rl.addWidget(self.login_btn)
        rl.addSpacing(8)
        rl.addWidget(self.error_label)
        rl.addStretch()
        rl.addWidget(hint_frame)
        rl.addSpacing(24)

        root.addWidget(left)
        root.addWidget(right, 1)

        self.eff = QGraphicsOpacityEffect(right)
        right.setGraphicsEffect(self.eff)
        self.eff.setOpacity(0)

    def _animate_in(self):
        anim = QPropertyAnimation(self.eff, b'opacity', self)
        anim.setDuration(600)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        QTimer.singleShot(80, anim.start)
        self._anim = anim

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            self.error_label.setText('⚠  Veuillez remplir tous les champs')
            return
        from models.database import get_session, User
        session = get_session()
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        user = session.query(User).filter_by(username=username, password=pw_hash, active=True).first()
        session.close()
        if user:
            self.error_label.setText('')
            self.on_login_success(user)
        else:
            self.error_label.setText('✕  Identifiants incorrects. Réessayez.')
            self.password_input.clear()
            self._shake()

    def _shake(self):
        orig = self.pos()
        for i, dx in enumerate([8,-8,6,-6,4,-4,2,-2,0]):
            QTimer.singleShot(i * 35, lambda x=dx: self.move(orig.x()+x, orig.y()))
