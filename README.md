# XYZRender Web App — 分子图形工作站

基于 **xyzrender** 库的 Web 渲染界面，支持将分子文件渲染为出版质量的 SVG、PNG、PDF 和 GIF。

---

## 目录结构

```
xyzrender_app/
├── app.py              # Flask 后端
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # 前端界面
├── MOLECULES/          # 放置分子文件（自动创建）
└── FIGURE/             # 渲染结果保存目录（自动创建）
```

---

## 安装

### 1. 安装

```bash
pip install xyzrender
# latest development version:
pip install --upgrade git+https://github.com/aligfellow/xyzrender.git
```

> 如果需要全部功能，可以安装如下：
> 
> ```bash
> pip install 'xyzrender[crystal]'  # VASP/QE periodic structures (phonopy)
> pip install 'xyzrender[smi]'      # SMILES input (rdkit)
> pip install 'xyzrender[cif]'      # CIF input (ase)
> pip install 'xyzrender[all]'      # everything above
> ```

### 2. 启动应用

```bash
python app.py
```

浏览器访问：<http://localhost:5000>

---

## 使用方法

### 步骤 1 — 准备分子文件

将分子文件放入 `MOLECULES/` 文件夹，或直接在网页界面中拖拽上传。

**支持的文件格式：**
| 格式 | 说明 |
|------|------|
| `.xyz` | XYZ 坐标文件 |
| `.mol` / `.sdf` | MOL/SDF 格式 |
| `.mol2` | MOL2 格式 |
| `.pdb` | 蛋白质数据库格式 |
| `.out` / `.log` | ORCA、Gaussian 等 QM 输出文件 |
| `.gjf` / `.gjc` | Gaussian 输入文件 |
| `.fchk` | Gaussian formatted checkpoint |
| `.cube` | 电子密度 / 分子轨道 cube 文件 |
| `.cif` | 晶体结构文件（需要 `xyzrender[crystal]`） |
| `.smiles` | SMILES 字符串文件（需要 `xyzrender[smiles]`） |

### 步骤 2 — 选择渲染选项

- **输出格式**：SVG（默认）、PNG、PDF、GIF（旋转动画）
- **绘图风格**：
  - `default` — 标准 CPK 风格，带深度雾化
  - `flat` — 扁平化无阴影风格
  - `paton` — PyMOL 风格（球棍模型）
  - `skeletal` — 骨架式（有机化学惯例）
  - `bubble` — 大球风格
  - `tube` — 管状键
  - `wire` — 线框风格
- **渲染选项**：
  - 显示氢原子（`--hy`）
  - 过渡态键（`--ts`）
  - 非共价相互作用（`--nci`）
- **GIF 动画**：旋转轴 x / y / z / xy
- **高级选项**（量子化学）：
  - 电子密度等值面（`--dens`，需要 cube 文件）
  - 分子轨道（`--mo`，需要 MO cube 文件）
  - ESP 映射（需要两个 cube 文件）
  - 自定义 JSON 配置覆盖

### 步骤 3 — 渲染 & 查看

点击 **▶ 渲染分子** 后，结果将：
1. 自动保存到 `FIGURE/` 文件夹
2. 在右侧预览区实时显示
3. 支持全屏查看和下载

---

## API 说明

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET /api/molecules` | GET | 列出 MOLECULES/ 中的文件 |
| `GET /api/figures` | GET | 列出 FIGURE/ 中的渲染结果 |
| `POST /api/upload` | POST | 上传分子文件（multipart/form-data） |
| `POST /api/render` | POST | 执行渲染（JSON body） |
| `POST /api/delete_molecule` | POST | 删除分子文件 |
| `POST /api/delete_figure` | POST | 删除渲染结果 |
| `GET /figures/<name>` | GET | 获取渲染图形文件 |
| `GET /molecules/<name>` | GET | 下载原始分子文件 |

### /api/render 请求体示例

```json
{
  "file": "caffeine.xyz",
  "format": "png",
  "style": "paton",
  "hydrogens": true,
  "ts": false,
  "nci": false,
  "gif_rot": "y",
  "iso": "",
  "opacity": "",
  "dens_color": "",
  "bg_color": "white",
  "width": "",
  "height": ""
}
```

---

## 引用

使用本工具发表研究成果时，请引用 xyzrender：

> A.S. Goodfellow & B.N. Nguyen, *J. Chem. Theory Comput.*, 2026,
> DOI: [10.1021/acs.jctc.5c02073](https://doi.org/10.1021/acs.jctc.5c02073)

### BibTeX

```txt
@article{goodfellow2026xyzgraph,
  author  = {Goodfellow, A.S. and Nguyen, B.N.},
  title   = {Graph-Based Internal Coordinate Analysis for Transition State Characterization},
  journal = {J. Chem. Theory Comput.},
  year    = {2026},
  doi     = {10.1021/acs.jctc.5c02073},
}
```

---

## 相关链接

- xyzrender 文档：<https://xyzrender.readthedocs.io>
- xyzrender GitHub：<https://github.com/aligfellow/xyzrender>
- 官方 Streamlit 演示：<https://xyzrender-web.streamlit.app>
