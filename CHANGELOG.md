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

## 2026-07-15 15:47:45+08:00

- Request: Publish the current web application source and Windows installer to TiegenFang/xyzrender-webapp
- Status: Completed
- Changes:
  - Connected the local project to the existing public GitHub repository while preserving its main-branch history, then published the refactored Flask web application and reproducible desktop packaging sources.
  - Excluded generated builds, runtime output, reference projects, and third-party software from Git; removed obsolete generated previews and legacy flat-template files from the repository.
  - Updated README publishing guidance and created GitHub Release v0.2.0 with the Windows installer asset.
- Files:
  - `.gitignore`
  - `README.md`
  - `TEMP/.gitkeep`
  - `FIGURE/.gitkeep`
- Verification:
  - python -m pytest -q: 25 passed
  - Remote main matched local source commit 61042bc6382ecac74bb83af0de16fb0e2ab75a2e before the release-log follow-up commit
  - GitHub Release v0.2.0 asset uploaded: 88,111,234 bytes; SHA256 69FC555E2CC3D8417DD570E09607B38323399B0C1EB7112379D2C2C455F58A82

## 2026-07-15 16:14:18+08:00

- Request: Optimize the V1 web rotation workflow by merging live orientation control with the render preview.
- Status: Completed
- Changes:
  - Replaced the modal orientation page with an inline two-pane workspace: live molecular rotation on the left and rendered artwork on the right.
  - Ported quaternion arcball rotation, right-drag panning, wheel zoom, keyboard rotation, reset, PCA alignment, live axes, and orientation-matrix feedback from the reference desktop canvas.
  - Connected “apply orientation and render” to bake the current matrix into a rotated structure, reload the live canvas, and refresh the right-side result without double-applying the pose.
  - Added responsive V1 presentation styling, unified the visible V1 version label, and added a structural regression test.
- Files:
  - `scripts/build_html.py`
  - `src/xyzrender_workstation/web/app.py`
  - `src/xyzrender_workstation/web/static/pretty_lattice_refresh.css`
  - `src/xyzrender_workstation/web/templates/index.html`
  - `tests/test_flask_compat.py`
- Verification:
  - `python -m py_compile scripts\\build_html.py src\\xyzrender_workstation\\web\\app.py`
  - `python scripts\\build_html.py`
  - `python -m pytest tests\\test_flask_compat.py`: 4 passed
  - Browser at 1280x720: panes side by side with no overlap; molecule selection, drag rotation, matrix update, orientation bake, and SVG refresh passed; zero console errors

## 2026-07-15 16:33:20+08:00

- Request: 优化V1实时旋转画布风格并修正渲染预览居中缩放
- Status: Completed
- Changes:
  - 参考桌面端MolCanvas接入17套实时画布风格预设及下拉切换，覆盖背景、配色、渐变、键线、阴影与轮廓
  - 让SVG和位图预览按右侧容器自适应缩放、保持比例居中并充分利用横向空间
  - 补充V1页面结构回归断言并重新生成HTML模板
- Files:
  - `scripts/build_html.py`
  - `src/xyzrender_workstation/web/templates/index.html`
  - `src/xyzrender_workstation/web/static/pretty_lattice_refresh.css`
  - `tests/test_flask_compat.py`
- Verification:
  - python -m pytest: 26 passed
  - Browser check: style switching redraws the live canvas and generated SVG fills and centers in the render pane
  - git diff --check: passed

## 2026-07-15 16:40:54+08:00

- Request: 修复实时旋转画布误连键与风格背景残留
- Status: Completed
- Changes:
  - 为实时视角API增加PDB、MOL/SDF、MOL2、CIF显式键表读取，并对无键表格式使用保守共价半径推断
  - 前端改为仅绘制后端返回的键表，移除宽阈值全原子试连
  - 移除风格十字环装饰并在每帧重置Canvas绘制状态，避免旋转背景与残影
- Files:
  - `src/xyzrender_workstation/web/app.py`
  - `scripts/build_html.py`
  - `src/xyzrender_workstation/web/templates/index.html`
  - `tests/test_flask_compat.py`
- Verification:
  - python -m pytest: 27 passed
  - Browser check: c2c1im ring connectivity is correct and HoukPremium remains clean after X/Y/Z rotation
  - git diff --check: passed

## 2026-07-15 18:43:36+08:00

- Request: 实现 Multiwfn 离线任务包生成、CALC 回导和网页计算接口 V1
- Status: Completed
- Changes:
  - 新增 Multiwfn 2026.4.10 版本化模板，支持 MO、密度、ESP、NCI、IGMH、振动与六种电荷任务综合 ZIP
  - 新增安全回导、artifact 注册、结果校验、CALC 管理及受控渲染绑定
  - 在现有单页工作流新增计算标签页、结果回导和一键应用交互
  - 补充离线包、ZIP 安全、结果绑定和 Web API 自动化测试
- Files:
  - `src/xyzrender_workstation/core/multiwfn_offline.py`
  - `src/xyzrender_workstation/core/render_service.py`
  - `src/xyzrender_workstation/core/__init__.py`
  - `src/xyzrender_workstation/web/app.py`
  - `src/xyzrender_workstation/web/templates/index.html`
  - `tests/test_multiwfn_offline.py`
- Verification:
  - python -m pytest -q: 37 passed
  - python -m py_compile: passed
  - git diff --check: passed
  - In-app browser: compute tab visible, seven task controls present, no console errors
  - External Multiwfn execution not run: executable and wavefunction fixture unavailable

