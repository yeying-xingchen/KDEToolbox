# KDE Toolbox

一个基于 PyQt6 的 KDE 桌面工具箱，提供系统信息查看、快捷操作和定时任务管理功能。

## 功能

### 系统信息

- 查看 Plasma 和 KWin 版本
- 检测显示服务器（X11/Wayland）
- 监控 Compositor 运行状态

### 快捷操作

- 重启 KWin（仅限 X11）
- 重启 Plasma Shell
- 清除缓存并重启
- 切换 Compositor（启用/暂停）

### 定时任务

- 支持 Cron 表达式语法
- 自定义命令调度
- 任务启用/禁用管理
- 后台自动执行

### 系统托盘

- 最小化到系统托盘
- 托盘菜单快捷操作
- 双击恢复主窗口

## 安装

### 环境要求
- Python >= 3.10
- KDE Plasma 桌面环境
- PyQt6 >= 6.4.0

### 方式一：安装 DEB 包（推荐）

从 [Releases](https://github.com/yeying-xingchen/KDEToolbox/releases) 页面下载最新 `.deb` 文件，然后安装：

```bash
sudo dpkg -i kde-toolbox_*.deb
sudo apt-get install -f  # 修复依赖（如果需要）
```

### 方式二：使用 pip 安装

1. 克隆仓库
```bash
git clone https://github.com/yeying-xingchen/KDEToolbox.git
cd KDEToolbox
```

2. 使用 uv 安装
```bash
uv sync
uv pip install .
```

## 使用方法

### 启动应用

直接在终端运行：
```bash
kde-toolbox
```

### 查看系统信息

点击"刷新信息"按钮获取最新的系统信息。

### 执行快捷操作

1. 在"快捷操作"区域点击相应按钮
2. 确认操作提示
3. 等待操作完成

### 添加定时任务

1. 在"定时任务"区域选择命令
   - 选择预设命令（kwin --replace 或 plasmashell --replace）
   - 或选择"自定义命令"并输入命令
2. 设置 Cron 表达式（格式：分 时 日 月 周）
   - 示例：`30 2 * * *` 表示每天凌晨 2:30
   - 示例：`*/5 * * * *` 表示每 5 分钟
3. 点击"添加"按钮

### 系统托盘

- 关闭窗口时应用会隐藏到系统托盘
- 双击托盘图标恢复主窗口
- 右键托盘图标访问快捷菜单

## 项目结构

```
kde_toolbox/
├── core/              # 核心模块
│   ├── config.py      # 配置管理（使用 XDG 标准）
│   └── scheduler.py   # 定时任务调度器
├── kde/               # KDE 服务封装
│   └── service.py     # KDE 系统操作（重启、缓存等）
├── ui/                # 用户界面
│   ├── main_window.py # 主窗口
│   └── tray_icon.py   # 系统托盘图标
└── main.py            # 应用入口
```

## 配置

配置文件位于：
- Linux: `~/.config/kde-toolbox/config.json`
- 或使用 `XDG_CONFIG_HOME` 环境变量指定的路径

### 配置示例

```json
{
  "auto_start": false,
  "minimize_to_tray": true,
  "confirm_before_action": true,
  "tasks": [
    {
      "id": "Task_1",
      "name": "Task_1",
      "command": "kwin --replace",
      "schedule": "30 2 * * *",
      "enabled": true
    }
  ]
}
```

## 日志

日志文件位于：
- Linux: `~/.local/share/kde-toolbox/kde-toolbox.log`
- 或使用 `XDG_DATA_HOME` 环境变量指定的路径

## 开发

### 设置开发环境

```bash
uv sync --dev
```

### 运行开发版本

```bash
python -m kde_toolbox.main
```

## 注意事项

1. **KWin 重启**：仅在 X11 会话下可用，Wayland 不支持 `--replace` 参数

## 贡献

欢迎提交 Issue 和 Pull Request！

## 友情链接

[LINUX DO](https://linux.do/)

## 许可证

本项目采用 MIT 许可证。

## 致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 优秀的 Python Qt 绑定
- [schedule](https://github.com/dbader/schedule) - Python 定时任务库
- [psutil](https://github.com/giampaolo/psutil) - 系统和进程实用工具
