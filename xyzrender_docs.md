# xyzrender documentation

Publication-quality molecular graphics from XYZ, cube, QM output, and more — as SVG, PNG, PDF, or animated GIF.

Simple CLI input:

```bash
xyzrender bimp.out --gif-ts --gif-rot --nci --vdw 84-169
```


---

# Installation

## From PyPI

```bash
pip install xyzrender
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install xyzrender
```

To test without installing:

```bash
uvx xyzrender
```

## From Source

```bash
git clone https://github.com/aligfellow/xyzrender.git
cd xyzrender
pip install .
```

Or with uv:

```bash
git clone https://github.com/aligfellow/xyzrender.git
cd xyzrender
uv tool install .
```

## Optional dependencies

Some features require additional packages:

```bash
pip install 'xyzrender[crystal]'  # VASP/QE periodic structures (phonopy)
pip install 'xyzrender[smi]'      # SMILES input (rdkit)
pip install 'xyzrender[cif]'      # CIF input (ase)
pip install 'xyzrender[all]'      # everything above
```

xyzrender auto-detects resvg-py and uses it when available. Without it, CairoSVG is used as fallback (filters silently ignored in raster output).

## Development setup

Requires [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

```bash
git clone https://github.com/aligfellow/xyzrender.git
cd xyzrender
just setup
```

Available `just` commands:

| Command | Description |
|---------|-------------|
| `just check` | Run lint + type-check + tests |
| `just lint` | Format and lint with ruff |
| `just type` | Type-check with ty |
| `just test` | Run pytest with coverage |
| `just fix` | Auto-fix lint issues |
| `just build` | Build distribution |
| `just setup` | Install all dev dependencies |

---

# CLI Quickstart

One command is all you need:

```bash
xyzrender caffeine.xyz
```

This writes `caffeine.svg` in the current directory, auto-oriented with depth cueing and bond orders.

```{image} ../../examples/images/caffeine_default.svg
:width: 400
:alt: Caffeine default render
```

Specify output path and format with `-o` (extension controls format):

```bash
xyzrender caffeine.xyz -o render.svg
xyzrender caffeine.xyz -o render.png
xyzrender caffeine.xyz -o render.pdf
```

From QM output (ORCA, Gaussian, Q-Chem — auto-detected from content):

```bash
xyzrender calc.out
```

From stdin:

```bash
cat caffeine.xyz | xyzrender
```

See [User Guide](userguide.md) for all input formats, configuration, and the full CLI flag reference.

---

# Python / Jupyter Quickstart

## Load and render

```python
from xyzrender import load, render

mol = load("caffeine.xyz")
render(mol, output="caffeine.svg")
```

Results display inline in Jupyter automatically — `render()` returns an `SVGResult` object with a rich HTML repr.

```python
# Inline display in notebook — no output= needed
render(mol)
```

Pass render options as keyword arguments:

```python
render(mol, output="caffeine.png", hy=True, config="paton")
```

## Orient interactively

`orient()` opens the molecule in the `v` viewer for interactive rotation. Rotate to the desired view, press `z`, then `q`. The rotated positions are written back to `mol` and `mol.oriented` is set to `True` so subsequent `render()` calls skip auto-orientation.

```python
from xyzrender import orient

orient(mol)
render(mol, output="oriented.svg")
```

## Save geometry

Write the current atom positions back to an XYZ file with `mol.to_xyz()`. For crystal structures the output is extXYZ format with a `Lattice=` header:

```python
mol.to_xyz("output.xyz")
mol.to_xyz("output.xyz", title="My molecule")
```

## GIF animations

```python
from xyzrender import render_gif

render_gif(mol, gif_rot="y", output="caffeine.gif")
render_gif(mol, gif_diffuse=True, output="diffuse.gif")
```

See [Core API](api/core.rst) for the full API reference.

---

# Python API Guide

xyzrender has a full Python API. All CLI flags are available as keyword arguments. Results display inline in Jupyter automatically.

See also the [auto-generated API reference](api/core.rst) for docstrings and type signatures, and the runnable [`examples/examples.ipynb`](https://github.com/aligfellow/xyzrender/blob/main/examples/examples.ipynb) notebook.

## Loading molecules

`load()` parses a file and returns a `Molecule` object. Pass it to `render()` to avoid re-reading the file on every call. You can also pass a path string directly to `render()` as a shorthand.

```python
from xyzrender import load, render

mol = load("caffeine.xyz")
render(mol)                          # displays inline in Jupyter
render(mol, output="caffeine.svg")   # save as SVG
render(mol, output="caffeine.png")   # save as PNG

# Short-form: pass a path directly (re-parses each time)
render("caffeine.xyz")
```

### Loading options

Use `load()` keyword arguments for non-default loading behaviour:

```python
mol = load("ts.out", ts_detect=True)            # detect TS bonds via graphRC
mol = load("mol.xyz", nci_detect=True)          # detect NCI interactions
mol = load("mol.sdf", mol_frame=2, kekule=True) # SDF frame + Kekule bonds
mol = load("CC(=O)O", smiles=True)              # SMILES → 3D (requires rdkit)
mol = load("POSCAR", crystal=True)              # VASP/QE structure (requires phonopy)
mol = load("caffeine_cell.xyz", cell=True)      # extXYZ Lattice= header
mol = load("mol.xyz", quick=True)               # skip BO detection (faster, use with bo=False)
mol = load("mol.xyz", threshold=1.3)           # more permissive bond detection (detect longer bonds)
mol = load("mol.xyz", threshold=0.8)           # stricter bond detection (detect fewer bonds)
```

## Render options

All CLI flags are available as keyword arguments to `render()`:

### Styling

```python
render(mol, config="flat")                                     # built-in preset
render(mol, config="paton", transparent=True)                  # preset + transparent bg
render(mol, bond_width=8, atom_scale=1.5, background="#f0f0f0") # individual overrides
render(mol, bond_cutoff=2.0)                                   # hide bonds longer than 2.0 Å
render(mol, hide_bonds=True)                                   # hide all bonds
```

### Hydrogen visibility

Atom indices are **1-indexed**.

```python
ethanol = load("ethanol.xyz")
render(ethanol, hy=True)            # show all H
render(ethanol, no_hy=True)         # hide all H
render(ethanol, hy=[7, 8, 9])       # show specific H atoms
```

### Overlays

```python
render(mol, vdw=True)               # vdW spheres on all atoms
render(mol, vdw=[1, 3, 5])          # vdW spheres on specific atoms
render(mol, ts_bonds=[(1, 6)])      # manual TS bond (1-indexed)
render(mol, ts_color="dodgerblue")  # color for dashed TS bonds
render(mol, nci_bonds=[(2, 8)])     # manual NCI bond (1-indexed)
render(mol, nci_color="teal")       # color for dotted NCI bonds
render(mol, idx=True)               # atom index labels ("C1", "N3", ...)
render(mol, idx="n")                # index only ("1", "3", ...)
render(mol, mol_color="gray")                            # flat color for all atoms + bonds
render(mol, highlight="1-3,7")                           # highlight atoms 1-3 and 7 (orchid)
render(mol, highlight=[1, 2, 3, 7])                      # 1-indexed list
render(mol, highlight=[("1-5", "blue"), ("10-15", "red")])  # multi-group with colors
render(mol, highlight=["1-5", "10-15"])                  # multi-group, auto-colors from palette
render(mol, mol_color="gray", highlight="1-5")           # gray base + orchid highlight on top
render(mol, dof=True)                                   # depth-of-field blur
render(mol, dof=True, dof_strength=6.0)                 # stronger blur
```

### Structural overlay

```python
mol1 = load("isothio_xtb.xyz", charge=1)
mol2 = load("isothio_uma.xyz", charge=1)
render(mol1, overlay=mol2)                         # overlay mol2 onto mol1
render(mol1, overlay=mol2, overlay_color="green")  # custom overlay color
render(mol1, overlay=mol2, align_atoms=[1, 2, 3])  # align on atom subset
render_gif(mol1, overlay=mol2, gif_rot="y")        # spinning overlay GIF
```

See [Structural Overlay](examples/overlay.md) and [Conformer Ensemble](examples/ensemble.md) for more.

### Annotations

```python
render(mol, labels=["1 2 d", "1 2 3 a"])   # inline spec strings
render(mol, label_file="annot.txt")         # bulk annotation file
```

See [Annotations](examples/annotations.md) for the full spec syntax.

### Atom property colormap

`cmap` accepts a `{1-indexed atom: value}` dict or a path to a two-column file. Atoms absent from the mapping are drawn white.

```python
render(mol, cmap={1: 0.5, 2: -0.3}, cmap_range=(-1.0, 1.0))
render(mol, cmap="charges.txt", cmap_symm=True)   # symmetric range about 0
```

See [Atom Property Colormap](examples/cmap.md) for details on file format, palettes, and the colorbar.

### Surfaces (cube files)

```python
mol_cube = load("caffeine_homo.cube")
render(mol_cube, mo=True)                                          # MO lobes
render(mol_cube, mo=True, iso=0.03, mo_pos_color="maroon", mo_neg_color="teal")

dens_cube = load("caffeine_dens.cube")
render(dens_cube, dens=True)                       # density isosurface
render(dens_cube, esp="caffeine_esp.cube")         # ESP mapped onto density
render(dens_cube, nci="caffeine_grad.cube")        # NCI surface
```

See [Molecular Orbitals](examples/mo.md), [Electron Density and ESP](examples/dens_esp.md), and [NCI Surface](examples/nci_surf.md).

### Convex hull

```python
render(mol, hull=[1, 2, 3, 4, 5, 6],
       hull_color="steelblue", hull_opacity=0.35)
render(mol, hull="rings", hull_color="teal")       # auto-detect aromatic rings
```

See [Convex Hull](examples/hull.md) for multi-subset hulls and all options.

## Reusing a style config

`build_config()` builds a `RenderConfig` object you can pass to `render()` and `render_gif()`. Useful in notebooks or scripts that render several structures with the same style:

```python
from xyzrender import build_config

cfg = build_config("flat", atom_scale=1.5, gradient=False)
render(mol1, config=cfg)
render(mol2, config=cfg, ts_bonds=[(1, 6)])   # per-render overlay on shared style
render_gif("mol.xyz", gif_rot="y", config=cfg)
```

## Geometry measurements

`measure()` returns bonded distances, angles, and dihedrals as a dict. It does not render anything. Atom indices in the output are **0-indexed**.

```python
from xyzrender import measure

data = measure(mol)                    # all measurements
data = measure("mol.xyz")             # also accepts a path
data = measure(mol, modes=["d", "a"]) # distances and angles only

for i, j, d in data["distances"]:
    print(f"  {i+1}-{j+1}: {d:.3f} Å")
```

## Saving geometry

`Molecule.to_xyz()` writes the structure to an XYZ file. Ghost atoms are excluded. If the molecule has `cell_data` (loaded with `cell=True` or `crystal=...`), the output is extXYZ with a `Lattice=` header so it can be reloaded directly.

```python
mol = load("CC(=O)O", smiles=True)
mol.to_xyz("acetic_acid.xyz")                            # plain XYZ
mol.to_xyz("acetic_acid.xyz", title="acetic acid")       # with comment line

mol_cell = load("caffeine_cell.xyz", cell=True)
mol_cell.to_xyz("out.xyz")                               # extXYZ with Lattice= header
```

## Interactive orientation

`orient()` opens the 3D viewer ([**v**](https://github.com/briling/v)) so you can rotate a molecule manually, then locks the orientation for subsequent `render()` calls:

```python
from xyzrender import orient

mol = load("caffeine.xyz")
orient(mol)        # opens viewer — rotate, close to confirm
render(mol)        # renders in the manually chosen orientation
```

Requires `pip install xyzrender[v]` (Linux only).

## Orientation reference

Use `ref=` to save or load a reference orientation for consistent batch rendering:

```python
mol1 = load("homo.cube")
render(mol1, mo=True, ref="reference.xyz")   # first call saves oriented positions

mol2 = load("lumo.cube")
render(mol2, mo=True, ref="reference.xyz")   # subsequent calls Kabsch-align to the reference
```

When the reference file exists, `orient=True` is ignored — the reference is the orientation.

## GIF animations

```python
from xyzrender import render_gif

render_gif("caffeine.xyz", gif_rot="y")           # rotation GIF
render_gif("ts.out", gif_ts=True)                  # TS vibration GIF
render_gif("traj.xyz", gif_trj=True)               # trajectory GIF
render_gif("mol.xyz", gif_rot="y", config=cfg)     # with shared style config

# Diffuse / assembly GIF
render_gif("caffeine.xyz", gif_diffuse=True)
render_gif("caffeine.xyz", gif_diffuse=True, diffuse_noise=0.5, diffuse_bonds="hide")
render_gif("caffeine.xyz", gif_diffuse=True, gif_rot="y", diffuse_rot=90)
render_gif("caffeine.xyz", gif_diffuse=True, anchor="1-5,8")

# Surface in rotation GIF (cube file)
mol_cube = load("caffeine_homo.cube")
render_gif(mol_cube, gif_rot="y", mo=True, output="homo_rot.gif")
```

## Return types

### SVGResult

`render()` returns an `SVGResult` object. In Jupyter it displays inline automatically.

```python
result = render(mol)
str(result)              # raw SVG string
result.save("out.svg")   # write to file
```

### GIFResult

`render_gif()` returns a `GIFResult` object. In Jupyter it displays inline automatically.

```python
gif = render_gif("mol.xyz", gif_rot="y")
gif.path                 # pathlib.Path to the GIF on disk
bytes(gif)               # raw GIF bytes
gif.save("copy.gif")     # copy to another path
```

---

# Input Formats

xyzrender reads bond connectivity directly from file where available (mol, SDF, MOL2, PDB, SMILES, CIF). The parser is selected by file extension.

## XYZ

Standard XYZ files:

```bash
xyzrender molecule.xyz
```

extXYZ (with `Lattice=` header) is handled automatically — the unit cell box, ghost atoms, and axis arrows are enabled without any extra flags. See [Crystal Structures](examples/crystal.md).

## QM Output

ORCA (`.out`), Gaussian (`.log`), Q-Chem (`.out`) — format is auto-detected from file content:

```bash
xyzrender calc.out
xyzrender calc.log
```

Use `--charge` and `--multiplicity` if needed for bond detection:

```bash
xyzrender calc.out -c -1 -m 2
```

See [Transition States and NCI](examples/ts_nci.md) for transition state rendering from QM output.

## Cheminformatics formats

```bash
xyzrender molecule.sdf       # SDF — bonds from file
xyzrender molecule.mol       # mol — bonds from file
xyzrender molecule.mol2      # MOL2 — Tripos aromatic bonds
xyzrender structure.pdb      # PDB — ATOM/HETATM + CONECT records
```

**PDB with CRYST1:** if the PDB contains a `CRYST1` record, the unit cell is parsed and crystal rendering is used automatically.

**Multi-record SDF:** use `--mol-frame N` to select a record (default: 0):

```bash
xyzrender multi.sdf --mol-frame 1
```

## SMILES

Requires `pip install 'xyzrender[smi]'` (rdkit). Embeds a SMILES string into 3D using ETKDGv3 + MMFF94.

```bash
xyzrender --smi "C1CCCCC1" --hy -o cyclohexane.svg
```

An XYZ file of the optimised 3D geometry is automatically saved alongside the rendered image (e.g. `cyclohexane.xyz`).

## CIF

Requires `pip install 'xyzrender[cif]'` (ase):

```bash
xyzrender structure.cif
```

## Cube files

Cube files contain both molecular geometry and a 3D volumetric grid. Used for molecular orbitals ([Molecular Orbitals](examples/mo.md)), electron density and ESP ([Electron Density and ESP](examples/dens_esp.md)), and NCI surfaces ([NCI Surface](examples/nci_surf.md)).

```bash
xyzrender homo.cube --mo
xyzrender dens.cube --dens
xyzrender dens.cube --esp esp.cube
xyzrender dens.cube --nci-surf grad.cube
```

## Periodic structures (VASP / QE)

Requires `pip install 'xyzrender[crystal]'` (`phonopy`):

```bash
xyzrender NV63.vasp --crystal vasp
xyzrender NV63.in --crystal qe
```

Format is auto-detected from extension; `--crystal` with no argument also works. See [Crystal Structures](examples/crystal.md).

## Re-detecting bonds

`--rebuild` discards file connectivity and re-runs xyzgraph distance-based detection:

```bash
xyzrender molecule.sdf --rebuild
```

## Format-specific flags

| Flag | Description |
|------|-------------|
| `--smi SMILES` | Embed a SMILES string into 3D (requires rdkit) |
| `--mol-frame N` | Record index in multi-molecule SDF (default: 0) |
| `--rebuild` | Ignore file connectivity; re-detect bonds with xyzgraph |
| `-c`, `--charge` | Molecular charge |
| `-m`, `--multiplicity` | Spin multiplicity |

---

# Orientation

## Auto-orientation

Auto-orientation is on by default. xyzrender aligns the molecule so the axis of largest positional variance lies along the x-axis (PCA), giving a consistent front-facing view.

```bash
xyzrender molecule.xyz            # auto-oriented (default)
xyzrender molecule.xyz --no-orient  # raw coordinates as-is
```

Auto-orientation is disabled automatically when reading from stdin.

## Interactive rotation (`-I`)

The `-I` flag opens the molecule in the [**v** molecular viewer](https://github.com/briling/v) by [Ksenia Briling **@briling**](https://github.com/briling)
for interactive rotation. Rotate the molecule to the desired orientation
and close the window with `q` or `esc`.
`xyzrender` captures the rotated coordinates and renders from those.

```bash
xyzrender molecule.xyz -I
```

## Orientation reference (`--ref`)

The `--ref` flag saves or loads a reference orientation for consistent rendering across multiple files (e.g. a batch of MO cube files).

**First render** — file does not exist yet, PCA-oriented positions are saved:
```bash
xyzrender homo.cube --mo --ref              # saves reference.xyz
xyzrender homo.cube --mo --ref custom.xyz   # saves custom.xyz
```

**Subsequent renders** — file exists, molecule is Kabsch-aligned to it:
```bash
xyzrender lumo.cube --mo --ref              # loads reference.xyz, same orientation
xyzrender lumo.cube --mo --ref custom.xyz   # loads custom.xyz
```

When loading an existing reference, `--orient` is ignored — the reference file IS the orientation.

### Combined with `-I`

Orient interactively once, then reuse:
```bash
xyzrender homo.cube --mo -I --ref           # orient in viewer, save
xyzrender lumo.cube --mo --ref              # load, same orientation
```

If the reference file already exists, `-I` is skipped (the viewer is not opened).

### Python API

```python
from xyzrender import render, load

mol1 = load("homo.cube")
render(mol1, mo=True, ref="reference.xyz")   # save

mol2 = load("lumo.cube")
render(mol2, mo=True, ref="reference.xyz")   # load, same orientation
```

### Consistent orientation across a chemical series

`--ref` works across related compounds with different substituents, atom counts, or conformations. The shared scaffold is detected automatically — molecules are aligned on their largest common connected substructure. This gives consistent orientations across a series of derivatives, useful for comparing substituent effects or building figure panels:

```bash
# Orient the first compound interactively and save the reference
xyzrender catalyst_a.xyz -I --ref series.xyz

# All derivatives align to the same scaffold, regardless of substitution
xyzrender catalyst_b.xyz --ref series.xyz   # different R-group
xyzrender catalyst_c.xyz --ref series.xyz   # different atom count
xyzrender catalyst_d.xyz --ref series.xyz   # different heterocycle
```

---

# Configuration

## Built-in presets

Use `--config` to load a styling preset. Built-in options: `default`, `flat`, `paton`, `pmol`, `skeletal`, `bubble`, `tube`, `wire`, `graph`.

| Preset | Description |
|--------|-------------|
| `default` | Radial gradients, depth fog, CPK colors |
| `flat` | No gradients, no fog — clean flat look |
| `paton` | PyMOL-inspired style (see [Rob Paton](https://github.com/patonlab)) |
| `pmol` | Ball-and-stick with element-coloured split bonds and tube shading (PyMOL-inspired) |
| `skeletal` | Skeletal formula diagram — thin bonds, minimal atoms |
| `bubble` | Space-filling (CPK) — large atoms, no bonds |
| `tube` | Tube/stick model — no atoms, thick element-coloured bonds with cylinder shading |
| `wire` | Wireframe — no atoms, thin element-coloured bonds with cylinder shading |
| `graph` | Minimal graph look — teal bonds, bold outlined nodes with light tinted centers |

```bash
xyzrender caffeine.xyz --config flat
xyzrender caffeine.xyz --config paton
xyzrender caffeine.xyz --config pmol
xyzrender caffeine.xyz --config skeletal
xyzrender caffeine.xyz --config bubble --hy
xyzrender caffeine.xyz --config tube
xyzrender caffeine.xyz --config wire
xyzrender caffeine.xyz --config graph
```

CLI flags override preset values:

```bash
xyzrender caffeine.xyz --config paton --bo   # paton preset but with bond orders on
xyzrender caffeine.xyz --config default --no-fog
```

## Custom presets (JSON)

Create a JSON file with any keys you want to override. Everything else falls back to the default. Load it with `--config`:

```bash
xyzrender caffeine.xyz --config my_style.json
```

All available keys:

```json
{
  "canvas_size": 800,
  "atom_scale": 2.5,
  "bond_width": 20,
  "bond_color": "#000000",
  "ts_color": "#1E90FF",
  "nci_color": "#228B22",
  "atom_stroke_width": 3,
  "gradient": true,
  "gradient_strength": 1.5,
  "fog": true,
  "fog_strength": 1.2,
  "bond_orders": true,
  "background": "#ffffff",
  "vdw_opacity": 0.25,
  "vdw_scale": 1.0,
  "vdw_gradient_strength": 0.845,
  "surface_opacity": 1.0,
  "mo_pos_color": "steelblue",
  "mo_neg_color": "maroon",
  "nci_mode": "avg",
  "dens_iso": 0.001,
  "dens_color": "steelblue",
  "label_font_size": 30,
  "label_color": "#222222",
  "label_offset": 1.5,
  "cmap_unlabeled": "#ffffff",
  "bond_color_by_element": false,
  "bond_gradient": false,
  "atom_wash": 0.0,
  "atoms_above_bonds": false,
  "colors": {
    "C": "silver",
    "H": "whitesmoke",
    "N": "slateblue",
    "O": "red"
  }
}
```

The `colors` key maps element symbols to hex values (`#D9D9D9`) or [CSS4 named colors](https://matplotlib.org/stable/gallery/color/named_colors.html) (`steelblue`), overriding the default CPK palette.

Surface-related keys (`mo_pos_color`, `mo_neg_color`, `dens_iso`, `dens_color`) are only used when `--mo`, `--dens`, or `--esp` is active.

## Output formats

The output format is determined by the file extension of `-o`:

```bash
xyzrender caffeine.xyz -o out.svg   # SVG (default, scalable)
xyzrender caffeine.xyz -o out.png   # PNG (rasterised)
xyzrender caffeine.xyz -o out.pdf   # PDF (vector)
```

If no `-o` is given, output defaults to `{input_basename}.svg`.

## Styling flags

| Flag | Description |
|------|-------------|
| `-a`, `--atom-scale` | Atom radius scale factor |
| `-b`, `--bond-width` | Bond line width |
| `-s`, `--atom-stroke-width` | Atom outline width |
| `--bond-color` | Bond color (hex or named) |
| `--ts-color` | Color for dashed TS bonds (hex or named) |
| `--nci-color` | Color for dotted NCI bonds (hex or named) |
| `-S`, `--canvas-size` | Canvas size in pixels (default: 800) |
| `-B`, `--background` | Background color (hex or named, default: `#ffffff`) |
| `-t`, `--transparent` | Transparent background |
| `--grad` / `--no-grad` | Toggle radial gradients |
| `-G`, `--gradient-strength` | Gradient contrast |
| `--fog` / `--no-fog` | Toggle depth fog |
| `-F`, `--fog-strength` | Depth fog strength |
| `--bo` / `--no-bo` | Toggle bond order rendering |
| `--vdw-opacity` | vdW sphere opacity |
| `--vdw-scale` | vdW sphere radius scale |
| `--vdw-gradient` | vdW sphere gradient strength |
| `--bond-by-element` / `--no-bond-by-element` | Color bonds by endpoint atom colors |
| `--bond-gradient` / `--no-bond-gradient` | Cylinder shading on bonds (3D tube look) |
| `--region ATOMS CONFIG` | Render atom subset with a different preset (repeatable) |

---

# CLI Reference

Full flag reference for `xyzrender`. See also `xyzrender --help`.

## Input / Output

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Static output path (`.svg`, `.png`, `.pdf`) |
| `--smi SMILES` | Embed a SMILES string into 3D (requires rdkit) |
| `--mol-frame N` | Record index in multi-molecule SDF (default: 0) |
| `--rebuild` | Ignore file connectivity; re-detect bonds with xyzgraph |
| `--threshold SCALE` | Global bond-distance scaling factor (default: 1.0). Values > 1.0 detect longer bonds, < 1.0 detect fewer |
| `-c`, `--charge` | Molecular charge |
| `-m`, `--multiplicity` | Spin multiplicity |
| `--config` | Config preset (`default`, `flat`, `paton`, `pmol`, `skeletal`) or path to JSON file |
| `-d`, `--debug` | Debug logging |

## Styling

| Flag | Description |
|------|-------------|
| `-S`, `--canvas-size` | Canvas size in px (default: 800) |
| `-a`, `--atom-scale` | Atom radius scale factor |
| `-b`, `--bond-width` | Bond stroke width |
| `-s`, `--atom-stroke-width` | Atom outline stroke width |
| `--bond-color` | Bond color (hex or named) |
| `--bond-cutoff` | Hide bonds longer than this distance (Å) |
| `--no-bonds` | Hide all bonds (e.g. space-filling style) |
| `-B`, `--background` | Background color |
| `-t`, `--transparent` | Transparent background |
| `-G`, `--gradient-strength` | Gradient contrast multiplier |
| `--grad` / `--no-grad` | Radial gradient toggle |
| `-F`, `--fog-strength` | Depth fog strength |
| `--fog` / `--no-fog` | Depth fog toggle |
| `--bo` / `--no-bo` | Bond order rendering toggle |

## Display

| Flag | Description |
|------|-------------|
| `--hy [ATOMS]` | Show H atoms (no args = all, or `"1-5,8"` 1-indexed) |
| `--no-hy` | Hide all H atoms |
| `-k`, `--kekule` | Use Kekulé bond orders (no aromatic 1.5) |
| `--vdw` | vdW spheres (no args = all, or index ranges e.g. `1-6`) |
| `--vdw-opacity` | vdW sphere opacity (default: 0.25) |
| `--vdw-scale` | vdW sphere radius scale |
| `--vdw-gradient` | vdW sphere gradient strength |
| `--mol-color COLOR` | Flat color for all atoms and bonds (overrides CPK). Highlight paints on top |
| `--hl ATOMS [COLOR]` | Highlight atom group: `--hl "1-5,8" [color]`. Can be repeated for multiple groups. Auto-colors from palette if no color given |
| `--dof` | Depth-of-field blur (front atoms sharp, back atoms blurred) |
| `--dof-strength FLOAT` | DoF max blur strength (default: 3.0) |

## Structural overlay / ensemble

| Flag | Description |
|------|-------------|
| `--overlay FILE` | Second structure to overlay (RMSD-aligned onto the primary). Different atom counts are handled automatically via shared-scaffold alignment |
| `--overlay-color COLOR` | Color for the overlay structure (hex or named) |
| `--ensemble` | Ensemble overlay for multi-frame XYZ trajectories; conformers default to CPK atom colours |
| `--ensemble-color VALUE` | Palette name (`viridis`, `spectral`, `coolwarm`), a single colour, or comma-separated colours |
| `--opacity FLOAT` | Opacity for non-reference conformers (0–1) |
| `--align-atoms INDICES` | 1-indexed atom subset for Kabsch alignment (min 3), e.g. `1,2,3` or `1-6`. Works with `--overlay` and `--ensemble` |

## Orientation

| Flag | Description |
|------|-------------|
| `-I`, `--interactive` | Interactive rotation via `v` viewer |
| `--orient` / `--no-orient` | Auto-orientation toggle |
| `--ref [FILE]` | Save/load orientation reference (`reference.xyz` by default) |

## TS / NCI

| Flag | Description |
|------|-------------|
| `--ts` | Auto-detect TS bonds via graphRC |
| `--ts-frame` | TS reference frame (0-indexed) |
| `--ts-bond` | Manual TS bond pair(s) (1-indexed, e.g. `1-2`) |
| `--ts-color` | Color for dashed TS bonds (hex or named) |
| `--nci` | Auto-detect NCI interactions |
| `--nci-bond` | Manual NCI bond pair(s) (1-indexed) |
| `--nci-color` | Color for dotted NCI bonds (hex or named) |

## Surfaces

| Flag | Description |
|------|-------------|
| `--mo` | Render MO lobes from `.cube` input |
| `--mo-colors POS NEG` | MO lobe colors (hex or named) |
| `--mo-blur SIGMA` | MO Gaussian blur sigma (default: 0.8, ADVANCED) |
| `--mo-upsample N` | MO contour upsample factor (default: 3, ADVANCED) |
| `--flat-mo` | Render all MO lobes as front-facing (no depth classification) |
| `--dens` | Render density isosurface from `.cube` input |
| `--dens-color` | Density surface color (default: `steelblue`) |
| `--esp CUBE` | ESP cube file for potential coloring (implies `--dens`) |
| `--nci-surf CUBE` | NCI gradient (RDG) cube — render NCI surface lobes |
| `--nci-mode MODE` | NCI surface coloring: `avg` (default), `pixel`, `uniform`, or a colour name/hex |
| `--iso` | Isosurface threshold (MO default: 0.05, density/ESP: 0.001, NCI: 0.3) |
| `--opacity` | Surface opacity multiplier (default: 1.0) |

## Annotations

| Flag | Description |
|------|-------------|
| `--measure [TYPE...]` | Print bond measurements to stdout (`d`, `a`, `t`; combine or omit for all) |
| `--idx [FMT]` | Atom index labels in SVG (`sn` = C1, `s` = C, `n` = 1) |
| `-l TOKEN...` | Inline SVG annotation (repeatable); 1-based indices |
| `--label FILE` | Bulk annotation file (same syntax as `-l`) |
| `--label-size PT` | Label font size (overrides preset) |
| `--stereo [CLASSES]` | Stereochemistry labels from 3D geometry. Optional comma-separated class filter: `point`, `ez`, `axis`, `plane`, `helix`. Omit to show all |
| `--stereo-style STYLE` | R/S label placement: `atom` (centered, default) or `label` (offset) |
| `--cmap FILE` | Per-atom property colormap (1-indexed atom index, value) |
| `--cmap-range VMIN VMAX` | Explicit colormap range (default: auto from file) |
| `--cmap-symm` | Symmetric colormap range about zero: `[-max(|v|), +max(|v|)]` |
| `--cmap-palette NAME` | Colormap palette (default: `viridis`) |
| `--cbar` | Add a vertical colorbar on the right showing the data range |

## Vector arrows

| Flag | Description |
|------|-------------|
| `--vector FILE` | Path to a JSON file defining 3D vector arrows for overlay |
| `--vector-scale` | Global length multiplier for all vector arrows |

## GIF animations

| Flag | Description |
|------|-------------|
| `--gif-rot [AXIS]` | Rotation GIF (default axis: `y`). Combinable with `--gif-ts` |
| `--gif-ts` | TS vibration GIF (via graphRC) |
| `--gif-trj` | Trajectory / optimisation GIF (multi-frame input) |
| `-go`, `--gif-output` | GIF output path (default: `{basename}.gif`) |
| `--gif-fps` | Frames per second (default: 10) |
| `--rot-frames` | Rotation frame count (default: 120) |

Available rotation axes: `x`, `y`, `z`, `xy`, `xz`, `yz`, `yx`, `zx`, `zy`. Prefix `-` to reverse (e.g. `-xy`). For crystal inputs, a 3-digit Miller index string is also accepted (e.g. `111`, `001`).

## Convex hull

| Flag | Description |
|------|-------------|
| `--hull [INDICES ...]` | Draw convex hull (no args = all heavy atoms; `rings` = auto-detect aromatic rings; or 1-indexed subsets e.g. `1-6` or `1-6 7-12`) |
| `--hull-color COLOR [...]` | Hull fill color(s) (hex or named, one per subset) |
| `--hull-opacity FLOAT` | Hull fill opacity (0-1) |
| `--hull-edge` / `--no-hull-edge` | Draw/hide non-bond hull edges (default: on) |
| `--hull-edge-width-ratio FLOAT` | Hull edge stroke width as fraction of bond width (default: 0.4) |

## Crystal / unit cell

| Flag | Description |
|------|-------------|
| `--cell` | Draw unit cell box from `Lattice=` in extXYZ (usually auto-detected) |
| `--cell-color` | Cell edge color (hex or named, default: `gray`) |
| `--cell-width` | Unit cell box line width (default: 2.0) |
| `--crystal [{vasp,qe}]` | Load as crystal via `phonopy`; format auto-detected or explicit |
| `--no-cell` | Hide the unit cell box |
| `--ghosts` / `--no-ghosts` | Show/hide ghost (periodic image) atoms outside the cell |
| `--ghost-opacity` | Opacity of ghost atoms/bonds (default: 0.5) |
| `--axes` / `--no-axes` | Show/hide the a/b/c axis arrows |
| `--axis HKL` | Orient looking down a crystallographic direction (e.g. `111`, `001`) |
| `--supercell M N L` | Repeat the unit cell `M×N×L` times along a/b/c (requires lattice/unit-cell data; default: `1 1 1`) |

---

# Basics

## Presets

| Default | Flat | Paton (PyMOL-like) | Bubble |
|---------|------|-------------------|--------|
| ![Default](../../../examples/images/caffeine_default.svg) | ![Flat](../../../examples/images/caffeine_flat.svg) | ![Paton (PyMOL-like)](../../../examples/images/caffeine_paton.svg) | ![Bubble](../../../examples/images/caffeine_bubble.svg) |

| Tube | Wire |
|------|------|
| ![Tube](../../../examples/images/caffeine_tube.svg) | ![Wire](../../../examples/images/caffeine_wire.svg) |

```bash
xyzrender caffeine.xyz                        # default
xyzrender caffeine.xyz --config flat          # flat: no gradient
xyzrender caffeine.xyz --config paton         # paton: PyMOL-style
xyzrender caffeine.xyz --config pmol          # pmol: ball-and-stick + element-coloured bonds (PyMOL-inspired)
xyzrender caffeine.xyz --config bubble --hy   # space-filling-like
xyzrender caffeine.xyz --config tube          # tube: cylinder-shaded sticks
xyzrender caffeine.xyz --config wire          # wire: thin element-coloured lines
```

The `paton` style is inspired by the clean styling used by [Rob Paton](https://github.com/patonlab) through PyMOL.

The `pmol` preset is a PyMOL-inspired style that keeps atoms visible and adds split element-coloured bonds with cylinder shading.

The `tube` and `wire` presets hide atom circles and colour each bond by its endpoint atoms, with a cylinder shading gradient for a 3D look. The `tube` preset uses thick bonds; `wire` uses thin bonds.

## Hydrogen display

| All H | Some H | No H |
|-------|--------|------|
| ![All H](../../../examples/images/ethanol_all_h.svg) | ![Some H](../../../examples/images/ethanol_some_h.svg) | ![No H](../../../examples/images/ethanol_no_h.svg) |

```bash
xyzrender ethanol.xyz --hy              # all H
xyzrender ethanol.xyz --hy 7 8 9        # specific H atoms (1-indexed)
xyzrender ethanol.xyz --no-hy           # no H
```

## Bond orders

| Aromatic | Kekulé |
|----------|--------|
| ![Aromatic](../../../examples/images/benzene.svg) | ![Kekulé](../../../examples/images/caffeine_kekule.svg) |

```bash
xyzrender benzene.xyz --hy              # aromatic notation (default)
xyzrender caffeine.xyz --bo -k          # Kekulé bond orders
```

## vdW spheres

| All atoms | Selected atoms | Paton style |
|-----------|---------------|-------------|
| ![All atoms](../../../examples/images/asparagine_vdw.svg) | ![Selected atoms](../../../examples/images/asparagine_vdw_partial.svg) | ![Paton style](../../../examples/images/asparagine_vdw_paton.svg) |

```bash
xyzrender asparagine.xyz --hy --vdw                   # all atoms
xyzrender asparagine.xyz --hy --vdw "1-6"             # atoms 1–6 only
xyzrender asparagine.xyz --hy --vdw --config paton    # paton style
```

## Depth of field

Blur back atoms while keeping front atoms sharp. Uses SVG `feGaussianBlur` filters.

| DoF | Rotation |
|-----|----------|
| ![dof](../../../examples/images/caffeine_dof.svg) | ![dof](../../../examples/images/caffeine_dof.gif) |

```bash
xyzrender caffeine.xyz --dof --no-orient                    # default strength
xyzrender caffeine.xyz --dof --dof-strength 6.0 --no-orient # stronger blur
```

```python
render(mol, dof=True, orient=False)
render(mol, dof=True, dof_strength=6.0, orient=False)
```

---

# Structural Overlay

Overlay two structures to compare them. When both molecules have the same atoms in the same order, alignment is direct (index-based Kabsch). When atom counts or elements differ, the largest shared connected substructure is found automatically and used as the alignment basis.

| Default | Custom colour | Rotation GIF |
|---------|---------------|--------------|
| ![Default overlay](../../../examples/images/isothio_overlay.svg) | ![Custom colour overlay](../../../examples/images/isothio_overlay_custom.svg) | ![Overlay rotation GIF](../../../examples/images/isothio_overlay.gif) |

```bash
xyzrender isothio_xtb.xyz --overlay isothio_uma.xyz -c 1 --hy -o isothio_overlay_rot.svg --gif-rot -go isothio_overlay.gif
xyzrender isothio_xtb.xyz --overlay isothio_uma.xyz -c 1 --overlay-color green -a 2 --no-orient -o isothio_overlay_custom.svg
```

From Python:

```python
from xyzrender import load, render, render_gif

mol1 = load("isothio_xtb.xyz", charge=1)
mol2 = load("isothio_uma.xyz", charge=1)

render(mol1, overlay=mol2)                        # overlay mol2 onto mol1
render(mol1, overlay=mol2, overlay_color="green") # custom overlay color
render_gif(mol1, overlay=mol2, gif_rot="y")       # spinning overlay GIF
```

## Cross-molecule overlay

Molecules with different atom counts or elements can be overlaid directly. The shared scaffold is found automatically and used as the alignment basis:

| Cross-molecule overlay | Rotation |
|------------------------|----------|
| ![Cross-molecule overlay](../../../examples/images/isothio_overlay_cross.svg) | ![rotating](../../../examples/images/isothio_overlay_cross.gif) |

```bash
xyzrender isothio_xtb.xyz --overlay isothio_bridged.xyz -c 1 --hy --gif-rot
```

```python
mol1 = load("isothio_xtb.xyz", charge=1)
mol2 = load("isothio_bridged.xyz")
render(mol1, overlay=mol2)  # aligns on largest shared connected substructure
```

| Flag | Description |
|------|-------------|
| `--overlay FILE` | Second structure to overlay (RMSD-aligned onto the primary). Molecules can have different atom counts — alignment uses the largest shared connected substructure |
| `--overlay-color COLOR` | Color for the overlay structure (hex or named, default: contrasting) |
| `--align-atoms INDICES` | 1-indexed atom subset for Kabsch alignment (min 3), e.g. `1,2,3` or `1-6`. Only for same-atom-count overlays |

---

# Conformer Ensemble

Visualise multiple conformers from a multi-frame XYZ trajectory overlaid on a single reference frame. Each frame is RMSD-aligned onto the reference (frame 0) via the Kabsch algorithm. By default, conformers render with standard CPK atom colours. Use `--ensemble-color` to apply a continuous palette or a fixed colour.

| Default (CPK) | Spectral + opacity |
|---------------|--------------------|
| ![Default ensemble](../../../examples/images/triphenylbenzol_ensemble.svg) | ![Custom ensemble](../../../examples/images/triphenylbenzol_ensemble_custom.svg) |

```bash
xyzrender triphenylbenzol.xyz --ensemble -o triphenylbenzol_ensemble.svg
xyzrender triphenylbenzol.xyz --ensemble --align-atoms 21,22,23 --ensemble-color spectral --opacity 0.4 -o triphenylbenzol_ensemble_custom.svg
```

From Python:

```python
from xyzrender import render

render("triphenylbenzol.xyz", ensemble=True)                                          # CPK colours
render("triphenylbenzol.xyz", ensemble=True, ensemble_palette="spectral")             # spectral palette
render("triphenylbenzol.xyz", ensemble=True, ensemble_color="#FF0000")                # single colour
render("triphenylbenzol.xyz", ensemble=True, ensemble_palette="viridis", opacity=0.4) # faded
render("triphenylbenzol.xyz", ensemble=True, align_atoms=[21, 22, 23])               # align on subset
render("triphenylbenzol.xyz", ensemble=True, max_frames=10)                          # limit frames
```

## Alignment subset

By default the Kabsch fit uses all atoms. Use `--align-atoms` to fit on a subset (minimum 3 atoms to define a plane); the rotation is still applied to every atom. This works for both `--ensemble` and `--overlay`.

```bash
xyzrender triphenylbenzol.xyz --ensemble --align-atoms 21,22,23 -o ensemble_align.svg
xyzrender isothio_xtb.xyz --overlay isothio_uma.xyz --align-atoms 1-6 -o overlay_align.svg
```

| Flag | Description |
|------|-------------|
| `--ensemble` | Enable ensemble mode for multi-frame XYZ trajectories |
| `--ensemble-color VALUE` | Palette name (`viridis`, `spectral`, `coolwarm`), a single colour, or comma-separated colours |
| `--opacity FLOAT` | Opacity for non-reference conformers (0–1, default: 1.0) |
| `--align-atoms INDICES` | 1-indexed atom subset for alignment (min 3), e.g. `21,22,23` or `1-6` |

---

# Animations

All GIF output defaults to `{input_basename}.gif`. Override with `-go`.

## Rotation GIF

| Rotation (y) | Rotation (xy) |
|-------------|--------------|
| ![Rotation (y)](../../../examples/images/caffeine.gif) | ![Rotation (xy)](../../../examples/images/caffeine_xy.gif) |

```bash
xyzrender caffeine.xyz --gif-rot -go caffeine.gif        # y-axis (default)
xyzrender caffeine.xyz --gif-rot xy -go caffeine_xy.gif  # xy axes
```

Available rotation axes: `x`, `y`, `z`, `xy`, `xz`, `yz`, `yx`, `zx`, `zy`. Prefix `-` to reverse (e.g. `-xy`). For crystal inputs, a 3-digit Miller index (e.g. `111`) rotates around the corresponding lattice direction.

Control speed and length:

```bash
xyzrender caffeine.xyz --gif-rot --gif-fps 20 --rot-frames 60 -go fast.gif
```

## TS vibration

| TS vibration (mn-h2) | TS + rotation (bimp) |
|---------------------|---------------------|
| ![TS vibration (mn-h2)](../../../examples/images/mn-h2.gif) | ![TS + rotation (bimp)](../../../examples/images/bimp.gif) |

```bash
xyzrender mn-h2.log --gif-ts -go mn-h2.gif
xyzrender bimp.out --gif-rot --gif-ts --vdw 84-169 -go bimp.gif
```

## Trajectory

```{image} ../../../examples/images/bimp_trj.gif
:width: 50%
:alt: Trajectory animation
```

```bash
xyzrender bimp.out --gif-trj --ts -go bimp_trj.gif
```

---

# Transition States and NCI

xyzrender uses [xyzgraph](https://github.com/aligfellow/xyzgraph) for molecular graph construction from Cartesian coordinates — determining bond connectivity, bond orders, detecting aromatic rings, and non-covalent interactions. It also provides element data (van der Waals radii, atomic numbers) used throughout rendering.

Transition state analysis uses [graphRC](https://github.com/aligfellow/graphRC) for internal coordinate vibrational mode analysis. Given a QM output file (ORCA, Gaussian, etc.), graphRC identifies which bonds are forming or breaking at the transition state with `--ts`. These are rendered as dashed bonds. graphRC is also used to generate TS vibration frames for `--gif-ts` animations.

## Transition states

`--ts` auto-detects forming/breaking bonds from QM output. TS bonds are rendered as dashed lines.

| Auto TS | Manual TS bond |
|---------|---------------|
| ![Auto TS](../../../examples/images/sn2_ts.svg) | ![Manual TS bond](../../../examples/images/sn2_ts_man.svg) |

```bash
xyzrender sn2.out --ts --hy -o sn2_ts.svg
xyzrender sn2.out --ts-bond "1-2" -o sn2_ts_man.svg    # specific bond only
xyzrender sn2.out --ts --ts-color dodgerblue -o sn2_ts_blue.svg
```

## QM output files

| ORCA output | Gaussian TS |
|-------------|------------|
| ![ORCA output](../../../examples/images/bimp_qm.svg) | ![Gaussian TS](../../../examples/images/mn-h2_qm.svg) |

```bash
xyzrender bimp.out -o bimp_qm.svg
xyzrender mn-h2.log --ts -o mn-h2_qm.svg
```

## NCI interactions (`--nci`)

`--nci` uses [xyzgraph](https://github.com/aligfellow/xyzgraph)'s `detect_ncis` to identify hydrogen bonds, halogen bonds, pi-stacking, and other non-covalent interactions from geometry. These are rendered as dotted bonds.

For pi-system interactions (e.g. pi-stacking, cation-pi), centroid dummy nodes are placed at the mean position of the pi-system atoms. For trajectory GIFs with `--nci`, interactions are re-detected per frame.

| Auto NCI | Manual NCI bond |
|----------|----------------|
| ![Auto NCI](../../../examples/images/nci.svg) | ![Manual NCI bond](../../../examples/images/nci_man.svg) |

```bash
xyzrender Hbond.xyz --hy --nci -o nci.svg                 # auto-detect all NCI
xyzrender Hbond.xyz --hy --nci-bond "8-9" -o nci_man.svg  # specific bond only
xyzrender Hbond.xyz --hy --nci --nci-color teal -o nci_teal.svg
```

## NCI + TS combined

| Default colours | Custom colours |
|-----------------|---------------|
| ![Default](../../../examples/images/bimp_ts_nci.svg) | ![Custom](../../../examples/images/bimp_ts_nci_custom.svg) |

```bash
xyzrender bimp.out --ts --nci --vdw 84-169 -o bimp_ts_nci.svg
xyzrender bimp.out --ts --nci -vdw 84-169 --ts-color magenta --nci-color teal -o bimp_ts_nci_custom.svg
```

---

# Molecular Orbitals

Render MO lobes from `.cube` files with `--mo`. The cube file contains both geometry and the orbital grid — no separate XYZ file needed.

When auto-orientation is active (default), the molecule is tilted 45° around the x-axis after alignment so lobes above and below the molecular plane are clearly visible. Use `--no-orient` to render in raw cube coordinates, or `-I` to use the [v viewer](https://github.com/briling/v) for interactive orientation.

Cube files are typically generated by [ORCA](https://www.faccts.de/docs/orca/6.1/manual/contents/utilitiesvisualization/utilities.html?q=orca_plot&n=0#orca-plot) (`orca_plot`) or Gaussian (`cubegen`).

| HOMO | LUMO |
|------|------|
| ![HOMO](../../../examples/images/caffeine_homo.svg) | ![LUMO](../../../examples/images/caffeine_lumo.svg) |

| HOMO + H (iso 0.03) | HOMO rotation |
|--------------------|--------------|
| ![HOMO + H (iso 0.03)](../../../examples/images/caffeine_homo_iso_hy.svg) | ![HOMO rotation](../../../examples/images/caffeine_homo.gif) |

```bash
xyzrender caffeine_homo.cube --mo -o caffeine_homo.svg
xyzrender caffeine_lumo.cube --mo --mo-colors maroon teal -o caffeine_lumo.svg
xyzrender caffeine_homo.cube --mo --hy --iso 0.03 -o homo_iso_hy.svg
xyzrender caffeine_homo.cube --mo --gif-rot -go caffeine_homo.gif
```

## Surface styles

All contour-based surfaces (MO, density, NCI) support alternative rendering styles via `--surface-style`:

| Mesh | Contour | Dot |
|------|---------|-----|
| ![Mesh](../../../examples/images/caffeine_homo_mesh.svg) | ![Contour](../../../examples/images/caffeine_homo_contour.svg) | ![Dot](../../../examples/images/caffeine_homo_dot.svg) |

```bash
xyzrender caffeine_homo.cube --mo --surface-style mesh
xyzrender caffeine_homo.cube --mo --surface-style contour
xyzrender caffeine_homo.cube --mo --surface-style dot
```

| Style | Description |
|-------|-------------|
| `solid` (default) | Filled surfaces with depth cueing |
| `mesh` | Warped grid lines emulating a 3D wireframe |
| `contour` | Iso-value contour rings showing surface depth |
| `dot` | Stippled contour rings (dots denser toward centre) |

## MO flags

| Flag | Description |
|------|-------------|
| `--mo` | Enable MO lobe rendering (required for `.cube` input) |
| `--iso` | Isosurface threshold (default: 0.05 — smaller value = larger lobes) |
| `--opacity` | Surface opacity multiplier (default: 1.0) |
| `--surface-style STYLE` | Surface rendering style: `solid`, `mesh`, `contour`, `dot` |
| `--mo-colors POS NEG` | Lobe colors as hex or [named color](https://matplotlib.org/stable/gallery/color/named_colors.html) (default: `steelblue` `maroon`) |
| `--flat-mo` | Disable depth classification — render all lobes as front-facing |
| `--mo-blur SIGMA` | Gaussian blur sigma for lobe smoothing (default: 0.8, ADVANCED) |
| `--mo-upsample N` | Upsample factor for contour resolution (default: 3, ADVANCED) |

---

# Electron Density and ESP

| Flag | Description |
|------|-------------|
| `--esp CUBE` | ESP cube file to map onto the density isosurface |
| `--iso` | Isosurface threshold for the density surface (default: 0.05) |
| `--opacity` | Surface opacity multiplier (default: 1.0) |

---

# NCI Surface

All NCI surface flags:

| Flag | Description |
|------|-------------|
| `--nci-surf GRAD_CUBE` | Reduced density gradient cube file (enables NCI surface rendering) |
| `--nci-mode MODE` | Coloring: `avg` (default), `pixel`, `uniform`, or a colour name/hex |
| `--iso` | RDG isovalue threshold (default: 0.5 — larger value = more surface) |
| `--opacity` | Surface opacity multiplier (default: 1.0) |
| `--surface-style STYLE` | `solid` or `mesh` recommended; `contour`, `dot` also available. These use avg lobe colour |
| `--nci-cutoff CUTOFF` | Density magnitude cutoff (advanced — not needed for standard NCIPLOT output) |

Sample structures from [NCIPlot](https://github.com/juliacontrerasgarcia/NCIPLOT-4.2/tree/master/tests).

---

# Convex hull

Draw the convex hull of selected atoms as semi-transparent facets — useful for aromatic rings, coordination spheres, or any subset of atoms. Facets are depth-sorted for correct occlusion. Hull edges that do not coincide with bonds are drawn as thin lines for better 3D perception; disable with `--no-hull-edge`.

Use `--hull` from the CLI (no args = all heavy atoms, `rings` to auto-detect aromatic rings, or 1-indexed atom ranges for subsets), or from Python pass `hull=` to `render()`: `True` for all heavy atoms, `"rings"` for automatic aromatic ring detection (one hull per ring), a flat list of 1-indexed atom indices for one hull, or a list of lists for multiple hulls with optional per-subset `hull_color=["red", "blue"]`. A default color palette cycles automatically for multiple subsets.

| Benzene ring | Anthracene (all ring carbons) | CoCl₆ octahedron |
|--------------|-------------------------------|------------------|
| ![benzene hull](../../../examples/images/benzene_ring_hull.svg) | ![anthracene hull](../../../examples/images/anthracene_hull.svg) | ![CoCl6 hull](../../../examples/images/CoCl6_octahedron_hull.svg) |

| Anthracene ring | Anthracene rot | Auto rings (`hull="rings"`) |
|--------------|------------------|----------------------------|
| ![anthracene hull](../../../examples/images/anthracene_hull_one.svg) | ![anthracene hull](../../../examples/images/anthracene_hull.gif) | ![mnh hull rings](../../../examples/images/mnh_hull_rings.svg) |

**CLI:**

```bash
# All heavy atoms:
xyzrender benzene.xyz --hull -o benzene_hull.svg

# Single subset (1-indexed atom range):
xyzrender benzene.xyz --hull 1-6 --hull-color steelblue --hull-opacity 0.35 -o benzene_ring_hull.svg

# Multiple subsets with per-hull colors:
xyzrender anthracene.xyz --hull 1-6 4,6-10 8,10-14 -o anthracene_hull.svg

# Auto-detect aromatic rings (one hull per ring, colours cycle automatically):
xyzrender mn-h2.log --ts --hull rings --hull-color teal -o mnh_hull_rings.svg
```

**Python:**

```python
from xyzrender import load, render, render_gif

# Single subset: one hull (e.g. benzene ring carbons, 1-indexed)
benzene = load("structures/benzene.xyz")
render(benzene, hull=[1, 2, 3, 4, 5, 6],
       hull_color="steelblue", hull_opacity=0.35, output="images/benzene_ring_hull.svg")
render_gif(benzene, gif_rot="y", hull=[1, 2, 3, 4, 5, 6],
           hull_color="steelblue", hull_opacity=0.35, output="images/benzene_ring_hull.gif")

# Multiple subsets with per-subset colors (1-indexed):
render(mol, hull=[[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]],
       hull_color=["steelblue", "coral"], hull_opacity=0.35,
       output="anthracene_hull.svg")

# Auto-detect aromatic rings — each ring gets its own hull:
render(mol, hull="rings", hull_color="teal")
```

**Options (passed to `render()`):**

| Option | Description |
|--------|-------------|
| `hull` | `True` = all heavy atoms; `"rings"` = auto-detect aromatic rings (one hull per ring); flat list = one subset; list of lists = multiple hulls |
| `hull_color` | Single string or list of strings for per-subset colours (default palette cycles automatically) |
| `hull_opacity` | Fill opacity for all hull surfaces |
| `hull_edge` | Draw non-bond hull edges as thin lines (default: `True`) |
| `hull_edge_width_ratio` | Edge stroke width as fraction of bond width |

Examples in this section are generated from `examples/examples.ipynb` (benzene, anthracene, CoCl₆).

---

# Crystal Structures

## extXYZ unit cell

Draw the unit cell box for periodic structures from an extXYZ file with a `Lattice=` header. The cell is detected automatically — no extra flag needed.

| Unit cell | Cell rotation | Custom color |
|-----------|--------------|-------------|
| ![Unit cell](../../../examples/images/caffeine_cell.svg) | ![Cell rotation](../../../examples/images/caffeine_cell.gif) | ![Custom color](../../../examples/images/caffeine_cell_custom.svg) |

| Default | No ghost atoms | No cell box |
|---------|---------------|------------|
| ![Default](../../../examples/images/NV63_cell.svg) | ![No ghost atoms](../../../examples/images/NV63_cell_no_ghosts.svg) | ![No cell box](../../../examples/images/NV63_cell_no_cell.svg) |

| Caffeine 2×2×1 (ghosts) | Caffeine 2×2×1 (ghosts + `--hy`) | NV63 2×2×1 (ghosts) |
|---|---|---|
| ![ghosts](../../../examples/images/caffeine_cell_supercell_221.svg) | ![ghosts + hy](../../../examples/images/caffeine_cell_supercell_221_hy.svg) | ![ghosts](../../../examples/images/NV63_cell_supercell_221.svg) |

```bash
xyzrender caffeine_cell.xyz -o caffeine_cell.svg
xyzrender caffeine_cell.xyz --gif-rot -go caffeine_cell.gif
xyzrender caffeine_cell.xyz --cell-color maroon -o caffeine_cell_custom.svg
xyzrender caffeine_cell.xyz --supercell 2 2 1 -o caffeine_cell_supercell_221.svg
xyzrender caffeine_cell.xyz --supercell 2 2 1 --hy -o caffeine_cell_supercell_221_hy.svg
xyzrender NV63_cell.xyz --no-ghosts --no-axes -o NV63_cell_no_ghosts.svg
xyzrender NV63_cell.xyz --no-cell -o NV63_cell_no_cell.svg
xyzrender NV63_cell.xyz --supercell 2 2 1 --no-axes -o NV63_cell_supercell_221.svg
```

## Crystal flags

| Flag | Description |
|------|-------------|
| `--crystal [{vasp,qe}]` | Load VASP/QE structure via phonopy; format auto-detected or explicit |
| `--cell` | Force cell rendering for extXYZ (usually not needed) |
| `--no-cell` | Hide the unit cell box |
| `--ghosts` / `--no-ghosts` | Show/hide ghost (periodic image) atoms outside the cell |
| `--ghost-opacity` | Opacity of ghost atoms/bonds (default: 0.5) |
| `--axes` / `--no-axes` | Show/hide the a/b/c axis arrows |
| `--cell-color` | Unit cell box color (hex or named, default: `gray`) |
| `--cell-width` | Unit cell box line width (default: 2.0) |
| `--axis HKL` | Orient looking down a crystallographic direction (e.g. `111`, `001`) |
| `--supercell M N L` | Repeat the unit cell `M×N×L` times along a/b/c (requires lattice/unit-cell data; default: `1 1 1`) |

---

# Annotations

## Atom indices

Add atom index labels centred on every atom in the SVG with `--idx`. Three format options:

| Symbol + index (default) | Index only |
|-------------------------|-----------|
| ![Symbol + index](../../../examples/images/caffeine_idx.svg) | ![Index only](../../../examples/images/caffeine_idx_n.svg) |

```bash
xyzrender caffeine.xyz --idx                         # symbol + index (C1)
xyzrender caffeine.xyz --hy --idx n --label-size 25  # index only (1)
xyzrender caffeine.xyz --hy --idx s                  # symbol only (C)
```

## SVG annotations (`-l`)

Annotate bonds, angles, atoms, or dihedrals with computed or custom text. The **last token** of each spec determines its type. All atom indices are **1-based**. `-l` is repeatable.

| Spec | SVG output |
|------|------------|
| `-l 1 2 d` | Distance text at the 1–2 bond midpoint |
| `-l 1 d` | Distance on every bond incident to atom 1 |
| `-l 1 2 3 a` | Arc at atom 2 (vertex) + angle value |
| `-l 1 2 3 4 t` | Colored line 1-2-3-4 + dihedral value near bond 2–3 |
| `-l 1 +0.512` | Custom text near atom 1 |
| `-l 1 2 NBO` | Custom text at the 1–2 bond midpoint |

| Distances + angles + dihedrals | Custom annotation |
|-------------------------------|------------------|
| ![Distances + angles + dihedrals](../../../examples/images/caffeine_dihedral.svg) | ![Custom annotation](../../../examples/images/caffeine_labels.svg) |

```bash
xyzrender caffeine.xyz -l 13 6 9 4 t -l 1 a -l 14 d -l 7 12 8 a -l 11 d
xyzrender caffeine.xyz -l 1 best -l 2 "NBO: 0.4"
```

## Bulk label file (`--label`)

Same syntax as `-l`, one spec per line. Lines whose first token is not an integer (e.g. CSV headers) are silently skipped. Comment lines (`#`) and quoted labels are supported.

```{image} ../../../examples/images/sn2_ts_label.svg
:width: 50%
:alt: Bulk label file example
```

```text
# sn2_label.txt
2 1 d
1 22 d
2 1 22 a
```

```bash
xyzrender sn2.out --ts --label sn2_label.txt --label-size 40
```

## Stereochemistry (`--stereo`)

Add stereochemistry labels derived from 3D geometry (via [xyzgraph](https://github.com/aligfellow/xyzgraph)). Detects R/S point chirality, E/Z double bonds, axial, planar (metallocene and CIP), and helical chirality.

| Isothiocyanate (R/S, E/Z, planar) | TS with stereo (Mn-H₂) |
|---|---|
| ![isothio stereo](../../../examples/images/isothio_stereo.svg) | ![mn-h2 ts stereo](../../../examples/images/mn-h2_ts_stereo.svg) |

```bash
xyzrender isothio_xtb.xyz -c 1 --stereo
xyzrender mn-h2.log --ts --stereo --no-orient
```

Filter to specific stereo classes with a comma-separated list:

```bash
xyzrender mol.xyz --stereo point,ez      # only R/S and E/Z
xyzrender mol.xyz --stereo point          # only R/S
```

Valid classes: `point`, `ez`, `axis`, `plane`, `helix`.

Two display modes for R/S labels: `--stereo-style atom` (default, centered on atom) and `--stereo-style label` (offset like other annotations).

> **Note:** `--stereo` with `--idx` will overlap labels on stereocenters since both draw text at the atom position. Use `--stereo-style label` to offset R/S labels if combining with `--idx`.

## Atom property colormap (`--cmap`)

Color atoms by a per-atom scalar value (e.g. partial charges) using a Viridis-like colormap.

| Mulliken charges | Symmetric range |
|-----------------|----------------|
| ![Mulliken charges](../../../examples/images/caffeine_cmap.gif) | ![Symmetric range](../../../examples/images/caffeine_cmap.svg) |

The colormap file has two columns — **1-indexed atom number** and value. Any extension works. Header lines (first token not an integer), blank lines, and `#` comment lines are silently skipped.

```text
# charges.txt
1  +0.512
2  -0.234
3   0.041
```

```bash
xyzrender caffeine.xyz --hy --cmap caffeine_charges.txt --gif-rot -go caffeine_cmap.gif
xyzrender caffeine.xyz --hy --cmap caffeine_charges.txt --cmap-range -0.5 0.5
```

- Atoms **in the file**: colored by Viridis (dark purple → blue → green → bright yellow)
- Atoms **not in the file**: white (`#ffffff`). Override with `"cmap_unlabeled"` in a custom JSON preset
- Range defaults to min/max of provided values; use `--cmap-range vmin vmax` for a symmetric scale

## Vector arrows

Overlay arbitrary 3D vectors as arrows on the rendered image via a JSON file. Useful for dipole moments, forces, electric fields, transition vectors, etc.

| Dipole moment | Rotation |
|-------------|-------------|
| ![dip](../../../examples/images/ethanol_dip.svg) | ![dip rot](../../../examples/images/ethanol_dip.gif) |

```bash
xyzrender ethanol.xyz --vector ethanol_dip.json -o ethanol_dip.svg
```

Each entry in the JSON array defines one arrow:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `vector` | `[vx, vy, vz]` | *required* | Three numeric components (x,y,z). Use the same coordinate units as the input (Å). Example: `[1.2, 0.0, 0.5]`. |
| `origin` | `"com"` / integer / `[x,y,z]` | `"com"` | Tail location: `"com"` = molecule centroid; integer = 1-based atom index from the input XYZ; list = explicit coordinates. |
| `color` | `"#rrggbb"` / named | `"#444444"` | Arrow color. Accepts hex (`#e63030`) or CSS color names (`steelblue`). |
| `label` | string | `""` | Text placed near the arrowhead (e.g. "μ"). Suppressed when a dot or × symbol is rendered (see below). |
| `scale` | float | `1.0` | Per-arrow multiplier applied on top of `--vector-scale`. Final arrow length = `scale * --vector-scale * |vector|`. |

**Near-Z rendering (dot and × symbols)**

When an arrow points nearly along the viewing axis its 2D projected length becomes shorter than the arrowhead size.  In that case a compact symbol is drawn at the arrow origin instead:

- **•** (filled dot) — the tip is closer to the viewer (arrow coming out of the screen).
- **×** (two crossed lines) — the tip is farther from the viewer (arrow going into the screen).

The label is suppressed for these compact symbols.  Once the viewing angle changes enough for the projected shaft to exceed the arrowhead size, the full arrow and label are restored automatically.  This behaviour is particularly visible in GIF rotations: as a lattice axis arrow passes through the viewing direction it transitions smoothly between dot, ×, and full-arrow rendering.

**Example — Dipole Moment:**

```json
{
  "anchor": "center",
  "vectors": [
    {
      "origin": "com",
      "vector": [
        1.0320170291976951,
        -0.042708195030485986,
        -1.332397645862797
      ],
      "color": "red",
      "label": "μ"
    }
  ]
}
```

**Example — forces on heavy atoms due to E field:**

| Forces | Rotation |
|-------------|-------------|
| ![forces](../../../examples/images/ethanol_forces_efield.svg) | ![forces rot](../../../examples/images/ethanol_forces_efield.gif) |

```text
{
  "anchor": "center",
  "units": "eV/Angstrom",
  "vectors": [
    {
      "origin": 1,
      "vector": [-0.318, -0.438, 0.368],
      "color": "red"
    },
    ...
  ]
}
```

## Bond measurements (`--measure`)

Print bonded distances, angles, and dihedral angles to stdout. The SVG is still rendered as normal.

```bash
xyzrender ethanol.xyz --measure          # all: distances, angles, dihedrals
xyzrender ethanol.xyz --measure d        # distances only
xyzrender ethanol.xyz --measure d a      # distances and angles
```

```text
Bond Distances:
     C1 - C2     1.498Å
     C1 - H4     1.104Å
Bond Angles:
     C2 - C1 - H5     109.62°
Dihedral Angles:
     H5 - C1 - C2 - O3      -55.99°
```

---

# Highlight & Molecule Color

Color specific atom groups to visualise partitioning, active sites, or any structural decomposition. Multiple highlight groups can be used simultaneously, each with its own color. A flat molecule color (`--mol-color`) can serve as a neutral base for highlights to paint on top of.

All atom indices are **1-indexed** and accept comma-range syntax (`"1-5,8,12"`).

## Single-group highlight

Color a set of atoms and their connecting bonds. Without an explicit color, the first palette color (orchid) is used.

| Default (orchid) | Custom colour | Rotation |
|------------------|---------------|----------|
| ![hl](../../../examples/images//caffeine_hl.svg) | ![hl custom](../../../examples/images//caffeine_hl_custom.svg) | ![hl rot](../../../examples/images//caffeine_hl.gif) |

```bash
xyzrender caffeine.xyz --hl "1-3,7"                    # orchid (default)
xyzrender caffeine.xyz --hl "1-3,7" lightseagreen      # custom colour
xyzrender caffeine.xyz --hl "1-3,7" --gif-rot -go hl.gif  # works in GIFs
```

### Python

```python
render(mol, highlight="1-3,7")                          # string
render(mol, highlight=[1, 2, 3, 7])                     # list
render(mol, highlight=[("1-3,7", "lightseagreen")])     # with explicit color
```

## Molecule color

Paint all atoms and bonds a single flat color, replacing the default CPK element coloring.

```bash
xyzrender caffeine.xyz --mol-color gray --hy
```

### Python

```python
render(mol, mol_color="gray", hy=True)
```

## Multi-group highlight

Highlight multiple atom groups with different colors. Each `--hl` flag specifies atoms and an optional color. Groups without a color are auto-assigned from the preset palette.

```bash
# Two groups with explicit colors
xyzrender caffeine.xyz --hl "1-3,5,10,11,15,16,19,21" maroon --hl "4,6-9,12-14,17,18,20,22-24" teal --hy

# Auto-color from palette (orchid, mediumseagreen, goldenrod, ...)
xyzrender caffeine.xyz --hl "1-5" --hl "6-10" --hl "11-14" --hy
```

| Multi-group (explicit colors) | Mol color + highlight + indices |
|-------------------------------|-------------------------------|
| ![multi hl](../../../examples/images/caffeine_multi_hl.svg) | ![mol color hl idx](../../../examples/images//caffeine_mol_color_hl_idx.svg) |

### Python

```python
# Multi-group with explicit colors
render(mol, highlight=[("1-3,5,10,11,15,16,19,21", "maroon"),
                       ("4,6-9,12-14,17,18,20,22-24", "teal")], hy=True)

# Auto-color from palette
render(mol, highlight=["1-5", "10-15"])

# List-of-lists form
render(mol, highlight=[[1, 2, 3, 4, 5], [10, 11, 12, 13, 14, 15]])

# With explicit colors via list[int]
render(mol, highlight=[([1, 2, 3, 4, 5], "blue"), ([10, 11, 12], "red")])
```

## Molecule color + highlight

Use `--mol-color` as a neutral base, then `--hl` to pick out specific regions. Highlight overrides the molecule color for both atoms and bonds.

```bash
xyzrender caffeine.xyz --hl "1-3,5,10,11,15,16,19,21" --mol-color mediumseagreen --hy --idx n
```

### Python

```python
render(mol, mol_color="mediumseagreen", highlight=[1, 2, 3, 5, 10, 11, 15, 16, 19, 21],
       hy=True, idx="n")
```

## Preset palette

The default highlight palette is defined in `default.json` and can be customised in a preset file:

```json
"highlight_colors": ["orchid", "mediumseagreen", "goldenrod", "coral", "mediumpurple", "hotpink"]
```

Groups are assigned colors in order: first group gets `orchid`, second `mediumseagreen`, etc. The palette cycles if there are more groups than colors.

---

# Style Regions

Render subsets of atoms with a different preset — useful for highlighting QM/MM regions, active sites, or multi-fragment systems. Each region specifies atom indices and a preset name (or JSON config path).

The base config controls global properties (canvas, fog, background). Regions override per-atom/bond properties (atom size, colors, bond width, gradient) for their atoms. Structural overlays (TS/NCI bonds, centroids) always use the base config.

| Tube + ball-stick region | Two regions | Multi-fragment with NCI |
|--------------------------|-------------|------------------------|
| ![region](../../../examples/images/caffeine_region.svg) | ![two regions](../../../examples/images/caffeine_two_region.svg) | ![bimp regions](../../../examples/images/bimp_regions.svg) |

```bash
# Ball-stick base, tube for atoms 84–165
xyzrender mol.xyz --region "84-165" tube

# Tube base, ball-stick for the QM region
xyzrender mol.xyz --config tube --region "1-20" default

# Multiple regions with different presets
xyzrender mol.xyz --config tube --region "1-20" default --region "21-40" flat

# Multi-fragment: NCI detection + highlight + vdW + two regions
xyzrender bimp.xyz --no-orient --region "84-165" tube --nci --hl "84-165" --vdw "84-165"
```

From Python:

```python
from xyzrender import load, render

mol = load("mol.xyz")

# Single region
render(mol, config="tube", regions=[("1-20", "default")])

# Multiple regions — indices are 1-indexed (strings or lists)
render(mol, config="tube", regions=[("1-20", "default"), ("21-40", "flat")])

# 1-indexed list form
render(mol, config="tube", regions=[([1, 2, 3, 4], "default")])
```

## Combining with other overlays

Style regions compose with all existing overlays — highlight, vdW spheres, NCI detection, TS bonds, and annotations. This makes it easy to build up complex visualisations from simple flags.

```bash
# QM/MM: tube for the MM region, ball-stick QM region with highlight + vdW + NCI
xyzrender complex.xyz --region "84-165" tube --hl "84-165" steelblue --vdw "84-165" --nci

# Active site: wire background, highlighted residue with vdW spheres
xyzrender protein.xyz --config wire --region "1-30" default --hl "10-15" --vdw "10-15"
```

```python
render(mol, config="wire",
       regions=[("84-165", "tube")],
       highlight=[("84-165", "steelblue")],
       vdw=list(range(84, 166)))
```

Highlight recolours atoms regardless of their region style, vdW spheres use the base config's sphere settings, and NCI/TS bonds always render in the base style — so everything stays visually consistent even with multiple regions active.

## Bond coloring

Element-coloured bonds and cylinder shading can be used with any preset.

```bash
xyzrender mol.xyz --bond-by-element                  # half-bond split by atom colour
xyzrender mol.xyz --bond-gradient                    # cylinder shading (3D tube look)
xyzrender mol.xyz --config tube --no-bond-by-element # uniform colour tube
```

```python
render(mol, bond_color_by_element=True)  # half-bond element colouring
render(mol, bond_gradient=True)          # cylinder shading
```

The tube and wire presets enable both by default. The cylinder shading uses the same `get_gradient_colors` system as atom radial gradients — controlled by `hue_shift_factor`, `light_shift_factor`, and `saturation_shift_factor` in the preset JSON.

## How two configs coexist

- Each atom maps to either a region config or the base config via a per-atom lookup
- Bonds between two atoms in the **same** region use that region's bond style
- **Boundary bonds** (one atom in region, one not) use the base config
- **TS/NCI bonds** always use the base config — they are structural overlays, not molecular skeleton
- **NCI centroids** (`*` nodes) always use the base config

| Flag | Description |
|------|-------------|
| `--region ATOMS CONFIG` | Render atom subset with a different preset (repeatable) |
| `--bond-by-element` / `--no-bond-by-element` | Color bonds by endpoint atom colors |
| `--bond-gradient` / `--no-bond-gradient` | Cylinder shading on bonds |

---

# Atom Colormap

Color atoms by a per-atom scalar value (e.g. partial charges, NMR shifts, Fukui indices) using a colormap palette.

| Mulliken charges (rotation) | Symmetric range | With colorbar |
|----------------------------|----------------|---------------|
| ![Mulliken charges (rotation)](../../../examples/images/caffeine_cmap.gif) | ![Symmetric range](../../../examples/images/caffeine_cmap.svg) | ![With colorbar](../../../examples/images/caffeine_cmap_colorbar.svg) |

```bash
xyzrender caffeine.xyz --hy --cmap caffeine_charges.txt --gif-rot -go caffeine_cmap.gif
xyzrender caffeine.xyz --hy --cmap caffeine_charges.txt --cmap-range -0.5 0.5
xyzrender caffeine.xyz --hy --cmap caffeine_charges.txt --cbar
```

The colormap file has two columns — **1-indexed atom number** and value. Any extension works. Header lines (first token not an integer), blank lines, and `#` comment lines are silently skipped.

```text
# charges.txt
1  +0.512
2  -0.234
3   0.041
```

- Atoms **in the file**: colored by the selected palette (default: Viridis — dark purple → blue → green → bright yellow)
- Atoms **not in the file**: white (`#ffffff`). Override with `"cmap_unlabeled"` in a custom JSON preset
- Range defaults to min/max of provided values; use `--cmap-range vmin vmax` for an explicit range or `--cmap-symm` for a symmetric range about zero

| Flag | Description |
|------|-------------|
| `--cmap FILE` | Path to colormap data file (two-column: atom index, value) |
| `--cmap-range VMIN VMAX` | Override colormap range (useful for symmetric scales, e.g. `-0.5 0.5`) |
| `--cmap-symm` | Symmetric range about zero: `[-max(|v|), +max(|v|)]` |
| `--cmap-palette NAME` | Colormap palette (default: `viridis`) |
| `--cbar` | Add a vertical colorbar on the right showing the data range |
| `--label-size PT` | Font size for colorbar tick labels (and all other labels) |

---

# Core API¶

# Core API[¶](#module-xyzrender.api "Link to this heading")

High-level Python API for xyzrender.

Typical usage in a Jupyter notebook:

```
from xyzrender import load, render, render_gif

mol = load("mol.xyz")
render(mol)  # displays inline in Jupyter
render(mol, hy=True)  # show all hydrogens
render(mol, atom_scale=1.5, bond_width=8)
render(mol, mo=True, iso=0.05)  # MO surface (mol loaded from .cube)
render(mol, nci="grad.cube")  # NCI surface

# Short-form path string (loads with defaults):
render("mol.xyz")

# Reuse a style config:
cfg = build_config("flat", atom_scale=1.5)
render(mol1, config=cfg)
render(mol2, config=cfg)
```

For GIFs use [`render_gif()`](#xyzrender.api.render_gif "xyzrender.api.render_gif"):

```
render_gif("mol.xyz", gif_rot="y")
render_gif("trajectory.xyz", gif_trj=True)
render_gif("ts.xyz", gif_ts=True)
```

class xyzrender.api.EnsembleFrames(*positions*, *colors*, *opacities*, *conformer\_graphs=None*, *reference\_idx=0*)[[source]](../_modules/xyzrender/api.html#EnsembleFrames)[¶](#xyzrender.api.EnsembleFrames "Link to this definition")
:   Bases: `object`

    Per-conformer data for an ensemble loaded with `load(ensemble=True)`.

    Kept separate from `Molecule.graph` (which holds only the reference frame)
    so the graph always represents a single n\_atoms structure regardless of
    ensemble size. Consumers (render, render\_gif) build the merged multi-
    conformer graph lazily from these arrays.

    positions[¶](#xyzrender.api.EnsembleFrames.positions "Link to this definition")
    :   Stacked conformer positions, shape `(n_conformers, n_atoms, 3)`.
        All frames are RMSD-aligned onto the reference frame.
        Contiguous memory allows vectorised rotation across all conformers
        simultaneously (single matmul for GIF frames).

    colors[¶](#xyzrender.api.EnsembleFrames.colors "Link to this definition")
    :   Resolved hex color string per conformer (`None` = use CPK).

    opacities[¶](#xyzrender.api.EnsembleFrames.opacities "Link to this definition")
    :   Per-conformer opacity override (`None` = fully opaque).

    conformer\_graphs[¶](#xyzrender.api.EnsembleFrames.conformer_graphs "Link to this definition")
    :   Optional per-frame graphs for `rebuild=True` ensembles (topology
        can differ per frame). `None` means all frames share the reference
        topology.

    reference\_idx[¶](#xyzrender.api.EnsembleFrames.reference_idx "Link to this definition")
    :   Index into *positions* / *colors* / *opacities* that is the reference.

    colors: list[str | None][¶](#id0 "Link to this definition")

    conformer\_graphs: list[Graph] | None = None[¶](#id1 "Link to this definition")

    opacities: list[float | None][¶](#id2 "Link to this definition")

    positions: ndarray[¶](#id3 "Link to this definition")

    reference\_idx: int = 0[¶](#id4 "Link to this definition")

class xyzrender.api.Molecule(*graph*, *cube\_data=None*, *cell\_data=None*, *oriented=False*, *ensemble=None*, *threshold=1.0*)[[source]](../_modules/xyzrender/api.html#Molecule)[¶](#xyzrender.api.Molecule "Link to this definition")
:   Bases: `object`

    Container for a loaded molecular structure.

    Obtain via [`load()`](#xyzrender.api.load "xyzrender.api.load"). Pass directly to [`render()`](#xyzrender.api.render "xyzrender.api.render") or
    [`render_gif()`](#xyzrender.api.render_gif "xyzrender.api.render_gif") to avoid re-parsing the file.

    For ensemble molecules (`load(ensemble=True)`), `graph` holds only the
    reference conformer (n\_atoms nodes). The full per-conformer data lives in
    `ensemble`; the merged multi-conformer graph is built lazily at render time.

    cell\_data: [CellData](types.html#xyzrender.types.CellData "xyzrender.types.CellData") | None = None[¶](#xyzrender.api.Molecule.cell_data "Link to this definition")

    cube\_data: CubeData | None = None[¶](#xyzrender.api.Molecule.cube_data "Link to this definition")

    ensemble: [EnsembleFrames](#xyzrender.api.EnsembleFrames "xyzrender.api.EnsembleFrames") | None = None[¶](#xyzrender.api.Molecule.ensemble "Link to this definition")

    graph: Graph[¶](#xyzrender.api.Molecule.graph "Link to this definition")

    oriented: bool = False[¶](#xyzrender.api.Molecule.oriented "Link to this definition")

    threshold: float = 1.0[¶](#xyzrender.api.Molecule.threshold "Link to this definition")

    to\_xyz(*path*, *title=''*)[[source]](../_modules/xyzrender/api.html#Molecule.to_xyz)[¶](#xyzrender.api.Molecule.to_xyz "Link to this definition")
    :   Write the molecule to an XYZ file.

        If the molecule carries `cell_data` (e.g. loaded with `cell=True`
        or `crystal=...`), the file is written in extXYZ format with a
        `Lattice=` header so it can be reloaded with `load(..., cell=True)`.
        Ghost (periodic image) atoms are excluded.

        Parameters:
        :   - **path** (`str` | `PathLike`) – Output path — should end with `.xyz`.
            - **title** (`str`) – Comment line written as the second line of the file.

        Return type:
        :   `None`

xyzrender.api.load(*molecule*, *\**, *smiles=False*, *charge=0*, *multiplicity=None*, *kekule=False*, *rebuild=False*, *mol\_frame=0*, *ts\_detect=False*, *ts\_frame=0*, *nci\_detect=False*, *crystal=False*, *cell=False*, *quick=False*, *threshold=1.0*, *ensemble=False*, *reference\_frame=0*, *max\_frames=None*, *align\_atoms=None*, *ensemble\_color=None*, *ensemble\_palette=None*, *ensemble\_opacity=None*, *reference\_mol=None*)[[source]](../_modules/xyzrender/api.html#load)[¶](#xyzrender.api.load "Link to this definition")
:   Load a molecule from file (or SMILES string) and return a [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule").

    Parameters:
    :   - **molecule** (`str` | `PathLike`) – Path to the input file, or a SMILES string when *smiles* is `True`.
          Supported extensions: `.xyz`, `.cube`, `.mol`, `.sdf`,
          `.mol2`, `.pdb`, `.smi`, `.cif`, and any QM output
          supported by cclib.
        - **smiles** (`bool`) – Treat *molecule* as a SMILES string and generate 3-D geometry.
        - **charge** (`int`) – Formal molecular charge (0 = read from file when available).
        - **multiplicity** (`int` | `None`) – Spin multiplicity (`None` = read from file).
        - **kekule** (`bool`) – Convert aromatic bonds to alternating single/double (Kekulé form).
        - **rebuild** (`bool`) – Force xyzgraph distance-based bond detection even when the file
          provides explicit connectivity. When used with `ensemble=True`,
          each frame’s graph is rebuilt independently (for trajectories where
          bonding changes between frames).
        - **mol\_frame** (`int`) – Zero-based frame index for multi-record SDF files.
        - **ts\_detect** (`bool`) – Run graphRC transition-state detection (requires `xyzrender[ts]`).
        - **ts\_frame** (`int`) – Reference frame index for TS detection in multi-frame files.
        - **nci\_detect** (`bool`) – Detect non-covalent interactions with xyzgraph after loading.
          When used with `ensemble=True`, NCI detection is run on
          each frame independently.
        - **crystal** (`bool` | `str`) – Load as a periodic crystal structure via phonopy. Pass `True`
          to auto-detect the interface from the filename, or a string such
          as `"vasp"` or `"qe"` to specify explicitly.
        - **cell** (`bool`) – Read the periodic cell box from an extXYZ `Lattice=` header and
          store it on the returned [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule").
        - **quick** (`bool`) – Skip bond-order optimisation (`build_graph(quick=True)`). Use
          when you know bond orders will be suppressed at render time (e.g.
          `render(mol, bo=False)`). CIF and PDB-with-cell always use
          `quick=True` automatically regardless of this flag.
        - **threshold** (`float`) – Global bond-distance scaling factor (default 1.0). Multiplies
          all VDW-based bond-detection cutoffs in xyzgraph. Values > 1.0
          make bonds easier to detect (longer tolerance), < 1.0 stricter.
        - **ensemble** (`bool`) – Load as a multi-frame trajectory ensemble. All frames are
          RMSD-aligned onto *reference\_frame* and merged into a single graph.
        - **reference\_frame** (`int`) – Index of the reference frame for ensemble alignment (default: 0).
        - **max\_frames** (`int` | `None`) – Maximum number of frames to include (default: all).
        - **align\_atoms** (`str` | `list`[`int`] | `None`) – 1-indexed atom indices for Kabsch alignment subset (min 3).
          When given, the rotation is computed from this subset only
          but applied to all atoms.
        - **ensemble\_color** (`str` | `list`[`str`] | `None`) – Single color string or list of hex/named colors for conformers.
        - **ensemble\_palette** (`str` | `None`) – Named continuous colormap (`"viridis"`, `"spectral"`,
          `"coolwarm"`). Overrides *ensemble\_color*.
        - **ensemble\_opacity** (`float` | `None`) – Opacity for non-reference conformer atoms (0-1).
        - **reference\_mol** ([`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule") | `None`) – Optional pre-loaded (and possibly oriented) [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule") for the
          reference frame. When given, its graph and positions are used directly
          instead of loading the reference frame from *molecule*. This lets
          interactive orientation be applied before ensemble alignment.

    Return type:
    :   [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule")

xyzrender.api.measure(*molecule*, *modes=None*)[[source]](../_modules/xyzrender/api.html#measure)[¶](#xyzrender.api.measure "Link to this definition")
:   Return geometry measurements as a dict.

    Parameters:
    :   - **molecule** (`str` | `PathLike` | [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule")) – A [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule") object or a file path (loaded with defaults).
        - **modes** (`list`[`str`] | `None`) – Subset of `["d", "a", "t"]` for distances, angles, dihedrals.
          `None` (default) returns all three.

    Return type:
    :   `dict`

xyzrender.api.orient(*mol*)[[source]](../_modules/xyzrender/api.html#orient)[¶](#xyzrender.api.orient "Link to this definition")
:   Open molecule in v viewer to set orientation interactively.

    The user rotates the molecule and presses `z` to output coordinates,
    then `q` to quit. Atom positions are written back to `mol.graph`
    in-place. Sets `mol.oriented = True` so subsequent [`render()`](#xyzrender.api.render "xyzrender.api.render")
    calls skip PCA auto-orientation.

    For cube-file molecules the cube grid alignment is handled automatically
    at render time via Kabsch rotation from original cube atom positions to
    the updated graph positions.

    Parameters:
    :   **mol** ([`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule")) – Molecule returned by [`load()`](#xyzrender.api.load "xyzrender.api.load").

    Return type:
    :   `None`

xyzrender.api.render(*molecule*, *\**, *config='default'*, *canvas\_size=None*, *atom\_scale=None*, *bond\_width=None*, *atom\_stroke\_width=None*, *bond\_color=None*, *ts\_color=None*, *nci\_color=None*, *background=None*, *transparent=False*, *gradient=None*, *hue\_shift\_factor=None*, *light\_shift\_factor=None*, *saturation\_shift\_factor=None*, *fog=None*, *fog\_strength=None*, *label\_font\_size=None*, *vdw\_opacity=None*, *vdw\_scale=None*, *vdw\_gradient\_strength=None*, *hide\_bonds=False*, *bond\_cutoff=None*, *hy=None*, *no\_hy=False*, *bo=None*, *orient=None*, *ref=None*, *no\_cell=False*, *axes=True*, *axis=None*, *supercell=(1, 1, 1)*, *ghosts=None*, *cell\_color=None*, *cell\_width=None*, *ghost\_opacity=None*, *ts\_bonds=None*, *nci\_bonds=None*, *vdw=None*, *idx=False*, *cmap=None*, *cmap\_range=None*, *cmap\_symm=False*, *cbar=False*, *labels=None*, *label\_file=None*, *stereo=False*, *stereo\_style='atom'*, *vector=None*, *vector\_scale=None*, *vector\_color=None*, *opacity=None*, *mo=False*, *dens=False*, *esp=None*, *nci=None*, *iso=None*, *mo\_pos\_color=None*, *mo\_neg\_color=None*, *mo\_blur=None*, *mo\_upsample=None*, *flat\_mo=False*, *dens\_color=None*, *nci\_mode=None*, *nci\_cutoff=None*, *surface\_style=None*, *hull=None*, *hull\_color=None*, *hull\_opacity=None*, *hull\_edge=None*, *hull\_edge\_width\_ratio=None*, *mol\_color=None*, *highlight=None*, *regions=None*, *bond\_color\_by\_element=None*, *bond\_gradient=None*, *dof=False*, *dof\_strength=None*, *overlay=None*, *overlay\_color=None*, *align\_atoms=None*, *output=None*)[[source]](../_modules/xyzrender/api.html#render)[¶](#xyzrender.api.render "Link to this definition")
:   Render a molecule to SVG and return an `SVGResult`.

    In a Jupyter cell the result displays inline automatically via
    `_repr_svg_()`. Pass *output* to save to disk at the same time.

    Parameters:
    :   - **molecule** (`str` | `PathLike` | [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule")) – A [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule") from [`load()`](#xyzrender.api.load "xyzrender.api.load"), or a file path (loaded with
          defaults).
        - **config** (`str` | [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")) – Config preset name (`"default"`, `"flat"`, …), path to a JSON
          config file, or a pre-built [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")
          from `build_config()`. Style kwargs below are only applied when
          *config* is a string.
        - **orient** (`bool` | `None`) – `True` / `False` to force / suppress PCA auto-orientation.
          `None` (default) enables auto-orientation, unless the molecule was
          manually oriented via [`orient()`](#xyzrender.api.orient "xyzrender.api.orient").
        - **ref** (`str` | `PathLike` | `None`) – Path to an orientation reference XYZ file. If the file exists,
          the molecule is Kabsch-aligned to it and PCA auto-orientation is
          disabled regardless of *orient*. If the file does not exist,
          current (possibly PCA-oriented) positions are saved to it.
          Not supported for periodic structures (raises `ValueError`).
        - **ts\_bonds** (`list`[`tuple`[`int`, `int`]] | `None`) – Manual TS / NCI bond overlays as 1-indexed atom pairs.
        - **nci\_bonds** (`list`[`tuple`[`int`, `int`]] | `None`) – Manual TS / NCI bond overlays as 1-indexed atom pairs.
        - **vdw** (`bool` | `list`[`int`] | `None`) – VdW sphere display. `True` = all atoms; a list of 1-indexed atom
          indices = specific atoms; `None` = off (default).
        - **idx** (`bool` | `str`) – Atom index labels. `True` or `"sn"` (e.g. `C1`); `"s"`
          (element only); `"n"` (number only).
        - **cmap** (`str` | `PathLike` | `dict`[`int`, `float`] | `None`) – Atom property colour map: either a `{1-indexed atom: value}` dict,
          or a path to a two-column text file (index value, same format as
          `--cmap` in the CLI).
        - **labels** (`list`[`str`] | `None`) – Inline annotation spec strings (e.g. `["1 2 d", "3 a", "1 NBO"]`).
        - **label\_file** (`str` | `None`) – Path to an annotation file (same format as `--label`).
        - **stereo** (`bool` | `list`[`str`]) – `True` for all stereochemistry labels, or a list of classes to show
          (`"point"`, `"ez"`, `"axis"`, `"plane"`, `"helix"`).
        - **stereo\_style** (`str`) – Placement for R/S labels: `"atom"` (centered on atom) or `"label"` (offset near atom).
        - **vectors** – Vector arrows to overlay. Pass a path/dict to a JSON file, or a list
          of [`xyzrender.types.VectorArrow`](types.html#xyzrender.types.VectorArrow "xyzrender.types.VectorArrow") objects. Each arrow is drawn
          as a shaft + filled arrowhead pointing from `origin` in the direction
          of `vector`. When the 2D projected length is shorter than the
          arrowhead size (i.e. the arrow points nearly along the viewing axis), a
          compact symbol is drawn instead: a filled dot (•) when the tip is closer
          to the viewer, or a cross (x) when it points away. The label is
          suppressed in these cases and reappears automatically once the arrow is
          long enough to draw a proper arrowhead.
        - **mo** (`bool`) – Render MO lobes / density isosurface from a cube file loaded via
          [`load()`](#xyzrender.api.load "xyzrender.api.load").
        - **dens** (`bool`) – Render MO lobes / density isosurface from a cube file loaded via
          [`load()`](#xyzrender.api.load "xyzrender.api.load").
        - **esp** (`str` | `PathLike` | `None`) – Path to an ESP `.cube` file (density iso + ESP colour map).
        - **nci** (`str` | `PathLike` | `None`) – Path to an NCI reduced-density-gradient `.cube` file.
        - **hull** (`bool` | `str` | `list`[`int`] | `list`[`list`[`int`]] | `None`) – `True` = hull over all heavy atoms; `"rings"` = one hull per
          aromatic ring (auto-detected from the molecular graph); a flat list
          of 1-indexed atom indices (one hull, e.g. `[1,2,3,4,5,6]`); a list
          of lists (multiple hulls, e.g. `[[1,2,3,4,5,6], [7,8,9]]`).
          `None` (default) = off.
        - **hull\_color** (`str` | `list`[`str`] | `None`) – A single color string for all hulls, or a list of colors for per-subset
          colouring (one per subset). Hex or named color.
        - **hull\_opacity** (`float` | `None`) – Fill opacity for all hull surfaces.
        - **hull\_edge** (`bool` | `None`) – Draw hull edges that are not bonds as thin lines.
        - **hull\_edge\_width\_ratio** (`float` | `None`) – Draw hull edges that are not bonds as thin lines.

    Returns:
    :   Wrapper around the SVG string. Displays inline in Jupyter.

    Return type:
    :   [`SVGResult`](types.html#xyzrender.types.SVGResult "xyzrender.types.SVGResult")

xyzrender.api.render\_gif(*molecule*, *\**, *gif\_rot=None*, *gif\_trj=False*, *gif\_ts=False*, *gif\_diffuse=False*, *diffuse\_frames=60*, *diffuse\_noise=0.3*, *diffuse\_bonds='fade'*, *diffuse\_rot=None*, *diffuse\_reverse=True*, *anchor=None*, *output=None*, *gif\_fps=10*, *rot\_frames=120*, *ts\_frame=0*, *config='default'*, *canvas\_size=None*, *atom\_scale=None*, *bond\_width=None*, *atom\_stroke\_width=None*, *bond\_color=None*, *ts\_color=None*, *nci\_color=None*, *background=None*, *transparent=False*, *gradient=None*, *hue\_shift\_factor=None*, *light\_shift\_factor=None*, *saturation\_shift\_factor=None*, *fog=None*, *fog\_strength=None*, *label\_font\_size=None*, *vdw\_opacity=None*, *vdw\_scale=None*, *vdw\_gradient\_strength=None*, *hide\_bonds=False*, *bond\_cutoff=None*, *hy=None*, *no\_hy=False*, *bo=None*, *orient=None*, *ref=None*, *mol\_color=None*, *highlight=None*, *regions=None*, *bond\_color\_by\_element=None*, *bond\_gradient=None*, *dof=False*, *dof\_strength=None*, *overlay=None*, *overlay\_color=None*, *reference\_graph=None*, *detect\_nci=False*, *vector=None*, *vector\_scale=None*, *vector\_color=None*, *mo=False*, *dens=False*, *iso=None*, *mo\_pos\_color=None*, *mo\_neg\_color=None*, *mo\_blur=None*, *mo\_upsample=None*, *flat\_mo=False*, *dens\_color=None*, *surface\_style=None*, *hull=None*, *hull\_color=None*, *hull\_opacity=None*, *hull\_edge=None*, *hull\_edge\_width\_ratio=None*, *no\_cell=False*, *axes=True*, *axis=None*, *supercell=(1, 1, 1)*, *ghosts=None*, *cell\_color=None*, *cell\_width=None*, *ghost\_opacity=None*)[[source]](../_modules/xyzrender/api.html#render_gif)[¶](#xyzrender.api.render_gif "Link to this definition")
:   Render a molecule to an animated GIF and return a `GIFResult`.

    The result displays the GIF inline in Jupyter via `_repr_html_`.
    Access the file path via `result.path`.

    At least one of *gif\_rot*, *gif\_trj*, *gif\_ts* must be set.

    Parameters:
    :   - **molecule** (`str` | `PathLike` | [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule")) – A [`Molecule`](#xyzrender.api.Molecule "xyzrender.api.Molecule") from [`load()`](#xyzrender.api.load "xyzrender.api.load"), or a file path. For
          *gif\_ts* and *gif\_trj* modes, a file path is required (the
          trajectory or vibration data is read directly from disk).
        - **gif\_rot** (`str` | `None`) – Rotation axis: `"x"`, `"y"`, `"z"`, diagonal (`"xy"`,
          …), or a 3-digit Miller index (`"111"`).
        - **gif\_trj** (`bool`) – Trajectory animation — *molecule* must be a multi-frame XYZ.
        - **gif\_ts** (`bool`) – Transition-state vibration animation (requires `xyzrender[ts]`).
        - **output** (`str` | `PathLike` | `None`) – Output `.gif` path. Defaults to `<stem>.gif` beside *molecule*.
        - **gif\_fps** (`int`) – Frames per second.
        - **rot\_frames** (`int`) – Number of frames for a full rotation.
        - **ts\_frame** (`int`) – Reference frame index for TS detection (0-indexed).
        - **config** (`str` | [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")) – Preset name, JSON path, or pre-built [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig").

    Returns:
    :   Wrapper with path to the written GIF file.

    Return type:
    :   [`GIFResult`](types.html#xyzrender.types.GIFResult "xyzrender.types.GIFResult")

---

# Types Reference¶

# Types Reference[¶](#module-xyzrender.types "Link to this heading")

Core types for xyzrender.

class xyzrender.types.BondStyle(*\*values*)[[source]](../_modules/xyzrender/types.html#BondStyle)[¶](#xyzrender.types.BondStyle "Link to this definition")
:   Bases: `Enum`

    Visual bond style.

    DASHED = 'dashed'[¶](#xyzrender.types.BondStyle.DASHED "Link to this definition")

    DOTTED = 'dot'[¶](#xyzrender.types.BondStyle.DOTTED "Link to this definition")

    SOLID = 'solid'[¶](#xyzrender.types.BondStyle.SOLID "Link to this definition")

class xyzrender.types.CellData(*lattice*, *cell\_origin=<factory>*)[[source]](../_modules/xyzrender/types.html#CellData)[¶](#xyzrender.types.CellData "Link to this definition")
:   Bases: `object`

    Periodic lattice data for crystal structure rendering.

    Parameters:
    :   - **lattice** (`ndarray`) – 3x3 array where each row is a lattice vector (a, b, c) in Ångströms.
        - **cell\_origin** (`ndarray`) – 3-vector (Å) of the (0,0,0) cell corner in the current coordinate frame.
          Defaults to the origin; updated during GIF rotation so the box keeps
          pace with the atoms.

    cell\_origin: ndarray[¶](#xyzrender.types.CellData.cell_origin "Link to this definition")

    lattice: ndarray[¶](#xyzrender.types.CellData.lattice "Link to this definition")

class xyzrender.types.DensParams(*isovalue=0.001*, *color='steelblue'*)[[source]](../_modules/xyzrender/types.html#DensParams)[¶](#xyzrender.types.DensParams "Link to this definition")
:   Bases: `object`

    Parameters for electron density surface rendering.

    Parameters:
    :   - **isovalue** (`float`) – Isovalue at which to extract the density isosurface.
        - **color** (`str`) – Fill color for the density contour (hex or CSS4 name).

    color: str = 'steelblue'[¶](#xyzrender.types.DensParams.color "Link to this definition")

    isovalue: float = 0.001[¶](#xyzrender.types.DensParams.isovalue "Link to this definition")

class xyzrender.types.ESPParams(*isovalue=0.001*)[[source]](../_modules/xyzrender/types.html#ESPParams)[¶](#xyzrender.types.ESPParams "Link to this definition")
:   Bases: `object`

    Parameters for electrostatic potential (ESP) surface rendering.

    Parameters:
    :   **isovalue** (`float`) – Isovalue of the density isosurface onto which ESP is mapped.

    isovalue: float = 0.001[¶](#xyzrender.types.ESPParams.isovalue "Link to this definition")

class xyzrender.types.GIFResult(*path*)[[source]](../_modules/xyzrender/types.html#GIFResult)[¶](#xyzrender.types.GIFResult "Link to this definition")
:   Bases: `object`

    Wraps a rendered GIF path with Jupyter inline display support.

    property path: Path[¶](#xyzrender.types.GIFResult.path "Link to this definition")
    :   Path to the GIF file on disk.

    save(*path*)[[source]](../_modules/xyzrender/types.html#GIFResult.save)[¶](#xyzrender.types.GIFResult.save "Link to this definition")
    :   Write the GIF to *path*.

        Return type:
        :   `None`

class xyzrender.types.HighlightGroup(*indices*, *color*)[[source]](../_modules/xyzrender/types.html#HighlightGroup)[¶](#xyzrender.types.HighlightGroup "Link to this definition")
:   Bases: `object`

    A group of atoms to highlight with a specific color.

    color: str[¶](#xyzrender.types.HighlightGroup.color "Link to this definition")

    indices: list[int][¶](#xyzrender.types.HighlightGroup.indices "Link to this definition")

class xyzrender.types.MOParams(*isovalue=0.05*, *pos\_color='steelblue'*, *neg\_color='maroon'*, *blur\_sigma=0.8*, *upsample\_factor=3*, *flat=False*)[[source]](../_modules/xyzrender/types.html#MOParams)[¶](#xyzrender.types.MOParams "Link to this definition")
:   Bases: `object`

    Parameters for MO (molecular orbital) surface rendering.

    Parameters:
    :   - **isovalue** (`float`) – Isovalue at which to extract the MO surface.
        - **pos\_color** (`str`) – Color for the positive-phase lobe (hex or CSS4 name).
        - **neg\_color** (`str`) – Color for the negative-phase lobe (hex or CSS4 name).
        - **blur\_sigma** (`float`) – Gaussian blur sigma in 2D grid-cell units applied before upsampling.
        - **upsample\_factor** (`int`) – Integer upsampling multiplier applied to the 2D projection grid.
        - **flat** (`bool`) – Render lobes as flat-filled shapes (no depth shading).

    blur\_sigma: float = 0.8[¶](#xyzrender.types.MOParams.blur_sigma "Link to this definition")

    flat: bool = False[¶](#xyzrender.types.MOParams.flat "Link to this definition")

    isovalue: float = 0.05[¶](#xyzrender.types.MOParams.isovalue "Link to this definition")

    neg\_color: str = 'maroon'[¶](#xyzrender.types.MOParams.neg_color "Link to this definition")

    pos\_color: str = 'steelblue'[¶](#xyzrender.types.MOParams.pos_color "Link to this definition")

    upsample\_factor: int = 3[¶](#xyzrender.types.MOParams.upsample_factor "Link to this definition")

class xyzrender.types.NCIParams(*isovalue=0.3*, *color='forestgreen'*, *color\_mode='avg'*, *dens\_cutoff=None*)[[source]](../_modules/xyzrender/types.html#NCIParams)[¶](#xyzrender.types.NCIParams "Link to this definition")
:   Bases: `object`

    Parameters for NCI (non-covalent interaction) surface rendering.

    Parameters:
    :   - **isovalue** (`float`) – Reduced density gradient isovalue for the NCI flood-fill.
        - **color** (`str`) – Fallback fill color when `color_mode` is `'uniform'` (hex or CSS4 name).
        - **color\_mode** (`str`) – How to assign colors to each NCI lobe:
          `'avg'` uses the average sign(lambda2)\*rho value per lobe,
          `'pixel'` maps per-pixel values (raster PNG),
          `'uniform'` uses `color` for every lobe.
        - **dens\_cutoff** (`float` | `None`) – Optional density magnitude cutoff; voxels with density magnitude (abs(rho)) above this are
          excluded (useful for non-NCIPLOT cubes where nuclear contributions
          are not pre-removed).

    color: str = 'forestgreen'[¶](#xyzrender.types.NCIParams.color "Link to this definition")

    color\_mode: str = 'avg'[¶](#xyzrender.types.NCIParams.color_mode "Link to this definition")

    dens\_cutoff: float | None = None[¶](#xyzrender.types.NCIParams.dens_cutoff "Link to this definition")

    isovalue: float = 0.3[¶](#xyzrender.types.NCIParams.isovalue "Link to this definition")

class xyzrender.types.RenderConfig(*canvas\_size=800*, *padding=20.0*, *atom\_scale=1.0*, *atom\_stroke\_width=1.5*, *atom\_stroke\_color='black'*, *atom\_wash=0.0*, *atoms\_above\_bonds=False*, *bond\_width=5.0*, *bond\_color='#333333'*, *ts\_color=None*, *nci\_color=None*, *bond\_gap=0.6*, *bond\_color\_by\_element=False*, *bond\_gradient=False*, *gradient=False*, *hue\_shift\_factor=0.2*, *light\_shift\_factor=0.2*, *saturation\_shift\_factor=0.2*, *fog=False*, *fog\_strength=0.8*, *hide\_bonds=False*, *bond\_cutoff=None*, *hide\_h=False*, *show\_h\_indices=<factory>*, *bond\_orders=True*, *ts\_bonds=<factory>*, *nci\_bonds=<factory>*, *vdw\_indices=None*, *vdw\_opacity=0.5*, *vdw\_scale=1.0*, *vdw\_gradient\_strength=1.6*, *auto\_orient=False*, *background='#ffffff'*, *transparent=False*, *dpi=300*, *fixed\_span=None*, *fixed\_center=None*, *color\_overrides=None*, *mol\_color=None*, *mo\_contours=None*, *dens\_contours=None*, *esp\_surface=None*, *nci\_contours=None*, *surface\_opacity=1.0*, *flat\_mo=False*, *surface\_style='solid'*, *annotations=<factory>*, *show\_indices=False*, *idx\_format='sn'*, *label\_font\_size=11.0*, *label\_color='#222222'*, *label\_offset=0.5*, *atom\_cmap=None*, *cmap\_range=None*, *cmap\_symm=False*, *cmap\_unlabeled='#ffffff'*, *cmap\_palette='viridis'*, *cbar=False*, *mo\_isovalue=0.05*, *mo\_pos\_color='steelblue'*, *mo\_neg\_color='maroon'*, *mo\_blur\_sigma=0.8*, *mo\_upsample\_factor=3*, *dens\_isovalue=0.001*, *dens\_color='steelblue'*, *nci\_isovalue=0.3*, *nci\_mode='avg'*, *highlight\_groups=<factory>*, *highlight\_colors=<factory>*, *dof=False*, *dof\_strength=3.0*, *overlay\_color='mediumorchid'*, *ensemble\_colors=None*, *skeletal\_style=False*, *skeletal\_label\_color=None*, *cell\_data=None*, *show\_cell=True*, *cell\_color='#333333'*, *cell\_line\_width=2.0*, *periodic\_image\_opacity=0.5*, *axis\_colors=('firebrick'*, *'forestgreen'*, *'royalblue')*, *axis\_width\_scale=3.0*, *vectors=<factory>*, *vector\_scale=1.0*, *vector\_color='firebrick'*, *show\_convex\_hull=False*, *hull\_opacity=0.2*, *hull\_colors=<factory>*, *hull\_atom\_indices=None*, *show\_hull\_edges=True*, *hull\_edge\_width\_ratio=0.4*, *style\_regions=<factory>*)[[source]](../_modules/xyzrender/types.html#RenderConfig)[¶](#xyzrender.types.RenderConfig "Link to this definition")
:   Bases: `object`

    Rendering settings.

    annotations: list[AtomValueLabel | BondLabel | AngleLabel | DihedralLabel | CentroidLabel][¶](#xyzrender.types.RenderConfig.annotations "Link to this definition")

    atom\_cmap: dict[int, float] | None = None[¶](#xyzrender.types.RenderConfig.atom_cmap "Link to this definition")

    atom\_scale: float = 1.0[¶](#xyzrender.types.RenderConfig.atom_scale "Link to this definition")

    atom\_stroke\_color: str = 'black'[¶](#xyzrender.types.RenderConfig.atom_stroke_color "Link to this definition")

    atom\_stroke\_width: float = 1.5[¶](#xyzrender.types.RenderConfig.atom_stroke_width "Link to this definition")

    atom\_wash: float = 0.0[¶](#xyzrender.types.RenderConfig.atom_wash "Link to this definition")

    atoms\_above\_bonds: bool = False[¶](#xyzrender.types.RenderConfig.atoms_above_bonds "Link to this definition")

    auto\_orient: bool = False[¶](#xyzrender.types.RenderConfig.auto_orient "Link to this definition")

    axis\_colors: tuple[str, str, str] = ('firebrick', 'forestgreen', 'royalblue')[¶](#xyzrender.types.RenderConfig.axis_colors "Link to this definition")

    axis\_width\_scale: float = 3.0[¶](#xyzrender.types.RenderConfig.axis_width_scale "Link to this definition")

    background: str = '#ffffff'[¶](#xyzrender.types.RenderConfig.background "Link to this definition")

    bond\_color: str = '#333333'[¶](#xyzrender.types.RenderConfig.bond_color "Link to this definition")

    bond\_color\_by\_element: bool = False[¶](#xyzrender.types.RenderConfig.bond_color_by_element "Link to this definition")

    bond\_cutoff: float | None = None[¶](#xyzrender.types.RenderConfig.bond_cutoff "Link to this definition")

    bond\_gap: float = 0.6[¶](#xyzrender.types.RenderConfig.bond_gap "Link to this definition")

    bond\_gradient: bool = False[¶](#xyzrender.types.RenderConfig.bond_gradient "Link to this definition")

    bond\_orders: bool = True[¶](#xyzrender.types.RenderConfig.bond_orders "Link to this definition")

    bond\_width: float = 5.0[¶](#xyzrender.types.RenderConfig.bond_width "Link to this definition")

    canvas\_size: int = 800[¶](#xyzrender.types.RenderConfig.canvas_size "Link to this definition")

    cbar: bool = False[¶](#xyzrender.types.RenderConfig.cbar "Link to this definition")

    cell\_color: str = '#333333'[¶](#xyzrender.types.RenderConfig.cell_color "Link to this definition")

    cell\_data: [CellData](#xyzrender.types.CellData "xyzrender.types.CellData") | None = None[¶](#xyzrender.types.RenderConfig.cell_data "Link to this definition")

    cell\_line\_width: float = 2.0[¶](#xyzrender.types.RenderConfig.cell_line_width "Link to this definition")

    cmap\_palette: str = 'viridis'[¶](#xyzrender.types.RenderConfig.cmap_palette "Link to this definition")

    cmap\_range: tuple[float, float] | None = None[¶](#xyzrender.types.RenderConfig.cmap_range "Link to this definition")

    cmap\_symm: bool = False[¶](#xyzrender.types.RenderConfig.cmap_symm "Link to this definition")

    cmap\_unlabeled: str = '#ffffff'[¶](#xyzrender.types.RenderConfig.cmap_unlabeled "Link to this definition")

    color\_overrides: dict[str, str] | None = None[¶](#xyzrender.types.RenderConfig.color_overrides "Link to this definition")

    dens\_color: str = 'steelblue'[¶](#xyzrender.types.RenderConfig.dens_color "Link to this definition")

    dens\_contours: SurfaceContours | None = None[¶](#xyzrender.types.RenderConfig.dens_contours "Link to this definition")

    dens\_isovalue: float = 0.001[¶](#xyzrender.types.RenderConfig.dens_isovalue "Link to this definition")

    dof: bool = False[¶](#xyzrender.types.RenderConfig.dof "Link to this definition")

    dof\_strength: float = 3.0[¶](#xyzrender.types.RenderConfig.dof_strength "Link to this definition")

    dpi: int = 300[¶](#xyzrender.types.RenderConfig.dpi "Link to this definition")

    ensemble\_colors: list[str] | None = None[¶](#xyzrender.types.RenderConfig.ensemble_colors "Link to this definition")

    esp\_surface: ESPSurface | None = None[¶](#xyzrender.types.RenderConfig.esp_surface "Link to this definition")

    fixed\_center: tuple[float, float] | None = None[¶](#xyzrender.types.RenderConfig.fixed_center "Link to this definition")

    fixed\_span: float | None = None[¶](#xyzrender.types.RenderConfig.fixed_span "Link to this definition")

    flat\_mo: bool = False[¶](#xyzrender.types.RenderConfig.flat_mo "Link to this definition")

    fog: bool = False[¶](#xyzrender.types.RenderConfig.fog "Link to this definition")

    fog\_strength: float = 0.8[¶](#xyzrender.types.RenderConfig.fog_strength "Link to this definition")

    gradient: bool = False[¶](#xyzrender.types.RenderConfig.gradient "Link to this definition")

    hide\_bonds: bool = False[¶](#xyzrender.types.RenderConfig.hide_bonds "Link to this definition")

    hide\_h: bool = False[¶](#xyzrender.types.RenderConfig.hide_h "Link to this definition")

    highlight\_colors: list[str][¶](#xyzrender.types.RenderConfig.highlight_colors "Link to this definition")

    highlight\_groups: list[[HighlightGroup](#xyzrender.types.HighlightGroup "xyzrender.types.HighlightGroup")][¶](#xyzrender.types.RenderConfig.highlight_groups "Link to this definition")

    hue\_shift\_factor: float = 0.2[¶](#xyzrender.types.RenderConfig.hue_shift_factor "Link to this definition")

    hull\_atom\_indices: list[int] | list[list[int]] | None = None[¶](#xyzrender.types.RenderConfig.hull_atom_indices "Link to this definition")

    hull\_colors: list[str][¶](#xyzrender.types.RenderConfig.hull_colors "Link to this definition")

    hull\_edge\_width\_ratio: float = 0.4[¶](#xyzrender.types.RenderConfig.hull_edge_width_ratio "Link to this definition")

    hull\_opacity: float = 0.2[¶](#xyzrender.types.RenderConfig.hull_opacity "Link to this definition")

    idx\_format: str = 'sn'[¶](#xyzrender.types.RenderConfig.idx_format "Link to this definition")

    label\_color: str = '#222222'[¶](#xyzrender.types.RenderConfig.label_color "Link to this definition")

    label\_font\_size: float = 11.0[¶](#xyzrender.types.RenderConfig.label_font_size "Link to this definition")

    label\_offset: float = 0.5[¶](#xyzrender.types.RenderConfig.label_offset "Link to this definition")

    light\_shift\_factor: float = 0.2[¶](#xyzrender.types.RenderConfig.light_shift_factor "Link to this definition")

    mo\_blur\_sigma: float = 0.8[¶](#xyzrender.types.RenderConfig.mo_blur_sigma "Link to this definition")

    mo\_contours: SurfaceContours | None = None[¶](#xyzrender.types.RenderConfig.mo_contours "Link to this definition")

    mo\_isovalue: float = 0.05[¶](#xyzrender.types.RenderConfig.mo_isovalue "Link to this definition")

    mo\_neg\_color: str = 'maroon'[¶](#xyzrender.types.RenderConfig.mo_neg_color "Link to this definition")

    mo\_pos\_color: str = 'steelblue'[¶](#xyzrender.types.RenderConfig.mo_pos_color "Link to this definition")

    mo\_upsample\_factor: int = 3[¶](#xyzrender.types.RenderConfig.mo_upsample_factor "Link to this definition")

    mol\_color: str | None = None[¶](#xyzrender.types.RenderConfig.mol_color "Link to this definition")

    nci\_bonds: list[tuple[int, int]][¶](#xyzrender.types.RenderConfig.nci_bonds "Link to this definition")

    nci\_color: str | None = None[¶](#xyzrender.types.RenderConfig.nci_color "Link to this definition")

    nci\_contours: NCIContours | None = None[¶](#xyzrender.types.RenderConfig.nci_contours "Link to this definition")

    nci\_isovalue: float = 0.3[¶](#xyzrender.types.RenderConfig.nci_isovalue "Link to this definition")

    nci\_mode: str = 'avg'[¶](#xyzrender.types.RenderConfig.nci_mode "Link to this definition")

    overlay\_color: str = 'mediumorchid'[¶](#xyzrender.types.RenderConfig.overlay_color "Link to this definition")

    padding: float = 20.0[¶](#xyzrender.types.RenderConfig.padding "Link to this definition")

    periodic\_image\_opacity: float = 0.5[¶](#xyzrender.types.RenderConfig.periodic_image_opacity "Link to this definition")

    saturation\_shift\_factor: float = 0.2[¶](#xyzrender.types.RenderConfig.saturation_shift_factor "Link to this definition")

    show\_cell: bool = True[¶](#xyzrender.types.RenderConfig.show_cell "Link to this definition")

    show\_convex\_hull: bool = False[¶](#xyzrender.types.RenderConfig.show_convex_hull "Link to this definition")

    show\_h\_indices: list[int][¶](#xyzrender.types.RenderConfig.show_h_indices "Link to this definition")

    show\_hull\_edges: bool = True[¶](#xyzrender.types.RenderConfig.show_hull_edges "Link to this definition")

    show\_indices: bool = False[¶](#xyzrender.types.RenderConfig.show_indices "Link to this definition")

    skeletal\_label\_color: str | None = None[¶](#xyzrender.types.RenderConfig.skeletal_label_color "Link to this definition")

    skeletal\_style: bool = False[¶](#xyzrender.types.RenderConfig.skeletal_style "Link to this definition")

    style\_regions: list[[StyleRegion](#xyzrender.types.StyleRegion "xyzrender.types.StyleRegion")][¶](#xyzrender.types.RenderConfig.style_regions "Link to this definition")

    surface\_opacity: float = 1.0[¶](#xyzrender.types.RenderConfig.surface_opacity "Link to this definition")

    surface\_style: str = 'solid'[¶](#xyzrender.types.RenderConfig.surface_style "Link to this definition")

    transparent: bool = False[¶](#xyzrender.types.RenderConfig.transparent "Link to this definition")

    ts\_bonds: list[tuple[int, int]][¶](#xyzrender.types.RenderConfig.ts_bonds "Link to this definition")

    ts\_color: str | None = None[¶](#xyzrender.types.RenderConfig.ts_color "Link to this definition")

    vdw\_gradient\_strength: float = 1.6[¶](#xyzrender.types.RenderConfig.vdw_gradient_strength "Link to this definition")

    vdw\_indices: list[int] | None = None[¶](#xyzrender.types.RenderConfig.vdw_indices "Link to this definition")

    vdw\_opacity: float = 0.5[¶](#xyzrender.types.RenderConfig.vdw_opacity "Link to this definition")

    vdw\_scale: float = 1.0[¶](#xyzrender.types.RenderConfig.vdw_scale "Link to this definition")

    vector\_color: str = 'firebrick'[¶](#xyzrender.types.RenderConfig.vector_color "Link to this definition")

    vector\_scale: float = 1.0[¶](#xyzrender.types.RenderConfig.vector_scale "Link to this definition")

    vectors: list[[VectorArrow](#xyzrender.types.VectorArrow "xyzrender.types.VectorArrow")][¶](#xyzrender.types.RenderConfig.vectors "Link to this definition")

class xyzrender.types.SVGResult(*svg*)[[source]](../_modules/xyzrender/types.html#SVGResult)[¶](#xyzrender.types.SVGResult "Link to this definition")
:   Bases: `object`

    Wraps a rendered SVG string with Jupyter display and file-save support.

    save(*path*)[[source]](../_modules/xyzrender/types.html#SVGResult.save)[¶](#xyzrender.types.SVGResult.save "Link to this definition")
    :   Write the SVG to *path* (must end with `.svg`).

        Return type:
        :   `None`

class xyzrender.types.StyleRegion(*indices*, *config*)[[source]](../_modules/xyzrender/types.html#StyleRegion)[¶](#xyzrender.types.StyleRegion "Link to this definition")
:   Bases: `object`

    A subset of atoms rendered with a different visual style.

    Only per-atom/bond fields are used (atom\_scale, gradient, bond\_width,
    etc.); global fields (canvas\_size, background, fog, surfaces) are
    taken from the base config.

    config: [RenderConfig](#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")[¶](#xyzrender.types.StyleRegion.config "Link to this definition")

    indices: list[int][¶](#xyzrender.types.StyleRegion.indices "Link to this definition")

class xyzrender.types.VectorArrow(*vector*, *origin*, *color='#444444'*, *label=''*, *scale=1.0*, *anchor='tail'*, *host\_atom=None*, *draw\_on\_top=False*, *is\_axis=False*, *font\_size=None*, *width=None*)[[source]](../_modules/xyzrender/types.html#VectorArrow)[¶](#xyzrender.types.VectorArrow "Link to this definition")
:   Bases: `object`

    A 3D vector to be drawn as an arrow in the rendered image.

    Parameters:
    :   - **vector** (`ndarray`) – 3-component array giving the direction and magnitude of the arrow (Å or
          any consistent unit — the length on screen scales with the molecule).
        - **origin** (`ndarray`) – 3D origin point of the arrow tail in the same coordinate frame as atom
          positions. Set this after resolving `"com"` or atom-index origins.
        - **color** (`str`) – CSS hex color string (default `'#444444'`).
        - **label** (`str`) – Optional text placed near the arrowhead.
        - **scale** (`float`) – Additional per-arrow length scale factor applied on top of any global
          `vector_scale` setting (default 1.0).
        - **host\_atom** (`int` | `None`) – 0-based index of the atom this arrow is centred on, or `None` when
          the origin was specified as `"com"` or explicit coordinates. Used
          by the renderer to determine whether the arrowhead protrudes in front
          of the host atom without an expensive nearest-neighbour search.

    anchor: str = 'tail'[¶](#xyzrender.types.VectorArrow.anchor "Link to this definition")

    color: str = '#444444'[¶](#xyzrender.types.VectorArrow.color "Link to this definition")

    draw\_on\_top: bool = False[¶](#xyzrender.types.VectorArrow.draw_on_top "Link to this definition")

    font\_size: float | None = None[¶](#xyzrender.types.VectorArrow.font_size "Link to this definition")

    host\_atom: int | None = None[¶](#xyzrender.types.VectorArrow.host_atom "Link to this definition")

    is\_axis: bool = False[¶](#xyzrender.types.VectorArrow.is_axis "Link to this definition")

    label: str = ''[¶](#xyzrender.types.VectorArrow.label "Link to this definition")

    origin: ndarray[¶](#xyzrender.types.VectorArrow.origin "Link to this definition")

    scale: float = 1.0[¶](#xyzrender.types.VectorArrow.scale "Link to this definition")

    vector: ndarray[¶](#xyzrender.types.VectorArrow.vector "Link to this definition")

    width: float | None = None[¶](#xyzrender.types.VectorArrow.width "Link to this definition")

---

# Config Reference¶

# Config Reference[¶](#module-xyzrender.config "Link to this heading")

Configuration loading for xyzrender.

xyzrender.config.apply\_hydrogen\_flags(*cfg*, *\**, *hy*, *no\_hy=False*)[[source]](../_modules/xyzrender/config.html#apply_hydrogen_flags)[¶](#xyzrender.config.apply_hydrogen_flags "Link to this definition")
:   Single source of truth for –hy / –no-hy logic. Called by CLI and Python API.

    hy=None → hide C-H (default), hy=True → show all, hy=[1,3] → show specific (1-indexed).

    Return type:
    :   `None`

xyzrender.config.build\_config(*config\_name='default'*, *\**, *canvas\_size=None*, *atom\_scale=None*, *bond\_width=None*, *atom\_stroke\_width=None*, *bond\_color=None*, *ts\_color=None*, *nci\_color=None*, *background=None*, *transparent=False*, *gradient=None*, *hue\_shift\_factor=None*, *light\_shift\_factor=None*, *saturation\_shift\_factor=None*, *fog=None*, *fog\_strength=None*, *bo=None*, *label\_font\_size=None*, *vdw\_opacity=None*, *vdw\_scale=None*, *vdw\_gradient\_strength=None*, *hide\_bonds=False*, *bond\_cutoff=None*, *hy=None*, *no\_hy=False*, *orient=None*, *opacity=None*, *ts\_bonds=None*, *nci\_bonds=None*, *vdw\_indices=None*, *show\_indices=False*, *idx\_format='sn'*, *atom\_cmap=None*, *cmap\_range=None*, *cmap\_palette='viridis'*, *cbar=False*, *cmap\_symm=False*)[[source]](../_modules/xyzrender/config.html#build_config)[¶](#xyzrender.config.build_config "Link to this definition")
:   Build a [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig") from a preset and style kwargs.

    Parameters:
    :   - **config\_name** (`str`) – Preset name (`"default"`, `"flat"`, `"paton"`, …) or path to a
          custom JSON config file.
        - **canvas\_size** – Style overrides; any `None` value falls back to the preset default.
        - **atom\_scale** – Style overrides; any `None` value falls back to the preset default.
        - **bond\_width** – Style overrides; any `None` value falls back to the preset default.
        - **…** – Style overrides; any `None` value falls back to the preset default.
        - **orient** (`bool` | `None`) – `True` / `False` to force / suppress PCA auto-orientation.
          `None` (default) enables auto-orientation.
        - **ts\_bonds** (`list`[`tuple`[`int`, `int`]] | `None`) – Manual TS / NCI bond overlays as 0-indexed atom pairs.
        - **nci\_bonds** (`list`[`tuple`[`int`, `int`]] | `None`) – Manual TS / NCI bond overlays as 0-indexed atom pairs.
        - **vdw\_indices** (`list`[`int`] | `None`) – VdW sphere atom list (0-indexed). `[]` = all atoms, `None` = off.
        - **show\_indices** (`bool`) – Enable atom index labels.
        - **atom\_cmap** (`dict`[`int`, `float`] | `None`) – Atom property colour map (0-indexed keys).

    Returns:
    :   Ready to pass to `render()` as `config=`.

    Return type:
    :   [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")

    Example

    ```
    cfg = build_config("flat", atom_scale=1.5, gradient=False)
    render(mol1, config=cfg)
    render(mol2, config=cfg)
    ```

    Bond/index/cmap params use **0-indexed** atom numbering (the internal
    convention). The Python API converts from user-facing 1-indexed values
    before calling this function; the CLI passes \_parse\_pairs() output directly.

xyzrender.config.build\_region\_config(*config\_name='default'*, *\*\*overrides*)[[source]](../_modules/xyzrender/config.html#build_region_config)[¶](#xyzrender.config.build_region_config "Link to this definition")
:   Build a `RenderConfig` for use as a `StyleRegion` config.

    Only per-atom/bond fields are meaningful; global fields (canvas, fog,
    surfaces) are ignored by the renderer for region configs.

    Return type:
    :   [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")

xyzrender.config.build\_render\_config(*config\_data*, *cli\_overrides*)[[source]](../_modules/xyzrender/config.html#build_render_config)[¶](#xyzrender.config.build_render_config "Link to this definition")
:   Merge config dict with CLI overrides into a RenderConfig.

    `config_data` is the base layer (from JSON).
    `cli_overrides` contains only explicitly-set CLI values (non-None).
    CLI values win over config file values.

    Return type:
    :   [`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")

xyzrender.config.build\_surface\_params(*cfg*, *cli\_overrides*, *\**, *has\_mo=False*, *has\_dens=False*, *has\_esp=False*, *has\_nci=False*)[[source]](../_modules/xyzrender/config.html#build_surface_params)[¶](#xyzrender.config.build_surface_params "Link to this definition")
:   Extract and merge surface params from config + CLI into typed `*Params` objects.

    Returns `None` for any surface that is not active (`has_*` flag is
    `False`), so callers can use simple `if params:` checks.

    Parameters:
    :   - **cfg** ([`RenderConfig`](types.html#xyzrender.types.RenderConfig "xyzrender.types.RenderConfig")) – Render config (surface defaults stored on fields populated by [`build_config()`](#xyzrender.config.build_config "xyzrender.config.build_config")).
        - **cli\_overrides** (`dict`) – Dict of explicit per-render values (non-`None` values only).
        - **has\_mo** (`bool`) – Flags indicating which surfaces are active.
        - **has\_dens** (`bool`) – Flags indicating which surfaces are active.
        - **has\_esp** (`bool`) – Flags indicating which surfaces are active.
        - **has\_nci** (`bool`) – Flags indicating which surfaces are active.

    Return type:
    :   `tuple`[[`MOParams`](types.html#xyzrender.types.MOParams "xyzrender.types.MOParams") | `None`, [`DensParams`](types.html#xyzrender.types.DensParams "xyzrender.types.DensParams") | `None`, [`ESPParams`](types.html#xyzrender.types.ESPParams "xyzrender.types.ESPParams") | `None`, [`NCIParams`](types.html#xyzrender.types.NCIParams "xyzrender.types.NCIParams") | `None`]

xyzrender.config.collect\_surf\_overrides(*\**, *iso=None*, *mo\_pos\_color=None*, *mo\_neg\_color=None*, *mo\_blur=None*, *mo\_upsample=None*, *flat\_mo=False*, *dens\_color=None*, *nci\_mode=None*, *nci\_cutoff=None*, *surface\_style=None*)[[source]](../_modules/xyzrender/config.html#collect_surf_overrides)[¶](#xyzrender.config.collect_surf_overrides "Link to this definition")
:   Collect surface param overrides into a dict for `build_surface_params`.

    `nci_mode` accepts `'avg'`, `'pixel'`, `'uniform'`, or a colour
    name/hex (implying uniform mode). `flat_mo=True` overrides the config
    default.

    Return type:
    :   `dict`

xyzrender.config.load\_config(*name\_or\_path*)[[source]](../_modules/xyzrender/config.html#load_config)[¶](#xyzrender.config.load_config "Link to this definition")
:   Load config from a built-in preset name or a JSON file path.

    All presets (including named built-ins like `"flat"` or `"paton"`) are
    merged on top of `default.json` so unspecified keys always inherit the
    standard defaults. The `"default"` preset itself is returned as-is.

    Return type:
    :   `dict`

---

#  Citation

xyzrender uses [xyzgraph](https://github.com/aligfellow/xyzgraph) and [graphRC](https://github.com/aligfellow/graphRC) for all molecular graph construction — bond orders, aromaticity detection, NCI interactions, and TS bond detection. If you use xyzrender in published work, please cite:

> A.S. Goodfellow* and B.N. Nguyen, *J. Chem. Theory Comput.*, 2026, DOI: [10.1021/acs.jctc.5c02073](https://doi.org/10.1021/acs.jctc.5c02073)

Preprint:
> A.S. Goodfellow* and B.N. Nguyen, *ChemRxiv*, 2025, DOI: [10.26434/chemrxiv-2025-k69gt](https://doi.org/10.26434/chemrxiv-2025-k69gt)

## BibTeX

```bibtex
@article{goodfellow2026xyzgraph,
  author  = {Goodfellow, A.S. and Nguyen, B.N.},
  title   = {Graph-Based Internal Coordinate Analysis for Transition State Characterization},
  journal = {J. Chem. Theory Comput.},
  year    = {2026},
  doi     = {10.1021/acs.jctc.5c02073},
}
```

---

# Acknowledgements

The SVG rendering in xyzrender is built on and heavily inspired by [**xyz2svg**](https://github.com/briling/xyz2svg). The CPK colour scheme, core SVG atom/bond rendering logic, fog, and overall approach originate from that project.

- [Ksenia Briling (@briling)](https://github.com/briling) — [**xyz2svg**](https://github.com/briling/xyz2svg) and [**v**](https://github.com/briling/v)
- [Iñigo Iribarren Aguirre (@iribirii)](https://github.com/iribirii) — radial gradient (pseudo-3D) rendering from [**xyz2svg**](https://github.com/briling/xyz2svg).

## Key dependencies

- [**xyzgraph**](https://github.com/aligfellow/xyzgraph) — bond connectivity, bond orders, aromaticity detection and non-covalent interactions from molecular geometry
- [**graphRC**](https://github.com/aligfellow/graphRC) — reaction coordinate analysis and TS bond detection from imaginary frequency vibrations
- [**cclib**](https://github.com/cclib/cclib) — parsing quantum chemistry output files (ORCA, Gaussian, Q-Chem, etc.)
- [**CairoSVG**](https://github.com/Kozea/CairoSVG) — SVG to PNG/PDF conversion
- [**Pillow**](https://github.com/python-pillow/Pillow) — GIF frame assembly
- [**resvg-py**](https://github.com/nicmr/resvg-py) — SVG to PNG conversion preserving SVG effects

## Optional dependencies

- [**phonopy**](https://github.com/phonopy/phonopy) — crystal structure loading (`pip install 'xyzrender[crystal]'`)
- [**rdkit**](https://www.rdkit.org/) — SMILES 3D embedding (`pip install 'xyzrender[smiles]'`)
- [**ase**](https://wiki.fysik.dtu.dk/ase/) — CIF parsing (`pip install 'xyzrender[cif]'`)
- [**v**](https://github.com/briling/v) — interactive molecule orientation (`-I` flag, `pip install xyzrender[v]`, Linux only, not included into `[all]`)

The `paton` colour preset is inspired by the clean styling used by [Rob Paton](https://github.com/patonlab) through PyMOL ([gist](https://gist.github.com/bobbypaton/1cdc4784f3fc8374467bae5eb410edef)).

NCI surface example structures from [NCIPlot](https://github.com/juliacontrerasgarcia/NCIPLOT-4.2/tree/master/tests).

## Contributors

- [Ksenia Briling (@briling)](https://github.com/briling) — `vmol` integration and the [xyz2svg](https://github.com/briling/xyz2svg) foundation
- [Sander Cohen-Janes (@scohenjanes5)](https://github.com/scohenjanes5) — crystal/periodic structure support (VASP, Quantum ESPRESSO, ghost atoms, crystallographic axes), vector annotations and gif parallelisation
- [Rubén Laplaza (@rlaplaza)](https://github.com/rlaplaza) — convex hull facets
- [Iñigo Iribarren Aguirre (@iribirii)](https://github.com/iribirii) — radial gradients respecting colour space (pseudo-3D), skeletal rendering, ensemble display
- [Vinicius Port (@caprilesport)](https://github.com/caprilesport) — `v` binary path discovery
- [Lucas Attia (@lucasattia)](https://github.com/lucasattia) — `--transparent` background flag

## License

[MIT](https://github.com/aligfellow/xyzrender/blob/main/LICENSE)
