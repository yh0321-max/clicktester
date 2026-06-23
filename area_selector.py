"""
可拖动/可调整大小的纯灰色区域设置窗口。
用户通过移动和调整此窗口来定义测试区域，确认后窗口保持显示。
"""

import tkinter as tk
from typing import Callable


class AreaSelector(tk.Toplevel):
    """一个可自由移动、调整大小的纯灰色窗口。

    确认后窗口不消失，变为「已锁定」状态继续显示在屏幕上，
    作为测试区域的边界参考。

    用法:
        win = AreaSelector(root)
        win.set_callback(lambda rect: print(rect))  # 确认时回调
        win.set_cancel_callback(lambda: print("cancelled"))  # 取消时回调
    """

    def __init__(self, master):
        super().__init__(master)
        self.result: tuple[int, int, int, int] | None = None
        self._confirmed = False
        self._on_confirm_cb: Callable | None = None
        self._on_cancel_cb: Callable | None = None

        # ── 窗口外观 ──
        self.title("测试区域 - 拖拽边框调整大小和位置")
        self.configure(bg="#888888")
        self.attributes("-topmost", True)

        # 默认尺寸和居中位置
        w, h = 400, 300
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(80, 60)

        # ── 提示内容 ──
        self._info_frame = tk.Frame(self, bg="#888888")
        self._info_frame.pack(expand=True, fill=tk.BOTH)

        self._hint1 = tk.Label(
            self._info_frame,
            text="↕ 拖拽边框调整窗口大小",
            fg="white", bg="#888888",
            font=("Microsoft YaHei", 10),
        )
        self._hint1.pack(pady=(35, 4))

        self._hint2 = tk.Label(
            self._info_frame,
            text="↔ 拖拽标题栏移动窗口位置",
            fg="white", bg="#888888",
            font=("Microsoft YaHei", 10),
        )
        self._hint2.pack(pady=4)

        self._hint3 = tk.Label(
            self._info_frame,
            text="将此窗口覆盖在目标区域上方，\n然后点击「确认」",
            fg="#CCCCCC", bg="#888888",
            font=("Microsoft YaHei", 9),
            justify=tk.CENTER,
        )
        self._hint3.pack(pady=4)

        # ── 底部按钮 ──
        self._btn_frame = tk.Frame(self, bg="#888888")
        self._btn_frame.pack(fill=tk.X, pady=(0, 12))

        self._btn_confirm = tk.Button(
            self._btn_frame,
            text="✓  确认",
            command=self._on_confirm,
            bg="#4CAF50", fg="white",
            activebackground="#45a049",
            relief=tk.FLAT, padx=24, pady=3,
            font=("Microsoft YaHei", 10),
        )
        self._btn_confirm.pack(side=tk.RIGHT, padx=(0, 16))

        self._btn_cancel = tk.Button(
            self._btn_frame,
            text="✗  取消",
            command=self._on_cancel,
            bg="#f44336", fg="white",
            activebackground="#da190b",
            relief=tk.FLAT, padx=24, pady=3,
            font=("Microsoft YaHei", 10),
        )
        self._btn_cancel.pack(side=tk.RIGHT, padx=(0, 8))

        # 已确认状态标签（初始隐藏）
        self._confirmed_label = tk.Label(
            self,
            text="✓ 已确认",
            fg="#4CAF50", bg="#888888",
            font=("Microsoft YaHei", 11, "bold"),
        )

        # X 关闭按钮 → 取消
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ── 回调设置 ─────────────────────────────────────────

    def set_callback(self, cb: Callable):
        """设置确认回调，参数为 (x1, y1, x2, y2) 坐标元组。"""
        self._on_confirm_cb = cb

    def set_cancel_callback(self, cb: Callable):
        """设置取消回调。"""
        self._on_cancel_cb = cb

    # ── 事件处理 ─────────────────────────────────────────

    def _on_confirm(self):
        """确认：锁定窗口状态，记录坐标，保持窗口显示。"""
        self._confirmed = True
        self._update_rect()

        # 切换到锁定状态 UI
        self._switch_to_confirmed_ui()

        # 通知回调
        if self._on_confirm_cb:
            self._on_confirm_cb(self.result)

    def _on_cancel(self):
        """取消：关闭窗口。"""
        self.result = None
        if self._on_cancel_cb:
            self._on_cancel_cb()
        self.destroy()

    def _update_rect(self):
        """更新保存的矩形坐标。"""
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()
        self.result = (x, y, x + w, y + h)

    def _switch_to_confirmed_ui(self):
        """将 UI 切换到「已确认」状态。"""
        self.title("测试区域 - ✓ 已确认")
        # 隐藏操作按钮和提示
        self._btn_frame.pack_forget()
        self._info_frame.pack_forget()
        # 显示已确认标签
        self._confirmed_label.pack(expand=True)

    # ── 公共方法 ─────────────────────────────────────────

    def refresh_rect(self):
        """刷新保存的矩形坐标（窗口可能被用户移动过）。"""
        if self._confirmed:
            self._update_rect()

    @property
    def is_confirmed(self) -> bool:
        return self._confirmed

    # ── 测试模式 ─────────────────────────────────────────

    def set_ghost_mode(self, enabled: bool):
        """测试模式下窗口保持纯灰色不透明，仅改变背景色作为视觉提示。

        点击不会被穿透——pynput 在 OS 层面捕获点击用于计数，
        窗口本身正常接收鼠标事件。
        """
        if not self._confirmed:
            return

        if enabled:
            # 测试中：稍微变亮以示区别
            self.configure(bg="#AAAAAA")
            self._confirmed_label.configure(bg="#AAAAAA")
        else:
            # 恢复
            self.configure(bg="#888888")
            self._confirmed_label.configure(bg="#888888")
