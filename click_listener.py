"""
全局鼠标点击监听器模块。
使用 pynput 监听全局鼠标事件，通过线程安全队列与主线程通信。
"""

import queue
from pynput import mouse


class ClickListener:
    """全局鼠标左键点击监听器。

    在后台线程中运行 pynput.Listener，将每次点击的 (x, y) 坐标
    放入线程安全的 queue.Queue 中，供主线程轮询消费。
    """

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._listener: mouse.Listener | None = None
        self._running = False

    def _on_click(self, x, y, button, pressed):
        """pynput 回调：仅记录左键按下事件。"""
        if button == mouse.Button.left and pressed:
            self._queue.put((x, y))
        # 返回 True 继续监听，False 会停止监听器
        return True

    def start(self):
        """启动后台监听线程。"""
        if self._running:
            return
        self._running = True
        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """停止后台监听线程。"""
        self._running = False
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def drain_clicks(self) -> list[tuple[int, int]]:
        """非阻塞地取出队列中所有未处理的点击坐标。

        Returns:
            list of (x, y) 坐标元组列表。
        """
        clicks = []
        while True:
            try:
                clicks.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return clicks

    @property
    def is_running(self) -> bool:
        return self._running


def is_inside_rect(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    """判断坐标 (x, y) 是否在矩形区域内。

    Args:
        x, y: 鼠标坐标。
        rect: (x1, y1, x2, y2)，两个对角点，自动规范化为左上-右下。

    Returns:
        True 如果在矩形内部。
    """
    x1, y1, x2, y2 = rect
    left, right = (x1, x2) if x1 <= x2 else (x2, x1)
    top, bottom = (y1, y2) if y1 <= y2 else (y2, y1)
    return left <= x <= right and top <= y <= bottom
