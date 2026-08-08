import os
import sys
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from models.file import FileModel


def get_base_path() -> str:
    """Returns the root resource directory (handles both dev and PyInstaller environments)."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    icon_path = os.path.join(get_base_path(), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    engine = QQmlApplicationEngine()

    model = FileModel()
    engine.rootContext().setContextProperty("fileModel", model)

    # Dynamically resolve import path for dev and frozen executable
    base_path = get_base_path()
    engine.addImportPath(base_path)

    engine.loadFromModule("Renamer", "Main")
    if not engine.rootObjects():
        sys.exit(-1)

    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
