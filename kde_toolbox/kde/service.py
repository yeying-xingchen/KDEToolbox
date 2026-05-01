import logging
import subprocess
import os
import glob
import shutil
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class DisplayServer(Enum):
    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


class KdeService:
    def __init__(self):
        self._display_server = self._detect_display_server()

    def _detect_display_server(self) -> DisplayServer:
        xdg_session = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if xdg_session == "x11":
            return DisplayServer.X11
        elif xdg_session == "wayland":
            return DisplayServer.WAYLAND

        if os.environ.get("WAYLAND_DISPLAY"):
            return DisplayServer.WAYLAND
        if os.environ.get("DISPLAY"):
            return DisplayServer.X11

        return DisplayServer.UNKNOWN

    @property
    def display_server(self) -> DisplayServer:
        return self._display_server

    def get_plasma_version(self) -> str:
        try:
            result = subprocess.run(
                ["plasmashell", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split()[-1]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "Unknown"

    def get_kwin_version(self) -> str:
        try:
            if self._display_server == DisplayServer.X11:
                cmd = ["kwin_x11", "--version"]
            else:
                cmd = ["kwin_wayland", "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip().split()[-1]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "Unknown"

    def get_compositor_active(self) -> bool:
        try:
            import dbus
            bus = dbus.SessionBus()
            proxy = bus.get_object(
                "org.kde.KWin",
                "/org/kde/KWin/Compositor",
            )
            iface = dbus.Interface(proxy, "org.kde.kwin.Compositing")
            return iface.isActive()
        except Exception:
            return False

    def restart_kwin(self) -> tuple[bool, str]:
        try:
            if self._display_server == DisplayServer.X11:
                cmd = ["kwin_x11", "--replace"]
            else:
                return False, "Wayland: KWin cannot be restarted with --replace"

            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True, f"KWin (X11) 重启命令已发送: {' '.join(cmd)}"
        except Exception as e:
            logger.error(f"KWin restart failed: {e}")
            return False, f"KWin 重启失败: {e}"

    def restart_plasmashell(self) -> tuple[bool, str]:
        try:
            cmd = ["plasmashell", "--replace"]
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True, "Plasma Shell 重启命令已发送 (plasmashell --replace)"
        except Exception as e:
            logger.error(f"Plasma Shell restart failed: {e}")
            return False, f"Plasma Shell 重启失败: {e}"

    def clear_cache_and_restart(self) -> tuple[bool, str]:
        try:
            cache_base = Path(os.path.expanduser("~/.cache"))
            removed_count = 0
            
            for pattern in ["plasma*", "kioexec*"]:
                for path in glob.glob(str(cache_base / pattern)):
                    target = Path(path)
                    try:
                        if target.is_dir():
                            shutil.rmtree(target)
                        else:
                            target.unlink()
                        removed_count += 1
                        logger.info(f"Removed cache: {path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {path}: {e}")
            
            logger.info(f"Cleared {removed_count} cache files/directories")
            self.restart_plasmashell()
            return True, f"缓存已清除（{removed_count} 项），Plasma Shell 重启命令已发送"
        except Exception as e:
            return False, f"清除缓存失败: {e}"

    def toggle_compositor(self, enable: bool) -> tuple[bool, str]:
        try:
            import dbus
            bus = dbus.SessionBus()
            proxy = bus.get_object(
                "org.kde.KWin",
                "/org/kde/KWin/Compositor",
            )
            iface = dbus.Interface(proxy, "org.kde.kwin.Compositing")
            if enable:
                iface.resume()
            else:
                iface.suspend()
            status = "启用" if enable else "暂停"
            return True, f"Compositor 已{status}"
        except Exception as e:
            return False, f"Compositor 切换失败: {e}"
