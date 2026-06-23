# 🖱️ ClickTester - 鼠标点击速度测试工具

一款简洁的 Windows 桌面工具，在自定义屏幕区域内测试鼠标点击速度。

## ✨ 功能

- **可视化区域设置** — 弹出可拖动/调整大小的灰色窗口，直观定义测试区域
- **延时启动** — 支持 0-10 秒倒计时，给你准备时间
- **实时反馈** — 倒计时进度条、实时点击数、实时 CPS（每秒点击数）
- **水平评级** — 根据 CPS 自动评定：入门 / 普通 / 熟练 / 优秀 / 高手 / 大神
- **历史记录** — JSON 持久化保存，支持查看和清空
- **始终置顶** — 主窗口和测试区域窗口始终在前端

## 🎯 评级标准

| CPS 范围 | 等级 |
|----------|------|
| < 3 | 🟢 入门 |
| 3 – 5 | 🟡 普通 |
| 5 – 7 | 🟠 熟练 |
| 7 – 10 | 🔴 优秀 |
| 10 – 15 | 🟣 高手 |
| 15+ | ⭐ 大神 |

## 📦 安装

### 从源码运行

```bash
git clone https://github.com/yh0321-max/clicktester.git
cd clicktester
pip install -r requirements.txt
python main.py
```

### 打包为 exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ClickTester" main.py
# 输出在 dist\ClickTester.exe
```

## 🚀 使用方式

1. 点击 **📐 设置区域** → 弹出灰色窗口
2. 拖拽标题栏移动、拖拽边框调整大小，覆盖目标区域
3. 点击 **✓ 确认**（窗口保持显示）
4. 设置测试时长和启动延时
5. 点击 **▶ 开始测试** → 在选区内疯狂点击！
6. 查看结果和历史记录 📋

## 📥 下载

前往 [Releases](https://github.com/yh0321-max/clicktester/releases) 页面下载最新版 `ClickTester.exe`，无需安装 Python 即可运行。

## 🛠️ 技术栈

- **Python 3.10+**
- **Tkinter** — GUI 界面
- **pynput** — 全局鼠标事件监听
- **PyInstaller** — 打包为 Windows exe

## 📂 项目结构

```
clicktester/
├── main.py              # 程序入口
├── click_tester.py      # 主界面逻辑
├── area_selector.py     # 区域设置窗口
├── click_listener.py    # 鼠标监听器
├── requirements.txt     # Python 依赖
└── README.md
```

## 📄 License

MIT License
