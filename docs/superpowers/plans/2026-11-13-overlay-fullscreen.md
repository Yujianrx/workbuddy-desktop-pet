# Overlay Fullscreen Implementation Plan

**Goal:** 独立置顶、全屏自动收起与更短胶囊。
**Architecture:** 新增只读Windows全屏探测模块；Controller分离用户显隐与自动隐藏，统一恢复；Settings、菜单和设置页同步三项偏好。
**Tech Stack:** Python3.12、PySide6、Win32 ctypes、PyInstaller、Inno Setup。
**Spec:** docs/plans/2026-11-13-overlay-fullscreen-design.md

## Review Focus
- 全屏结束不恢复用户主动隐藏的人物／整体；保留窗口模式和位置。
- 普通最大化、桌面、自身窗口不误判；检测失败不闪现。
- 置顶切换保留可见状态和焦点，不中断接入授权。
- 全屏期间消息仍处理，动画解码暂停，更新提示不弹出。
- 缩短胶囊后长标题省略、完整提示及长积分仍可读。

- [x] 合成全屏判定、配置迁移、显隐恢复与短胶囊测试。
- [x] Windows探测、Controller隐藏策略、置顶和UI入口实现。
- [x] 原生全屏／置顶与100%／150%布局验证，全量回归和冻结程序检查。
- [ ] 更新0.7.3文档和安装包，Windows CI通过后发布及保留偏好的本机升级。

按用户已确认方案在本会话执行；每项先验证失败再实现，不改动任何角色GIF或授权。
