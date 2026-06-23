"""
ClickTester 主界面模块。
提供区域选择、时长配置、测试控制、实时状态显示和历史记录。
"""

import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from area_selector import AreaSelector
from click_listener import ClickListener, is_inside_rect

# 历史记录文件路径
_RECORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clicktest_records.json")


class ClickTester:
    """鼠标点击测试工具主应用。"""

    # ── 初始化 ──────────────────────────────────────────────

    def __init__(self, root: tk.Tk):
        self._root = root
        self._root.title("ClickTester - 鼠标点击测试工具")
        self._root.resizable(False, False)
        self._root.attributes("-topmost", True)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 状态
        self._area: tuple[int, int, int, int] | None = None
        self._area_window: AreaSelector | None = None  # 区域设置窗口引用
        self._listener = ClickListener()
        self._running = False
        self._in_delay = False         # 是否在启动延时阶段
        self._elapsed_ms = 0           # 已过毫秒
        self._duration_ms = 10_000     # 默认 10 秒
        self._delay_ms = 0             # 启动延时毫秒
        self._click_count = 0
        self._tick_job_id: str | None = None
        self._records: list[dict] = []  # 历史记录
        self._history_win: tk.Toplevel | None = None  # 历史窗口单例

        self._load_records()
        self._build_ui()
        self._center_window()

    # ── UI 构建 ─────────────────────────────────────────────

    def _build_ui(self):
        """构建主界面布局。"""
        pad = {"padx": 12, "pady": 6}

        # ── 标题 ──
        title = ttk.Label(
            self._root,
            text="🖱️  ClickTester - 鼠标点击测试工具",
            font=("Microsoft YaHei", 12, "bold"),
        )
        title.pack(pady=(12, 4))

        # ── 测试区域 ──
        area_frame = ttk.LabelFrame(self._root, text="测试区域", padding=10)
        area_frame.pack(fill=tk.X, **pad)

        self._btn_select = ttk.Button(
            area_frame, text="📐 设置区域", command=self._select_area
        )
        self._btn_select.grid(row=0, column=0, padx=(0, 10))

        self._area_label = ttk.Label(
            area_frame, text="未设置", foreground="gray"
        )
        self._area_label.grid(row=0, column=1, sticky=tk.W)

        self._area_size_label = ttk.Label(
            area_frame, text="", foreground="#666"
        )
        self._area_size_label.grid(row=0, column=2, padx=(20, 0))

        # ── 测试配置 ──
        config_frame = ttk.LabelFrame(self._root, text="测试配置", padding=10)
        config_frame.pack(fill=tk.X, **pad)

        ttk.Label(config_frame, text="测试时长:").grid(
            row=0, column=0, sticky=tk.W
        )

        self._duration_var = tk.StringVar(value="10")
        self._duration_spin = ttk.Spinbox(
            config_frame,
            from_=1,
            to=300,
            textvariable=self._duration_var,
            width=6,
            validate="focusout",
            validatecommand=(self._root.register(self._validate_duration), "%P"),
        )
        self._duration_spin.grid(row=0, column=1, padx=(4, 2))

        ttk.Label(config_frame, text="秒").grid(row=0, column=2, sticky=tk.W)

        # 启动延时
        ttk.Label(config_frame, text="启动延时:").grid(
            row=1, column=0, sticky=tk.W, pady=(6, 0)
        )
        self._delay_var = tk.StringVar(value="0")
        self._delay_spin = ttk.Spinbox(
            config_frame,
            from_=0,
            to=10,
            textvariable=self._delay_var,
            width=6,
        )
        self._delay_spin.grid(row=1, column=1, padx=(4, 2), pady=(6, 0))
        ttk.Label(config_frame, text="秒").grid(row=1, column=2, sticky=tk.W, pady=(6, 0))

        self._btn_start = ttk.Button(
            config_frame, text="▶ 开始测试", command=self._start_test
        )
        self._btn_start.grid(row=0, column=3, padx=(20, 4), rowspan=2)

        self._btn_stop = ttk.Button(
            config_frame, text="⏹ 停止", command=self._stop_test, state=tk.DISABLED
        )
        self._btn_stop.grid(row=0, column=4, padx=(0, 4), rowspan=2)

        self._btn_reset = ttk.Button(
            config_frame, text="↺ 重置", command=self._reset
        )
        self._btn_reset.grid(row=0, column=5, rowspan=2)

        # ── 实时状态 ──
        status_frame = ttk.LabelFrame(self._root, text="实时状态", padding=10)
        status_frame.pack(fill=tk.X, **pad)

        # 倒计时进度条
        self._progress = ttk.Progressbar(
            status_frame, mode="determinate", maximum=100
        )
        self._progress.grid(row=0, column=0, columnspan=3, sticky=tk.EW, pady=(0, 8))
        status_frame.columnconfigure(0, weight=1)

        # 剩余时间
        ttk.Label(status_frame, text="⏱ 剩余时间:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 20)
        )
        self._time_label = ttk.Label(
            status_frame, text="0.0 秒", font=("Consolas", 11)
        )
        self._time_label.grid(row=1, column=1, sticky=tk.W)

        # 点击数
        ttk.Label(status_frame, text="🖱 点击数:").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 20)
        )
        self._click_label = ttk.Label(
            status_frame, text="0", font=("Consolas", 14, "bold"), foreground="#0078D4"
        )
        self._click_label.grid(row=2, column=1, sticky=tk.W)

        # CPS
        ttk.Label(status_frame, text="⚡ CPS:").grid(
            row=3, column=0, sticky=tk.W, padx=(0, 20)
        )
        self._cps_label = ttk.Label(
            status_frame, text="0.0", font=("Consolas", 11), foreground="#107C10"
        )
        self._cps_label.grid(row=3, column=1, sticky=tk.W)

        # CPS 水平
        ttk.Label(status_frame, text="📊 水平:").grid(
            row=4, column=0, sticky=tk.W, padx=(0, 20)
        )
        self._level_label = ttk.Label(
            status_frame, text="--", font=("Microsoft YaHei", 11, "bold")
        )
        self._level_label.grid(row=4, column=1, sticky=tk.W)

        # ── 底部按钮 ──
        bottom_frame = ttk.Frame(self._root)
        bottom_frame.pack(fill=tk.X, **pad)

        self._btn_history = ttk.Button(
            bottom_frame, text="📋 历史记录", command=self._show_history
        )
        self._btn_history.pack(side=tk.LEFT)

        hint = ttk.Label(
            bottom_frame,
            text="提示: 点击「设置区域」弹出窗口 → 拖拽/调整大小 → 确认 → 开始测试",
            foreground="gray",
        )
        hint.pack(side=tk.RIGHT)

    # ── 区域选择 ────────────────────────────────────────────

    def _select_area(self):
        """弹出半透明灰色窗口，用户移动/调整窗口大小来定义测试区域。
        确认后窗口保持显示，不消失。"""
        # 如果已有旧窗口，先关闭
        if self._area_window is not None:
            self._area_window.destroy()
            self._area_window = None

        win = AreaSelector(self._root)
        win.set_callback(self._on_area_confirmed)
        win.set_cancel_callback(self._on_area_cancelled)
        self._area_window = win

    def _on_area_confirmed(self, rect: tuple[int, int, int, int]):
        """区域窗口确认后的回调。"""
        self._area = rect
        x1, y1, x2, y2 = rect
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        self._area_label.config(
            text=f"({x1}, {y1}) → ({x2}, {y2})",
            foreground="black",
        )
        self._area_size_label.config(text=f"[{w} × {h} px]")

    def _on_area_cancelled(self):
        """区域窗口被取消/关闭的回调。"""
        if self._area_window is not None:
            self._area_window = None

        # 如果正在测试中，自动终止测试
        if self._running:
            self._running = False
            if self._tick_job_id is not None:
                self._root.after_cancel(self._tick_job_id)
                self._tick_job_id = None
            self._listener.stop()
            self._area = None
            self._elapsed_ms = 0
            self._click_count = 0
            self._set_ui_state(running=False)
            self._update_display(remaining_ms=self._duration_ms, clicks=0)
            self._area_label.config(text="未设置", foreground="gray")
            self._area_size_label.config(text="")
            messagebox.showwarning("测试终止", "测试区域窗口已关闭，测试已终止。")
        else:
            # 非测试状态下关闭窗口，清除区域（防止未确认就开始测试）
            self._area = None
            self._area_label.config(text="未设置", foreground="gray")
            self._area_size_label.config(text="")

    # ── 测试控制 ────────────────────────────────────────────

    def _validate_duration(self, value: str) -> bool:
        """校验时长输入。"""
        if value == "":
            return True
        try:
            v = float(value)
            return 0 < v <= 300
        except ValueError:
            return False

    def _start_test(self):
        """开始测试（先处理延时，再启动实际测试）。"""
        # 前置检查
        if self._area is None:
            messagebox.showwarning("未设置区域", "请先点击「设置区域」定义测试区域并确认。")
            return

        # 刷新区域坐标（窗口可能被移动过）
        if self._area_window is not None:
            self._area_window.refresh_rect()
            if self._area_window.result:
                self._area = self._area_window.result

        try:
            duration_s = float(self._duration_var.get())
            delay_s = float(self._delay_var.get())
        except ValueError:
            messagebox.showwarning("无效输入", "请输入有效的数字。")
            return

        if duration_s <= 0 or duration_s > 300:
            messagebox.showwarning("无效时长", "测试时长范围为 1-300 秒。")
            return

        if delay_s < 0 or delay_s > 10:
            messagebox.showwarning("无效延时", "启动延时范围为 0-10 秒。")
            return

        # 初始化状态
        self._duration_ms = int(duration_s * 1000)
        self._delay_ms = int(delay_s * 1000)
        self._elapsed_ms = 0
        self._click_count = 0
        self._running = True

        # 更新 UI 状态
        self._set_ui_state(running=True)

        if self._delay_ms > 0:
            # 先进入延时倒计时
            self._in_delay = True
            self._time_label.config(text=f"{delay_s:.1f} 秒")
            self._pre_tick()
        else:
            # 无延时，直接开始
            self._start_actual_test()

    def _pre_tick(self):
        """启动延时倒计时（每 100ms 更新一次）。"""
        if not self._running:
            return

        self._delay_ms -= 100

        if self._delay_ms <= 0:
            # 延时结束，开始实际测试
            self._in_delay = False
            self._start_actual_test()
            return

        # 更新延时显示
        remaining = self._delay_ms / 1000.0
        self._time_label.config(text=f"倒计时 {remaining:.1f} 秒")
        self._progress["value"] = 0

        self._tick_job_id = self._root.after(100, self._pre_tick)

    def _start_actual_test(self):
        """实际开始测试（延时结束后调用）。"""
        # 区域窗口进入测试模式
        if self._area_window is not None:
            self._area_window.set_ghost_mode(True)

        # 启动点击监听
        self._listener.start()

        # 开始计时循环
        self._tick()

    def _stop_test(self):
        """手动停止测试（延时阶段也可停止）。"""
        if not self._running:
            return
        # 如果在延时阶段，直接取消
        if self._in_delay:
            self._running = False
            self._in_delay = False
            if self._tick_job_id is not None:
                self._root.after_cancel(self._tick_job_id)
                self._tick_job_id = None
            self._set_ui_state(running=False)
            self._update_display(remaining_ms=self._duration_ms, clicks=0)
            self._time_label.config(text="0.0 秒")
            messagebox.showinfo("已取消", "测试已取消。")
            return
        self._finish_test(manual=True)

    def _finish_test(self, manual: bool = False):
        """结束测试，停止监听，显示结果。"""
        self._running = False
        self._in_delay = False

        # 取消定时器
        if self._tick_job_id is not None:
            self._root.after_cancel(self._tick_job_id)
            self._tick_job_id = None

        # 停止监听并收集最后剩余点击
        self._listener.stop()
        self._drain_clicks()

        # 恢复区域窗口正常状态
        if self._area_window is not None:
            self._area_window.set_ghost_mode(False)

        # 更新 UI
        self._set_ui_state(running=False)

        # 显示结果
        effective_s = self._elapsed_ms / 1000.0
        cps = self._click_count / effective_s if effective_s > 0 else 0.0

        # 保存记录
        level_text, _ = self._get_cps_level(cps)
        self._save_record(effective_s, cps, level_text, self._delay_ms / 1000.0)

        result_msg = (
            f"测试完成！\n\n"
            f"🖱 总点击数: {self._click_count}\n"
            f"⏱ 测试时长: {effective_s:.1f} 秒\n"
            f"⚡ 平均 CPS: {cps:.2f}\n"
            f"📊 水平: {level_text}"
        )
        if manual:
            result_msg = "（手动停止）\n" + result_msg

        messagebox.showinfo("测试结果", result_msg)

        # 重置显示
        self._update_display(0, 0)

    def _reset(self):
        """重置所有状态。"""
        if self._running:
            self._finish_test(manual=True)

        # 关闭区域窗口
        if self._area_window is not None:
            self._area_window.destroy()
            self._area_window = None

        self._area = None
        self._elapsed_ms = 0
        self._click_count = 0
        self._area_label.config(text="未设置", foreground="gray")
        self._area_size_label.config(text="")
        self._duration_var.set("10")
        self._update_display(remaining_ms=self._duration_ms, clicks=0)
        self._btn_stop.config(state=tk.DISABLED)

    # ── 定时更新循环 ────────────────────────────────────────

    def _tick(self):
        """每 100ms 执行一次：收集点击、更新时间、刷新显示。"""
        if not self._running:
            return

        # 排空点击队列，过滤区域
        self._drain_clicks()

        # 更新时间
        self._elapsed_ms += 100
        remaining_ms = max(0, self._duration_ms - self._elapsed_ms)

        # 更新显示
        self._update_display(remaining_ms, self._click_count)

        # 检查是否到时
        if remaining_ms <= 0:
            self._finish_test(manual=False)
            return

        # 调度下一次
        self._tick_job_id = self._root.after(100, self._tick)

    def _drain_clicks(self):
        """从监听器队列取出点击并过滤区域。"""
        if self._area is None:
            return
        clicks = self._listener.drain_clicks()
        for x, y in clicks:
            if is_inside_rect(x, y, self._area):
                self._click_count += 1

    def _update_display(self, remaining_ms: int, clicks: int):
        """刷新所有实时状态显示。"""
        remaining_s = remaining_ms / 1000.0
        elapsed_s = self._elapsed_ms / 1000.0
        cps = clicks / elapsed_s if elapsed_s > 0 else 0.0
        progress_pct = (
            (1 - remaining_ms / self._duration_ms) * 100
            if self._duration_ms > 0
            else 0
        )

        self._time_label.config(text=f"{remaining_s:.1f} 秒")
        self._click_label.config(text=str(clicks))
        self._cps_label.config(text=f"{cps:.1f}")
        self._progress["value"] = progress_pct

        # 更新 CPS 水平
        level_text, level_color = self._get_cps_level(cps)
        self._level_label.config(text=level_text, foreground=level_color)

    # ── UI 状态切换 ─────────────────────────────────────────

    def _set_ui_state(self, running: bool):
        """根据运行状态启用/禁用控件。"""
        if running:
            self._btn_select.config(state=tk.DISABLED)
            self._btn_start.config(state=tk.DISABLED)
            self._btn_stop.config(state=tk.NORMAL)
            self._btn_reset.config(state=tk.DISABLED)
            self._duration_spin.config(state=tk.DISABLED)
            self._delay_spin.config(state=tk.DISABLED)
        else:
            self._btn_select.config(state=tk.NORMAL)
            self._btn_start.config(state=tk.NORMAL)
            self._btn_stop.config(state=tk.DISABLED)
            self._btn_reset.config(state=tk.NORMAL)
            self._duration_spin.config(state=tk.NORMAL)
            self._delay_spin.config(state=tk.NORMAL)

    # ── 辅助方法 ────────────────────────────────────────────

    def _center_window(self):
        """将主窗口居中于屏幕。"""
        self._root.update_idletasks()
        w = self._root.winfo_width()
        h = self._root.winfo_height()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self._root.geometry(f"+{x}+{y}")

    # ── 历史记录 ────────────────────────────────────────────

    @staticmethod
    def _get_cps_level(cps: float) -> tuple[str, str]:
        """根据 CPS 返回 (水平名称, 颜色)。"""
        if cps < 3:
            return "🟢 入门", "#228B22"
        elif cps < 5:
            return "🟡 普通", "#B8860B"
        elif cps < 7:
            return "🟠 熟练", "#D2691E"
        elif cps < 10:
            return "🔴 优秀", "#DC143C"
        elif cps < 15:
            return "🟣 高手", "#8B008B"
        else:
            return "⭐ 大神", "#FF4500"

    def _save_record(self, effective_s: float, cps: float, level: str = "", delay_s: float = 0):
        """保存本次测试记录。"""
        area_str = ""
        area_size_str = ""
        if self._area:
            x1, y1, x2, y2 = self._area
            area_str = f"({x1}, {y1}) → ({x2}, {y2})"
            area_size_str = f"{abs(x2-x1)} × {abs(y2-y1)} px"

        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": round(effective_s, 1),
            "delay": round(delay_s, 1),
            "clicks": self._click_count,
            "cps": round(cps, 2),
            "level": level,
            "area": area_str,
            "area_size": area_size_str,
        }
        self._records.append(record)
        self._save_records_to_file()

    def _load_records(self):
        """从文件加载历史记录。"""
        try:
            if os.path.exists(_RECORDS_FILE):
                with open(_RECORDS_FILE, "r", encoding="utf-8") as f:
                    self._records = json.load(f)
        except Exception:
            self._records = []

    def _save_records_to_file(self):
        """将历史记录写入文件。"""
        try:
            with open(_RECORDS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _show_history(self):
        """打开历史记录窗口（单例），按时间倒序展示。"""
        # 如果已有窗口，聚焦并返回
        if self._history_win is not None and self._history_win.winfo_exists():
            self._history_win.lift()
            self._history_win.focus_force()
            return

        win = tk.Toplevel(self._root)
        self._history_win = win
        win.title("📋 历史记录")
        win.protocol("WM_DELETE_WINDOW", lambda: self._on_history_close(win))
        win.geometry("680x380")
        win.resizable(True, True)
        win.attributes("-topmost", True)

        # Treeview 表格
        columns = ("time", "duration", "clicks", "cps", "level", "area")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=12)

        tree.heading("time", text="测试时间")
        tree.heading("duration", text="时长 (秒)")
        tree.heading("clicks", text="点击数")
        tree.heading("cps", text="CPS")
        tree.heading("level", text="水平")
        tree.heading("area", text="测试区域")

        tree.column("time", width=140, anchor=tk.CENTER)
        tree.column("duration", width=70, anchor=tk.CENTER)
        tree.column("clicks", width=60, anchor=tk.CENTER)
        tree.column("cps", width=60, anchor=tk.CENTER)
        tree.column("level", width=80, anchor=tk.CENTER)
        tree.column("area", width=240, anchor=tk.W)

        # 滚动条
        scrollbar = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 按时间倒序插入数据
        for rec in sorted(self._records, key=lambda r: r["time"], reverse=True):
            tree.insert("", tk.END, values=(
                rec["time"],
                rec["duration"],
                rec["clicks"],
                rec["cps"],
                rec.get("level", ""),
                rec.get("area", ""),
            ))

        # 底部按钮
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        ttk.Label(
            btn_frame,
            text=f"共 {len(self._records)} 条记录",
            foreground="gray",
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="清空记录",
            command=lambda: self._clear_records(tree, win),
        ).pack(side=tk.RIGHT)

    def _clear_records(self, tree: ttk.Treeview, win: tk.Toplevel):
        """清空所有历史记录。"""
        if not messagebox.askyesno("确认清空", "确定要清空所有历史记录吗？"):
            return
        self._records.clear()
        self._save_records_to_file()
        # 更新表格
        for item in tree.get_children():
            tree.delete(item)
        self._history_win = None
        win.destroy()
        messagebox.showinfo("已清空", "历史记录已清空。")

    def _on_history_close(self, win: tk.Toplevel):
        """历史窗口关闭时的清理。"""
        self._history_win = None
        win.destroy()

    def _on_close(self):
        """窗口关闭时清理资源。"""
        if self._running:
            self._listener.stop()
        if self._area_window is not None:
            self._area_window.destroy()
            self._area_window = None
        self._save_records_to_file()
        self._root.destroy()
