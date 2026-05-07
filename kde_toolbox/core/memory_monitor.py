import logging
import psutil
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


class MemoryMonitorThread(QThread):
    memory_warning = pyqtSignal(float)
    memory_critical = pyqtSignal(float)

    def __init__(self, threshold_warning: float = 85.0, threshold_critical: float = 95.0, check_interval: int = 10):
        super().__init__()
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.check_interval = check_interval
        self._running = True

    def run(self):
        logger.info(f"Memory monitor started (warning: {self.threshold_warning}%, critical: {self.threshold_critical}%)")

        while self._running:
            try:
                memory = psutil.virtual_memory()
                memory_percent = memory.percent

                if memory_percent >= self.threshold_critical:
                    logger.warning(f"Memory usage critical: {memory_percent:.1f}%")
                    self.memory_critical.emit(memory_percent)
                elif memory_percent >= self.threshold_warning:
                    logger.info(f"Memory usage warning: {memory_percent:.1f}%")
                    self.memory_warning.emit(memory_percent)

                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
                time.sleep(self.check_interval)

    def stop(self):
        self._running = False
        self.wait()


class MemoryMonitor:
    def __init__(self, threshold_warning: float = 85.0, threshold_critical: float = 95.0):
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.monitor_thread = None
        self._warning_callback = None
        self._critical_callback = None

    def set_callbacks(self, warning_callback=None, critical_callback=None):
        self._warning_callback = warning_callback
        self._critical_callback = critical_callback

    def start(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            return

        self.monitor_thread = MemoryMonitorThread(
            threshold_warning=self.threshold_warning,
            threshold_critical=self.threshold_critical
        )

        if self._warning_callback:
            self.monitor_thread.memory_warning.connect(self._warning_callback)
        if self._critical_callback:
            self.monitor_thread.memory_critical.connect(self._critical_callback)

        self.monitor_thread.start()
        logger.info("Memory monitor started")

    def stop(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread = None
            logger.info("Memory monitor stopped")

    def get_memory_usage(self) -> tuple[float, float, float]:
        memory = psutil.virtual_memory()
        return memory.percent, memory.used / (1024**3), memory.total / (1024**3)

    def is_available(self) -> bool:
        try:
            psutil.virtual_memory()
            return True
        except Exception:
            return False