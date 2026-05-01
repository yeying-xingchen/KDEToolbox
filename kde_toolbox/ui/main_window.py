from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QMessageBox, QStatusBar, QFrame, QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

import logging
import subprocess

from kde_toolbox.kde.service import KdeService, DisplayServer
from kde_toolbox.core.config import AppConfig, ScheduledTask
from kde_toolbox.core.config import is_auto_start_enabled, apply_auto_start_setting
from kde_toolbox.core.scheduler import SchedulerThread
from kde_toolbox.ui.tray_icon import TrayIcon

STYLE_SHEET = """
QWidget {
    font-family: "Noto Sans", "Cantarell", "Noto Sans CJK SC", sans-serif;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    background-color: rgba(255,255,255,0.02);
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #b3e5fc;
    font-size: 13px;
}

QPushButton {
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    background-color: #1e88e5;
    color: #ffffff;
    font-weight: 600;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #2196f3;
}

QPushButton:pressed {
    background-color: #1565c0;
}

QPushButton.danger {
    background-color: #e53935;
}

QPushButton.danger:hover {
    background-color: #ef5350;
}

QPushButton.danger:pressed {
    background-color: #c62828;
}

QPushButton.secondary {
    background-color: #37474f;
}

QPushButton.secondary:hover {
    background-color: #455a64;
}

QPushButton.secondary:pressed {
    background-color: #263238;
}

QTableWidget {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    background-color: rgba(0,0,0,0.2);
    gridline-color: rgba(255,255,255,0.06);
    selection-background-color: #1e88e5;
    alternate-background-color: rgba(255,255,255,0.03);
}

QTableWidget::item {
    padding: 6px 4px;
    color: #e0e0e0;
}

QHeaderView::section {
    background-color: rgba(255,255,255,0.05);
    color: #b0bec5;
    padding: 8px 4px;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    font-weight: 600;
}

QComboBox, QLineEdit {
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 4px;
    padding: 6px 10px;
    background-color: rgba(0,0,0,0.3);
    color: #e0e0e0;
    min-height: 32px;
}

QComboBox:focus, QLineEdit:focus {
    border-color: #1e88e5;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
}

QStatusBar {
    background-color: rgba(0,0,0,0.4);
    border-top: 1px solid rgba(255,255,255,0.06);
    color: #90a4ae;
    font-size: 12px;
}

QMessageBox {
    background-color: #2d3748;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

QMessageBox QPushButton {
    min-height: 28px;
}
"""

ICON_MAP = {
    "preferences-system": "preferences-system",
    "refresh": "view-refresh",
    "restart": "system-reboot",
    "clear": "edit-clear",
    "add": "list-add",
    "remove": "list-remove",
    "info": "dialog-information",
    "warning": "dialog-warning",
    "error": "dialog-error",
}


