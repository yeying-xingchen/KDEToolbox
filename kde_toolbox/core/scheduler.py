import logging
import threading
import schedule
import time
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


class SchedulerThread(QThread):
    task_triggered = pyqtSignal(str)

    def __init__(self, task_name: str, schedule_str: str, callback):
        super().__init__()
        self.task_name = task_name
        self.schedule_str = schedule_str
        self.callback = callback
        self._running = True

    def run(self):
        def job():
            logger.info(f"Triggering task: {self.task_name}")
            self.task_triggered.emit(self.task_name)
            try:
                self.callback()
            except Exception as e:
                logger.error(f"Task {self.task_name} failed: {e}")

        try:
            minute, hour, day, month, day_of_week = self._parse_cron(self.schedule_str)

            if minute != "*" and hour != "*" and day == "*" and month == "*" and day_of_week == "*":
                schedule.every().day.at(f"{int(hour):02d}:{int(minute):02d}").do(job)
            elif minute != "*" and hour == "*" and day == "*" and month == "*" and day_of_week == "*":
                schedule.every().hour.at(f":{int(minute):02d}").do(job)
            elif minute == "*" and hour == "*" and day == "*" and month == "*" and day_of_week == "*":
                schedule.every().minute.do(job)
            else:
                logger.warning(f"Unsupported cron: {self.schedule_str}")
                return

            logger.info(f"Scheduler started for task: {self.task_name} (cron: {self.schedule_str})")

            while self._running:
                schedule.run_pending()
                time.sleep(1)

        except Exception as e:
            logger.error(f"Scheduler error for {self.task_name}: {e}")

    def stop(self):
        self._running = False
        self.wait()

    def _parse_cron(self, cron_str: str) -> tuple:
        parts = cron_str.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_str}")
        minute, hour, day, month, day_of_week = parts
        return minute, hour, day, month, day_of_week
