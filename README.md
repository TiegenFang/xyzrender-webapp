# XYZRender Workstation

基于 `xyzrender 0.3.1` 的分子与量子化学 Flask Web 可视化工作站。

## 项目结构

```text
xyzrender_app_new/
├── src/xyzrender_workstation/
│   ├── core/                 # 渲染、模型、旋转、Multiwfn 服务
│   ├── web/                  # Flask 应用、模板和静态资源
│   └── paths.py              # 统一工作区路径
├── scripts/build_html.py     # Web 模板生成器
├── desktop/                 # pywebview 启动器与 Windows 打包配置
├── tests/                    # 自动化测试
├── MOLECULES/                # 分子输入文件
├── TEMP/                     # 预览和临时任务
├── FIGURE/                   # 正式保存结果
├── app.py                    # Web 兼容入口
└── pyproject.toml            # Python 包及命令行入口
```

历史更新见 [CHANGELOG](CHANGELOG.md)，Windows 桌面版的构建与安装说明见
[`desktop/BUILD.md`](desktop/BUILD.md)。

## 安装

Web 版：

```powershell
python -m pip install -r requirements.txt
```

Web 版不需要 pywebview 或 PyInstaller；桌面打包依赖单独位于
`desktop/requirements-desktop.txt`。

## 启动

Web 版：

```powershell
python app.py
```

浏览器访问 <http://localhost:5000>。

Windows 也可双击 `start_web.bat`。Web 默认关闭 Flask 自动重载器，避免科学计算依赖被监视后触发无限重启；端口冲突时可使用：

```powershell
python app.py --port 5001
```

安装为包后使用 `xyzrender-web` 命令启动 Web 版。

## 功能

- SVG、PNG、PDF、GIF 输出和临时预览；
- 分子旋转、缩放、平移、框选、氢原子过滤、编号和过渡态虚线；
- 表面、ESP、MO、IGMH、晶体、叠加及高级 kwargs；
- Gaussian、ORCA、xTB 等 xyzrender 支持格式的读取；
- 外部 Multiwfn 的 ESP、MO、IGMH 和六类原子电荷任务；
- Multiwfn 独立任务目录、超时、取消、进程树清理和输出校验；
- Flask 旧接口和 `MOLECULES → TEMP → FIGURE` 流程兼容。
- 桌面“完整参数”页动态覆盖当前 xyzrender 公共 API 的加载、渲染和 GIF 参数。
- 桌面布局、配色、风格卡片、输出画廊和参数分类与 HTML 版保持一致，并额外保留原生交互画布和 Multiwfn 后台任务。

Multiwfn 不随本项目打包，需要在桌面设置页选择本机 `Multiwfn.exe`。本项目不会启动 Gaussian、ORCA 或 xTB 计算任务。

## Web API

主要端点：

| 端点 | 用途 |
|---|---|
| `GET /api/capabilities` | 查看 xyzrender 版本与可用能力 |
| `GET /api/molecules` | 列出项目分子文件 |
| `POST /api/upload` | 上传分子文件 |
| `POST /api/render` | 渲染到 `TEMP` |
| `GET /api/temp_figures` | 列出临时预览 |
| `POST /api/save_figure` | 从 `TEMP` 保存到 `FIGURE` |
| `GET /api/figures` | 列出正式输出 |

成功渲染响应继续使用 `{ok, output, cmd}` 格式；共享核心无法映射的旧参数会自动走兼容渲染路径。

## 测试

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

测试范围包括共享核心、四元数距离保持、Flask 回归、模拟 Multiwfn
任务，以及桌面端路径、日志和多格式验收。

## 生成 Web 模板

```powershell
python build_html.py
```

实际生成器位于 `scripts/build_html.py`，输出到包内 `web/templates/index.html`。

该命令只重建 Web 模板，不会触发桌面版打包。

## 引用

使用 xyzrender 发表研究成果时，请引用：

> A. S. Goodfellow & B. N. Nguyen, *J. Chem. Theory Comput.*, 2026, DOI: [10.1021/acs.jctc.5c02073](https://doi.org/10.1021/acs.jctc.5c02073)

## Windows 桌面版

桌面版保留现有 Flask 路由和 HTML 界面，由 `desktop/launcher.py` 启动仅监听
`127.0.0.1` 的本地服务，并通过 pywebview 显示原生窗口。构建和安装说明见
[`desktop/BUILD.md`](desktop/BUILD.md)。

```powershell
.\desktop\build.ps1
```

产物位于 `dist\XYZRender Workstation\`（PyInstaller onedir）和
`dist\installer\XYZRender-Workstation-1.0.0-Setup.exe`（Inno Setup）。用户的
MOLECULES、TEMP、FIGURE 与日志保存在 `%LOCALAPPDATA%\XYZRender Workstation`，
不会写入安装目录，也不会在升级或默认卸载时删除。
