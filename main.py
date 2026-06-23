"""
ClickTester 入口模块。
一款在用户自定义屏幕区域内统计鼠标点击次数的桌面工具。
"""

import sys
import ctypes
import tkinter as tk
from click_tester import ClickTester


def _set_dpi_awareness():
    """在 Windows 上设置 DPI 感知，确保 pynput 与 tkinter 坐标一致。"""
    if sys.platform == "win32":
        try:
            # Windows 10 1703+
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            # 2 = PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                # 旧版 Windows
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass  # 忽略，用户可能在高 DPI 下遇到坐标偏移


def main():
    """应用程序入口。"""
    _set_dpi_awareness()

    root = tk.Tk()
    ClickTester(root)  # pyright: ignore[reportUnusedCallResult]
    root.mainloop()


if __name__ == "__main__":
    main()
