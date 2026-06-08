import sys
import os
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Ensure directories exist
for d in ['database', 'receipts', 'backups', 'documents', 'assets']:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from models.database import init_db, migrate_db

main_win = None
login_win = None


def on_login_success(user):
    global main_win, login_win
    try:
        from ui.main_window import MainWindow
        main_win = MainWindow(user)
        main_win.show()
        # Hide login only after main window is successfully shown
        if login_win:
            login_win.hide()
            login_win.close()
    except Exception as e:
        tb = traceback.format_exc()
        QMessageBox.critical(
            None,
            'Erreur de démarrage',
            f'Impossible d\'ouvrir la fenêtre principale :\n\n{e}\n\n{tb}'
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Le Schéma SGS v4')
    app.setApplicationVersion('4.0.0')

    icon_path = os.path.join(BASE_DIR, 'assets', 'school_logo.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    try:
        init_db()
        migrate_db()
    except Exception as e:
        QMessageBox.critical(None, 'Erreur base de données', str(e))
        sys.exit(1)

    from ui.login_window import LoginWindow
    login_win = LoginWindow(on_login_success)
    login_win.show()

    sys.exit(app.exec())
