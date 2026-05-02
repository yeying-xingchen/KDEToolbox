# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-01

### Added

- GitHub Actions 自动构建 (Ubuntu/macOS/Windows, Python 3.10-3.12)
- DEB 打包和自动发布功能
- 开机自启功能（XDG 标准）
- 设置界面（开机自启、最小化到托盘开关）
- 初始 KDE Toolbox 核心功能
  - 系统信息查看（Plasma/KWin 版本、显示服务器、Compositor 状态）
  - 快捷操作（重启 KWin/Plasma、清除缓存、切换 Compositor）
  - 定时任务管理（Cron 表达式、任务调度）
  - 系统托盘集成（最小化到托盘、托盘菜单）
- README 文档

### Changed

- 使用 subprocess 替代 os.system() 提升安全性
- 简化 DEB 打包流程，移除 setuptools 依赖
- 优化工作流配置，修复 YAML 语法错误

### Fixed

- 关闭窗口时隐藏到托盘而非退出
- DEB 打包失败问题
- GitHub Actions YAML 语法错误

[Unreleased]: https://github.com/yeyingxingchen/KDEToolbox/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yeyingxingchen/KDEToolbox/releases/tag/v0.1.0
