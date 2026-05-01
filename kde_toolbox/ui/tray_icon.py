from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PyQt6.QtGui import QIcon, QAction, QPalette, QColor, QPainter
from PyQt6.QtCore import Qt, QSize

from kde_toolbox.kde.service import KdeService, DisplayServer


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.kde_service = KdeService()
        self._setup_icon()
        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _setup_icon(self):
        pixmap = QIcon.fromTheme("preferences-system").pixmap(22, 22)
        if pixmap.isNull():
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap(22, 22)
            pixmap.fill(QColor(52, 101, 164))
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "KT")
            painter.end()
        self.setIcon(QIcon(pixmap))

    def _setup_menu(self):
        menu = QMenu()

        self.action_show = QAction("显示主窗口", self)
        self.action_show.triggered.connect(lambda: self.parent().show())
        menu.addAction(self.action_show)

        menu.addSeparator()

        self.action_kwin = QAction("重启 KWin", self)
        self.action_kwin.triggered.connect(self._restart_kwin)
        menu.addAction(self.action_kwin)

        self.action_plasma = QAction("重启 Plasma Shell", self)
        self.action_plasma.triggered.connect(self._restart_plasma)
        menu.addAction(self.action_plasma)

        menu.addSeparator()

        self.action_quit = QAction("退出", self)
        self.action_quit.triggered.connect(lambda: self.parent().close())
        menu.addAction(self.action_quit)

        self.setContextMenu(menu)
        self.setToolTip("KDE Toolbox")

    def _restart_kwin(self):
        success, msg = self.kde_service.restart_kwin()
        self._show_notification("KDE Toolbox", msg)

    def _restart_plasma(self):
        success, msg = self.kde_service.restart_plasmashell()
        self._show_notification("KDE Toolbox", msg)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.parent().show()
            self.parent().activateWindow()

    def _show_notification(self, title: str, message: str):
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
