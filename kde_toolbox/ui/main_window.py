from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import logging
import subprocess

from kde_toolbox.kde.service import KdeService, DisplayServer
from kde_toolbox.core.config import AppConfig, ScheduledTask
from kde_toolbox.core.scheduler import SchedulerThread
from kde_toolbox.ui.tray_icon import TrayIcon


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.kde_service = KdeService()
        self.config = AppConfig.load()
        self.scheduler_threads = []
        self.tray_icon = None

        self.setWindowTitle("KDE Toolbox")
        self.resize(800, 600)

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
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        main_layout.addWidget(self._create_system_info_group())
        main_layout.addWidget(self._create_quick_actions_group())
        main_layout.addWidget(self._create_scheduler_group())

    def _create_system_info_group(self) -> QGroupBox:
        group = QGroupBox("系统信息")
        layout = QVBoxLayout(group)

        self.lbl_plasma = QLabel("Plasma 版本: -")
        self.lbl_kwin = QLabel("KWin 版本: -")
        self.lbl_display = QLabel("显示服务器: -")
        self.lbl_compositor = QLabel("Compositor: -")

        for lbl in [self.lbl_plasma, self.lbl_kwin, self.lbl_display, self.lbl_compositor]:
            layout.addWidget(lbl)

        btn_refresh = QPushButton("刷新信息")
        btn_refresh.clicked.connect(self._load_system_info)
        layout.addWidget(btn_refresh)

        return group

    def _create_quick_actions_group(self) -> QGroupBox:
        group = QGroupBox("快捷操作")
        layout = QHBoxLayout(group)

        actions = [
            ("重启 KWin", self._on_restart_kwin),
            ("重启 Plasma", self._on_restart_plasma),
            ("清除缓存", self._on_clear_cache),
            ("切换 Compositor", self._on_toggle_compositor),
        ]

        for text, callback in actions:
            btn = QPushButton(text)
            btn.setMinimumHeight(36)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        return group

    def _create_scheduler_group(self) -> QGroupBox:
        group = QGroupBox("定时任务")
        layout = QVBoxLayout(group)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["任务名", "命令", "调度时间", "状态"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.task_table)

        ctrl_layout = QHBoxLayout()

        self.cmb_command = QComboBox()
        self.cmb_command.addItems(["kwin --replace", "plasmashell --replace", "自定义命令"])
        self.cmb_command.setFixedWidth(200)
        ctrl_layout.addWidget(QLabel("命令:"))
        ctrl_layout.addWidget(self.cmb_command)

        self.le_custom_cmd = QLineEdit()
        self.le_custom_cmd.setPlaceholderText("自定义命令...")
        self.le_custom_cmd.setFixedWidth(200)
        self.le_custom_cmd.setVisible(False)
        ctrl_layout.addWidget(self.le_custom_cmd)

        self.cmb_command.currentTextChanged.connect(lambda t: self.le_custom_cmd.setVisible(t == "自定义命令"))

        ctrl_layout.addWidget(QLabel("时间:"))
        self.le_schedule = QLineEdit()
        self.le_schedule.setPlaceholderText("cron 格式 (分 时 日 月 周)")
        self.le_schedule.setText("30 2 * * *")
        self.le_schedule.setFixedWidth(200)
        ctrl_layout.addWidget(self.le_schedule)

        ctrl_layout.addStretch()

        btn_add = QPushButton("添加任务")
        btn_add.clicked.connect(self._on_add_task)
        ctrl_layout.addWidget(btn_add)

        btn_remove = QPushButton("删除任务")
        btn_remove.clicked.connect(self._on_remove_task)
        ctrl_layout.addWidget(btn_remove)

        layout.addLayout(ctrl_layout)

        return group

    def _load_system_info(self):
        self.lbl_plasma.setText(f"Plasma 版本: {self.kde_service.get_plasma_version()}")
        self.lbl_kwin.setText(f"KWin 版本: {self.kde_service.get_kwin_version()}")

        ds = self.kde_service.display_server
        self.lbl_display.setText(f"显示服务器: {ds.value.upper()}")

        comp = self.kde_service.get_compositor_active()
        self.lbl_compositor.setText(f"Compositor: {'运行中' if comp else '已暂停'}")

    def _load_tasks(self):
        self.task_table.setRowCount(0)
        for i, task_data in enumerate(self.config.tasks):
            self.task_table.insertRow(i)
            self.task_table.setItem(i, 0, QTableWidgetItem(task_data.get("name", "")))
            self.task_table.setItem(i, 1, QTableWidgetItem(task_data.get("command", "")))
            self.task_table.setItem(i, 2, QTableWidgetItem(task_data.get("schedule", "")))
            status = "已启用" if task_data.get("enabled", True) else "已禁用"
            self.task_table.setItem(i, 3, QTableWidgetItem(status))

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
        self._show_status(f"任务已触发: {task_name}", True)

    def _show_status(self, message: str, success: bool):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("KDE Toolbox" if success else "错误")
        msg_box.setText(message)
        if success:
            msg_box.setIcon(QMessageBox.Icon.Information)
        else:
            msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.exec()

    def closeEvent(self, event):
        for thread in self.scheduler_threads:
            thread.stop()
        event.accept()