class StatusLabel(QLabel):
    def __init__(self, label: str, value: str):
        super().__init__()
        self.label = label
        self.value = value
        self.update_display()

    def update_display(self, value: str = None):
        if value:
            self.value = value
        self.setText(f"<b style='color:#90a4ae'>{self.label}:</b> {self.value}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.kde_service = KdeService()
        self.config = AppConfig.load()
        self.scheduler_threads = []
        self.tray_icon = None

        self.setWindowTitle("KDE Toolbox")
        self.resize(850, 620)
        self.setMinimumSize(700, 500)

        self._setup_ui()
        self._setup_tray()
        self._load_system_info()
        self._load_tasks()

    def _setup_tray(self):
        if TrayIcon.isSystemTrayAvailable():
            self.tray_icon = TrayIcon(self)
            self.tray_icon.show()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(16, 16, 16, 16)

        main_layout.addWidget(self._create_system_info_group())
        main_layout.addWidget(self._create_quick_actions_group())
        main_layout.addWidget(self._create_settings_group())
        main_layout.addWidget(self._create_scheduler_group())

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("就绪")
        main_layout.addWidget(self.status_bar)

    def _create_system_info_group(self) -> QGroupBox:
        group = QGroupBox(" 系统信息")
        layout = QHBoxLayout(group)
        layout.setSpacing(20)

        info_panel = QFrame()
        info_layout = QVBoxLayout(info_panel)
        info_layout.setSpacing(8)

        self.info_labels = {}
        for key, label_text in [
            ("plasma", "Plasma 版本"),
            ("kwin", "KWin 版本"),
            ("display", "显示服务器"),
            ("compositor", "Compositor"),
        ]:
            lbl = StatusLabel(label_text, "-")
            self.info_labels[key] = lbl
            info_layout.addWidget(lbl)

        info_layout.addStretch()
        layout.addWidget(info_panel, stretch=1)

        action_panel = QFrame()
        action_layout = QVBoxLayout(action_panel)
        action_layout.setSpacing(8)

        btn_refresh = QPushButton("  刷新信息")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #37474f;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #455a64; }
            QPushButton:pressed { background-color: #263238; }
        """)
        btn_refresh.clicked.connect(self._load_system_info)
        action_layout.addWidget(btn_refresh)
        action_layout.addStretch()

        layout.addWidget(action_panel, stretch=0)

        return group

    def _create_quick_actions_group(self) -> QGroupBox:
        group = QGroupBox(" 快捷操作")
        layout = QHBoxLayout(group)
        layout.setSpacing(12)

        actions = [
            ("  重启 KWin", self._on_restart_kwin, "#1e88e5", "#2196f3"),
            ("  重启 Plasma", self._on_restart_plasma, "#1e88e5", "#2196f3"),
            ("  清除缓存", self._on_clear_cache, "#ff9800", "#ffa726"),
            ("  切换 Compositor", self._on_toggle_compositor, "#7b1fa2", "#9c27b0"),
        ]

        for text, callback, bg, hover in actions:
            btn = QPushButton(text)
            btn.setMinimumHeight(38)
            btn.setMinimumWidth(130)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: {hover}; }}
                QPushButton:pressed {{ background-color: {bg}; }}
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        return group

    def _create_settings_group(self) -> QGroupBox:
        group = QGroupBox(" 设置")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        self.chk_auto_start = QCheckBox("开机自启")
        self.chk_auto_start.setChecked(is_auto_start_enabled())
        self.chk_auto_start.stateChanged.connect(self._on_auto_start_changed)
        layout.addWidget(self.chk_auto_start)

        self.chk_minimize_to_tray = QCheckBox("最小化到系统托盘")
        self.chk_minimize_to_tray.setChecked(self.config.minimize_to_tray)
        self.chk_minimize_to_tray.stateChanged.connect(self._on_minimize_to_tray_changed)
        layout.addWidget(self.chk_minimize_to_tray)

        return group

    def _on_auto_start_changed(self, state):
        enabled = state == Qt.CheckState.Checked.value
        apply_auto_start_setting(enabled)
        self.config.auto_start = enabled
        self.config.save()
        status = "已启用" if enabled else "已禁用"
        self.status_bar.showMessage(f"开机自启{status}")

    def _on_minimize_to_tray_changed(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self.config.minimize_to_tray = enabled
        self.config.save()
        status = "已启用" if enabled else "已禁用"
        self.status_bar.showMessage(f"最小化到系统托盘{status}")

    def _create_scheduler_group(self) -> QGroupBox:
        group = QGroupBox(" 定时任务")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels([" 任务名", " 命令", " 调度时间", " 状态"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setMinimumHeight(160)
        layout.addWidget(self.task_table)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        ctrl_layout.addWidget(QLabel("命令:"))
        self.cmb_command = QComboBox()
        self.cmb_command.addItems(["kwin --replace", "plasmashell --replace", "自定义命令"])
        self.cmb_command.setFixedWidth(180)
        ctrl_layout.addWidget(self.cmb_command)

        self.le_custom_cmd = QLineEdit()
        self.le_custom_cmd.setPlaceholderText("输入自定义命令...")
        self.le_custom_cmd.setFixedWidth(200)
        self.le_custom_cmd.setVisible(False)
        ctrl_layout.addWidget(self.le_custom_cmd)

        self.cmb_command.currentTextChanged.connect(
            lambda t: self.le_custom_cmd.setVisible(t == "自定义命令")
        )

        ctrl_layout.addWidget(QLabel("调度:"))
        self.le_schedule = QLineEdit()
        self.le_schedule.setPlaceholderText("分 时 日 月 周")
        self.le_schedule.setText("30 2 * * *")
        self.le_schedule.setFixedWidth(150)
        ctrl_layout.addWidget(self.le_schedule)

        ctrl_layout.addStretch()

        btn_add = QPushButton("  添加")
        btn_add.setStyleSheet("""
            QPushButton { background-color: #2e7d32; border-radius: 6px; padding: 8px 16px; font-weight: 600; }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:pressed { background-color: #1b5e20; }
        """)
        btn_add.clicked.connect(self._on_add_task)
        ctrl_layout.addWidget(btn_add)

        btn_remove = QPushButton("  删除")
        btn_remove.setStyleSheet("""
            QPushButton { background-color: #e53935; border-radius: 6px; padding: 8px 16px; font-weight: 600; }
            QPushButton:hover { background-color: #ef5350; }
            QPushButton:pressed { background-color: #c62828; }
        """)
        btn_remove.clicked.connect(self._on_remove_task)
        ctrl_layout.addWidget(btn_remove)

        layout.addLayout(ctrl_layout)

        return group

    def _load_system_info(self):
        self.info_labels["plasma"].update_display(self.kde_service.get_plasma_version())
        self.info_labels["kwin"].update_display(self.kde_service.get_kwin_version())

        ds = self.kde_service.display_server
        self.info_labels["display"].update_display(ds.value.upper())

        comp = self.kde_service.get_compositor_active()
        status = "运行中" if comp else "已暂停"
        self.info_labels["compositor"].update_display(status)

        self.status_bar.showMessage("系统信息已刷新")

    def _load_tasks(self):
        self.task_table.setRowCount(0)
        for i, task_data in enumerate(self.config.tasks):
            self.task_table.insertRow(i)
            self.task_table.setItem(i, 0, QTableWidgetItem(task_data.get("name", "")))
            self.task_table.setItem(i, 1, QTableWidgetItem(task_data.get("command", "")))
            self.task_table.setItem(i, 2, QTableWidgetItem(task_data.get("schedule", "")))
            status = "已启用" if task_data.get("enabled", True) else "已禁用"
            item = QTableWidgetItem(status)
            if task_data.get("enabled", True):
                item.setForeground(Qt.GlobalColor.green)
            else:
                item.setForeground(Qt.GlobalColor.gray)
            self.task_table.setItem(i, 3, item)

        for task_data in self.config.tasks:
            if task_data.get("enabled", True):
                self._start_scheduler(task_data)

    def _on_restart_kwin(self):
        success, msg = self.kde_service.restart_kwin()
        self._show_status(msg, success)

    def _on_restart_plasma(self):
        success, msg = self.kde_service.restart_plasmashell()
        self._show_status(msg, success)

    def _on_clear_cache(self):
        success, msg = self.kde_service.clear_cache_and_restart()
        self._show_status(msg, success)

    def _on_toggle_compositor(self):
        current = self.kde_service.get_compositor_active()
        success, msg = self.kde_service.toggle_compositor(not current)
        self._show_status(msg, success)
        self._load_system_info()

    def _on_add_task(self):
        cmd = self.cmb_command.currentText()
        if cmd == "自定义命令":
            cmd = self.le_custom_cmd.text().strip()
            if not cmd:
                self._show_status("请输入自定义命令", False)
                return

        schedule = self.le_schedule.text().strip()
        if not schedule:
            self._show_status("请输入调度时间", False)
            return

        name = f"Task_{len(self.config.tasks) + 1}"
        task = ScheduledTask(id=name, name=name, command=cmd, schedule=schedule)
        self.config.tasks.append(task.__dict__)
        self.config.save()

        self._load_tasks()
        self._show_status(f"任务 {name} 已添加", True)

    def _on_remove_task(self):
        row = self.task_table.currentRow()
        if row < 0:
            self._show_status("请先选择要删除的任务", False)
            return

        task_name = self.task_table.item(row, 0).text()
        self.config.tasks = [t for t in self.config.tasks if t.get("name") != task_name]
        self.config.save()

        for t in self.scheduler_threads:
            if t.task_name == task_name:
                t.stop()
        self.scheduler_threads = [t for t in self.scheduler_threads if t.task_name != task_name]

        self._load_tasks()
        self._show_status(f"任务 {task_name} 已删除", True)

    def _start_scheduler(self, task_data: dict):
        def execute_task():
            try:
                subprocess.run(task_data["command"], shell=True, timeout=30)
            except Exception as e:
                logging.getLogger(__name__).error(f"Task execution failed: {e}")

        thread = SchedulerThread(task_data["name"], task_data["schedule"], execute_task)
        thread.task_triggered.connect(lambda name: self._on_task_triggered(name))
        thread.start()
        self.scheduler_threads.append(thread)

    def _on_task_triggered(self, task_name: str):
        self.status_bar.showMessage(f"任务已执行: {task_name}")

    def _show_status(self, message: str, success: bool):
        self.status_bar.showMessage(message)
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("KDE Toolbox" if success else "错误")
        msg_box.setText(message)
        if success:
            msg_box.setIcon(QMessageBox.Icon.Information)
        else:
            msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.exec()

    def closeEvent(self, event):
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.status_bar.showMessage("已隐藏到系统托盘")
        else:
            for thread in self.scheduler_threads:
                thread.stop()
            event.accept()