## 2026-07-15 19:05:00+08:00

- Request: 修正 Multiwfn 工作流，只生成外部计算与分析脚本，等待用户回传结果后再交给 xyzrender 绘制
- Status: Completed
- Changes:
  - 新增本地 Multiwfn.exe 路径设置，并将配置路径写入 Windows 分析任务启动脚本；应用本身不启动 Multiwfn
  - 新增从结构文件生成 Gaussian/ORCA 计算脚本 ZIP，支持泛函、基组、电荷、多重度、优化、频率、核心数与内存设置
  - Gaussian 脚本在用户外部运行后通过 formchk 产出 FCHK，ORCA 脚本通过 orca_2mkl 产出 Molden 波函数
  - 计算页调整为“工具路径—结构计算脚本—波函数分析脚本—结果回传”四阶段流程
  - 支持回传并识别 `.molden.input`，波函数进入 MOLECULES，Multiwfn 分析结果进入 CALC 后再绑定 xyzrender
  - 增加计算脚本、工具设置、Molden 回传与 Web API 回归测试
- Files:
  - `.gitignore`
  - `src/xyzrender_workstation/core/multiwfn_offline.py`
  - `src/xyzrender_workstation/core/__init__.py`
  - `src/xyzrender_workstation/web/app.py`
  - `src/xyzrender_workstation/web/templates/index.html`
  - `tests/test_multiwfn_offline.py`
- Verification:
  - python -m pytest -q: 44 passed
  - python -m py_compile: passed
  - git diff --check: passed
  - In-app browser: four-stage compute workflow visible, structure/ORCA selection reaches script generation, no console errors
  - No external Multiwfn, Gaussian, ORCA, or formchk process was executed

## 2026-07-15 19:18:51+08:00

- Request: 将 XYZRender Workstation 更新为 1.0.0 正式版，移除 V1 标识，重建并发布 Windows 安装器和便携版
- Status: Completed
- Changes:
  - 将应用、Python 包和 Inno Setup 版本统一升级为 1.0.0，并移除页面及启动信息中的 V1 标识
  - 重新构建 PyInstaller onedir 程序与 Inno Setup 安装器，生成完整便携版 ZIP 和 SHA-256 校验文件
  - 将正式版源码推送到 TiegenFang/xyzrender-webapp，并发布 v1.0.0 GitHub Release 的三个资产
- Files:
  - `.gitignore`
  - `pyproject.toml`
  - `src/xyzrender_workstation/__init__.py`
  - `src/xyzrender_workstation/web/app.py`
  - `src/xyzrender_workstation/web/templates/index.html`
  - `src/xyzrender_workstation/web/static/pretty_lattice_refresh.css`
  - `scripts/build_html.py`
  - `desktop/installer.iss`
  - `desktop/BUILD.md`
  - `README.md`
  - `tests/test_flask_compat.py`
  - `dist/XYZRender-Workstation-1.0.0-Portable.zip`
  - `dist/installer/XYZRender-Workstation-1.0.0-Setup.exe`
  - `dist/SHA256SUMS-1.0.0.txt`
- Verification:
  - python -m pytest -q: 44 passed
  - PyInstaller and Inno Setup 6.7.3 build: succeeded
  - Frozen desktop --self-test: exit 0; SVG, PNG, PDF, GIF, upload and save checks passed
  - GitHub Release v1.0.0: published, not draft/prerelease; all three assets uploaded
  - Remote main matched local commit 175cea50fe2fbe5819a9ab4a36a1decd677b7b9c before the release-log commit

## 2026-07-16 12:51:20+08:00

- Request: 升级桌面版内置 xyzrender/CIF 支持，更新应用图标并发布 v1.0.1
- Status: Completed
- Changes:
  - 将 xyzrender 固定到上游提交 6802a375e3378658186d7b930770fb60440fdb23（0.3.6），并纳入 xyzgraph 1.6.13 与 ASE。
  - 修复 PyInstaller 漏收 scipy._cyutility 导致 ASE CIF 解析失败的问题，加入真实 CIF 冻结包验收。
  - 生成透明分子视口新图标，并同时应用到主程序与安装器。
  - 版本提升至 1.0.1，重新生成安装包、便携包和校验文件并发布 GitHub Release。
- Files:
  - `.gitignore`
  - `README.md`
  - `desktop/BUILD.md`
  - `desktop/assets/xyzrender-icon.png`
  - `desktop/assets/xyzrender-workstation.ico`
  - `desktop/installer.iss`
  - `desktop/launcher.py`
  - `desktop/xyzrender_workstation.spec`
  - `pyproject.toml`
  - `requirements.txt`
  - `src/xyzrender_workstation/__init__.py`
  - `tests/test_desktop_acceptance.py`
  - `tests/test_flask_compat.py`
- Verification:
  - pytest：44 项全部通过。
  - 本地最新 xyzrender 直接渲染 Al2O3.cif 成功。
  - PyInstaller 与 Inno Setup 构建成功。
  - 冻结版自检退出码为 0，CIF 输出 SVG 55,421 字节，XYZ/PDB/MOL/SDF 与 SVG/PNG/PDF/GIF 流程均通过。
  - 从 EXE 提取图标并进行视觉检查，16–256 px 图标资源齐全。
  - GitHub v1.0.1 Release 已发布，安装包、便携包与 SHA256 校验文件均上传成功。
