# Project Change Log

This append-only file records user-requested changes made to this project.

## 2026-07-15 11:11:46+08:00

- Request: 整理项目架构并编写更新日志
- Status: Completed
- Changes:
  - 将共享核心、PyQt5 客户端和 Flask 应用迁移到标准 src/xyzrender_workstation 包结构
  - 新增统一工作区路径解析，保留 app.py、run_desktop.py 和 build_html.py 兼容入口
  - 新增 pyproject.toml、.gitignore 和架构文档，并将乱码 README 重写为 UTF-8 中文说明
  - 归档旧前端片段和 Flask 日志，清除旧源码路径缓存，更新测试与 PyInstaller 配置
- Files:
  - `src/xyzrender_workstation/paths.py`
  - `src/xyzrender_workstation/core/render_service.py`
  - `src/xyzrender_workstation/desktop/main_window.py`
  - `src/xyzrender_workstation/web/app.py`
  - `app.py`
  - `run_desktop.py`
  - `build_html.py`
  - `scripts/build_html.py`
  - `pyproject.toml`
  - `.gitignore`
  - `docs/ARCHITECTURE.md`
  - `README.md`
  - `pytest.ini`
  - `xyzrender_workstation.spec`
  - `tests/test_core.py`
  - `tests/test_desktop.py`
  - `tests/test_multiwfn.py`
  - `references/legacy/script_backup.js`
- Verification:
  - QT_QPA_PLATFORM=offscreen python -m pytest -q: 13 passed
  - python build_html.py: 成功生成包内 Web 模板
  - pyinstaller --noconfirm --clean xyzrender_workstation.spec: 构建成功
  - 打包 EXE 离屏运行 8 秒且 MOLECULES/TEMP/FIGURE 均存在

## 2026-07-15 11:23:13+08:00

- Request: 修复 Web 启动并按原 Web 功能补齐 xyzrender 桌面能力
- Status: Completed
- Changes:
  - 关闭 Flask 默认 watchdog 自动重载，增加 health 接口、host/port/debug 参数和 Windows 启动脚本
  - 从 xyzrender 0.3.1 的公开 API 动态生成 148 项加载、渲染和 GIF 完整参数目录
  - 新增桌面完整参数选项卡，支持搜索、分组、类型解析以及参数集 JSON 导入导出
  - 强化 GIF 参数校验，保留旧 Web 高亮、区域、标签、TS 和 CLI 专有选项的 legacy 回退
  - 新增功能矩阵、回归测试并重建 PyInstaller onedir 包
- Files:
  - `src/xyzrender_workstation/web/app.py`
  - `start_web.bat`
  - `src/xyzrender_workstation/core/option_schema.py`
  - `src/xyzrender_workstation/core/render_service.py`
  - `src/xyzrender_workstation/core/__init__.py`
  - `src/xyzrender_workstation/desktop/parameter_panel.py`
  - `src/xyzrender_workstation/desktop/main_window.py`
  - `tests/test_core.py`
  - `tests/test_desktop.py`
  - `tests/test_flask_compat.py`
  - `docs/FEATURE_MATRIX.md`
  - `README.md`
  - `xyzrender_workstation.spec`
- Verification:
  - QT_QPA_PLATFORM=offscreen python -m pytest -q: 15 passed
  - 真实 HTTP /api/health 返回 200 且 watchdog 重启次数为 0
  - 高亮、区域、索引、键轮廓和手工 TS 键组合 SVG 渲染成功
  - pyinstaller --noconfirm --clean xyzrender_workstation.spec: 构建成功
  - 打包 EXE 离屏运行 8 秒并正确创建运行目录

## 2026-07-15 11:28:54+08:00

- Request: 修复打包 EXE 缺少 xyzgraph.data
- Status: Completed
- Changes:
  - PyInstaller spec 增加 xyzgraph 全子模块和数据资源收集
  - 新增 EXE --self-test，验证 xyzgraph.data JSON、分子加载和最小 SVG 渲染链
  - 新增源码自检回归测试并重建 onedir 包
- Files:
  - `xyzrender_workstation.spec`
  - `run_desktop.py`
  - `tests/test_desktop.py`
- Verification:
  - QT_QPA_PLATFORM=offscreen python -m pytest -q: 16 passed
  - XYZRender_Workstation.exe --self-test: 退出码 0
  - 打包目录包含 xyzgraph/data 的 4 个必需 JSON 文件
  - 普通 EXE 离屏启动 6 秒正常运行

## 2026-07-15 11:47:25+08:00

- Request: 将 PyQt5 桌面布局、配色和 xyzrender 功能对齐 HTML 并保留 Multiwfn
- Status: Completed
- Changes:
  - 按实际 HTML 页面重构为顶部状态栏和文件库、参数中心、预览输出三栏布局
  - 对齐浅色/深色主题令牌、胶囊页签、风格卡片、按钮、字号与状态设计
  - 将 xyzrender 功能整理为基本、显示、着色、表面、叠加、GIF、晶体和高级页签
  - 新增交互画布/渲染结果双视图与 TEMP/FIGURE 文件画廊及保存清理流程
  - 保留并整合 Multiwfn ESP、MO、IGMH、电荷、取消、进度与日志功能
  - 更新测试、功能矩阵、README 和 PyInstaller 收集规则并重建包
