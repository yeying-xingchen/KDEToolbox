import json
import logging
import os
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))) / "kde-toolbox"
CONFIG_FILE = CONFIG_DIR / "config.json"

LOG_DIR = Path(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))) / "kde-toolbox"
LOG_FILE = LOG_DIR / "kde-toolbox.log"

AUTOSTART_DIR = Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))) / "autostart"
AUTOSTART_DESKTOP_FILE = AUTOSTART_DIR / "kde-toolbox.desktop"


@dataclass
class ScheduledTask:
    id: str
    name: str
    command: str
    schedule: str
    enabled: bool = True
    last_run: Optional[str] = None


@dataclass
class AppConfig:
    auto_start: bool = False
    minimize_to_tray: bool = True
    confirm_before_action: bool = True
    tasks: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_FILE.exists():
            return cls()
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def is_auto_start_enabled() -> bool:
    return AUTOSTART_DESKTOP_FILE.exists()


def enable_auto_start() -> None:
    try:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        
        desktop_content = """[Desktop Entry]
Name=KDE Toolbox
GenericName=KDE System Toolbox
Comment=A toolbox for managing KDE services and tasks
Exec=kde-toolbox
Icon=preferences-system
Terminal=false
Type=Application
Categories=System;Settings;Qt;KDE;
X-GNOME-Autostart-enabled=true
"""
        with open(AUTOSTART_DESKTOP_FILE, 'w') as f:
            f.write(desktop_content)
        logger.info("Auto-start enabled")
    except Exception as e:
        logger.error(f"Failed to enable auto-start: {e}")


def disable_auto_start() -> None:
    try:
        if AUTOSTART_DESKTOP_FILE.exists():
            AUTOSTART_DESKTOP_FILE.unlink()
        logger.info("Auto-start disabled")
    except Exception as e:
        logger.error(f"Failed to disable auto-start: {e}")


def apply_auto_start_setting(enabled: bool) -> None:
    if enabled:
        enable_auto_start()
    else:
        disable_auto_start()