- Files:
  - `src/xyzrender_workstation/desktop/main_window.py`
  - `src/xyzrender_workstation/desktop/file_gallery.py`
  - `tests/test_desktop.py`
  - `docs/FEATURE_MATRIX.md`
  - `README.md`
  - `xyzrender_workstation.spec`
- Verification:
  - 本地浏览器实测 HTML 布局、配色和控件尺寸并完成真实 Windows Qt 截图比对
  - QT_QPA_PLATFORM=offscreen python -m pytest -q: 16 passed
  - 叠加、高亮、区域、晶体和 TEMP 到 FIGURE 流程回归通过
  - pyinstaller --noconfirm --clean xyzrender_workstation.spec: 构建成功
  - 打包 EXE --self-test 退出码 0，普通启动 7 秒正常

## 2026-07-15 12:21:57+08:00

- Request: 归档桌面端代码并从当前项目入口移除
- Status: Completed
- Changes:
  - 将 PyQt5 桌面源码、入口、打包配置、桌面依赖和桌面测试移动到 old/desktop/
  - 在 .gitignore 中忽略 old/，避免归档桌面代码进入版本控制
  - 移除 pyproject.toml 的桌面命令与桌面 extras，并更新 README/架构文档为 Web 当前维护范围
  - 更新源码项目根目录识别逻辑，不再依赖已归档的 run_desktop.py
- Files:
  - `old/desktop`
  - `.gitignore`
  - `pyproject.toml`
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `src/xyzrender_workstation/paths.py`
- Verification:
  - python -m pytest -q：14 passed；归档目录与忽略规则检查通过

## 2026-07-15 14:34:23+08:00

- Request: 优化 Web 工作站的信息架构、视觉层级与响应式布局
- Status: Completed
- Changes:
  - 将页面重组为输入结构、调整与渲染、审阅与导出三阶段工作流，并强化预览区的主视觉地位
  - 将渲染操作移至常驻控制区，折叠低频预设与图稿历史，减少首屏噪音并修复切换标签后操作消失的问题
  - 采用克制的科研工作台视觉语言，统一排版、色彩、间距、状态和控件层级，并移除外部 Google Fonts 依赖
  - 补齐 1180、920、680 像素断点下的双栏与单栏响应式布局
- Files:
  - `scripts/build_html.py`
  - `src/xyzrender_workstation/web/templates/index.html`
  - `src/xyzrender_workstation/web/static/pretty_lattice_refresh.css`
- Verification:
  - python -m pytest -q：14 passed
  - python -m py_compile scripts/build_html.py：通过
  - 浏览器验收：1280、900、640 像素布局可用，关键折叠交互与固定渲染区正常，控制台无错误

## 2026-07-15 15:34:25+08:00

- Request: 新增 pywebview 桌面入口、PyInstaller onedir 构建和 Inno Setup 安装器
- Status: Completed
- Changes:
  - 在 desktop 目录实现 pywebview 启动器、本地 Flask 生命周期、首次运行示例复制、冻结程序自检与 Windows 多进程兼容
  - 将运行数据和日志迁移到用户可写目录，安装资源保持只读，并记录依赖版本、请求异常和渲染失败
  - 新增精简的 PyInstaller onedir spec、桌面依赖清单、PowerShell 构建脚本、Inno Setup 安装脚本和构建文档
  - 补充桌面验收测试，覆盖四类输入、四种输出、异常文件、离线资源、上传保存以及升级卸载数据保留
- Files:
  - `.gitignore`
  - `README.md`
  - `pyproject.toml`
  - `desktop/__init__.py`
  - `desktop/__main__.py`
  - `desktop/launcher.py`
  - `desktop/requirements-desktop.txt`
  - `desktop/xyzrender_workstation.spec`
  - `desktop/build.ps1`
  - `desktop/installer.iss`
  - `desktop/BUILD.md`
  - `src/xyzrender_workstation/__init__.py`
  - `src/xyzrender_workstation/paths.py`
  - `src/xyzrender_workstation/web/app.py`
  - `src/xyzrender_workstation/core/render_service.py`
  - `tests/test_desktop_acceptance.py`
  - `dist/XYZRender Workstation/`
  - `dist/installer/XYZRender-Workstation-0.2.0-Setup.exe`
- Verification:
  - python -m pytest -q：25 passed
  - 最终冻结 EXE 自检退出码 0：HTML、XYZ/PDB/MOL/SDF、SVG/PNG/PDF/GIF、上传、保存、错误文件存活全部通过
  - GUI 冷启动：pywebview 事件循环正常，首页、CSS 与主要 Flask 接口返回 200
  - Program Files 实装验收：运行前后安装目录文件数不变，用户数据写入外部目录
  - 覆盖升级和卸载验收：用户图稿哈希不变，卸载后图稿与日志保留
  - Inno Setup 6.7.3 编译成功；安装器版本 0.2.0，84.0 MB，SHA256 69FC555E2CC3D8417DD570E09607B38323399B0C1EB7112379D2C2C455F58A82
