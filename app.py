"""
xyzrender Web Application  v5
══════════════════════════════════════════════════════════
Changes in v5:
  • TEMP/  — all renders go here first (auto-cleared on startup)
  • FIGURE/ — only explicitly saved files land here
  • /api/temp_figures   — list TEMP
  • /api/save_figure    — copy TEMP → FIGURE
  • /api/delete_temp    — delete from TEMP
  • /temp/<file>        — serve TEMP files
"""

import json, math, shutil, subprocess
from pathlib import Path

import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024

BASE_DIR      = Path(__file__).parent
MOLECULES_DIR = BASE_DIR / "MOLECULES"
FIGURE_DIR    = BASE_DIR / "FIGURE"
TEMP_DIR      = BASE_DIR / "TEMP"

MOLECULES_DIR.mkdir(exist_ok=True)
FIGURE_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTENSIONS = {
    ".xyz",".mol",".mol2",".sdf",".pdb",
    ".out",".log",".gjf",".gjc",".fchk",
    ".cube",".cif",".smiles",
}
STYLES = ["default","flat","paton","pmol","skeletal","bubble","tube","wire","graph"]
STYLE_DESC = {
    "default":"CPK 渐变雾化","flat":"扁平 无渐变","paton":"PyMOL 风格",
    "pmol":"球棍+元素色键","skeletal":"骨架式","bubble":"空间填充",
    "tube":"管状棍","wire":"线框","graph":"图论风格",
}
GIF_AXES = ["y","x","z","xy","xz","yz","yx","zx","zy","-y","-x","-z","-xy","-xz","-yz"]
SURFACE_STYLES = ["solid","mesh","contour","dot"]
NCI_MODES      = ["avg","pixel","uniform"]
CMAP_PALETTES  = ["viridis","spectral","coolwarm","plasma","inferno","magma"]


# ── Geometry helpers ─────────────────────────────────────────────────────────
def _rot_euler(rx, ry, rz):
    Rx=np.array([[1,0,0],[0,math.cos(rx),-math.sin(rx)],[0,math.sin(rx),math.cos(rx)]])
    Ry=np.array([[math.cos(ry),0,math.sin(ry)],[0,1,0],[-math.sin(ry),0,math.cos(ry)]])
    Rz=np.array([[math.cos(rz),-math.sin(rz),0],[math.sin(rz),math.cos(rz),0],[0,0,1]])
    return Rz@Ry@Rx

def _parse_xyz(path):
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
    n=int(lines[0].strip()); comment=lines[1].strip() if len(lines)>1 else ""
    s,c=[],[]
    for line in lines[2:2+n]:
        p=line.split()
        if len(p)>=4:
            s.append(p[0]); c.append([float(p[1]),float(p[2]),float(p[3])])
    return s,np.array(c,dtype=float),comment

def _load_coords(path):
    if path.suffix.lower()==".xyz": return _parse_xyz(path)
    try:
        from xyzrender.io import load_molecule
        g=load_molecule(str(path)); nodes=sorted(g.nodes)
        return [g.nodes[i]["symbol"] for i in nodes],\
               np.array([list(g.nodes[i]["position"]) for i in nodes],dtype=float),\
               path.stem
    except Exception: pass
    try:
        import cclib; data=cclib.io.ccread(str(path))
        from cclib.parser.utils import PeriodicTable; pt=PeriodicTable()
        return [pt.element[z] for z in data.atomnos],np.array(data.atomcoords[-1],dtype=float),path.stem
    except Exception as e: raise ValueError(f"Cannot parse {path.name}: {e}") from e

def _write_xyz(path,symbols,coords,comment="rotated"):
    lines=[str(len(symbols)),comment]
    for sym,(x,y,z) in zip(symbols,coords):
        lines.append(f"{sym:<4s} {x:14.8f} {y:14.8f} {z:14.8f}")
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")


# ── Pages ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html",
        styles=STYLES, style_desc=STYLE_DESC, gif_axes=GIF_AXES,
        surface_styles=SURFACE_STYLES, nci_modes=NCI_MODES,
        cmap_palettes=CMAP_PALETTES)


# ── Molecule file management ─────────────────────────────────────────────────
@app.route("/api/molecules")
def list_molecules():
    return jsonify([
        {"name":f.name,"suffix":f.suffix.lower(),"size":f.stat().st_size}
        for f in sorted(MOLECULES_DIR.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])

@app.route("/api/upload",methods=["POST"])
def upload():
    if "file" not in request.files: return jsonify({"error":"No file part"}),400
    f=request.files["file"]
    if not f.filename: return jsonify({"error":"Empty filename"}),400
    suffix=Path(f.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS: return jsonify({"error":f"Unsupported: {suffix}"}),400
    f.save(MOLECULES_DIR/f.filename)
    return jsonify({"ok":True,"name":f.filename})

@app.route("/api/delete_molecule",methods=["POST"])
def delete_molecule():
    name=(request.json or {}).get("name","")
    path=MOLECULES_DIR/Path(name).name
    if not path.exists(): return jsonify({"error":"Not found"}),404
    path.unlink(); return jsonify({"ok":True})


# ── TEMP figures (preview) ───────────────────────────────────────────────────
@app.route("/api/temp_figures")
def list_temp_figures():
    figs=[]
    for f in TEMP_DIR.iterdir():
        if f.is_file():
            figs.append({"name":f.name,"suffix":f.suffix.lower(),"mtime":f.stat().st_mtime})
    figs.sort(key=lambda x:x["mtime"],reverse=True)
    return jsonify(figs)

@app.route("/api/delete_temp",methods=["POST"])
def delete_temp():
    name=(request.json or {}).get("name","")
    path=TEMP_DIR/Path(name).name
    if not path.exists(): return jsonify({"error":"Not found"}),404
    path.unlink(); return jsonify({"ok":True})

@app.route("/api/clear_temp",methods=["POST"])
def clear_temp():
    removed=0
    for f in TEMP_DIR.iterdir():
        if f.is_file(): f.unlink(); removed+=1
    return jsonify({"ok":True,"removed":removed})

@app.route("/temp/<path:filename>")
def serve_temp(filename):
    return send_from_directory(TEMP_DIR, filename)


# ── FIGURE files (saved) ─────────────────────────────────────────────────────
@app.route("/api/figures")
def list_figures():
    figs=[]
    for f in FIGURE_DIR.iterdir():
        if f.is_file():
            figs.append({"name":f.name,"suffix":f.suffix.lower(),"mtime":f.stat().st_mtime})
    figs.sort(key=lambda x:x["mtime"],reverse=True)
    return jsonify(figs)

@app.route("/api/save_figure",methods=["POST"])
def save_figure():
    """Copy a file from TEMP/ to FIGURE/."""
    d=request.json or {}
    name=d.get("name","")
    src=TEMP_DIR/Path(name).name
    if not src.exists(): return jsonify({"error":"Temp file not found"}),404
    dst=FIGURE_DIR/src.name
    shutil.copy2(src,dst)
    return jsonify({"ok":True,"saved":dst.name})

@app.route("/api/delete_figure",methods=["POST"])
def delete_figure():
    name=(request.json or {}).get("name","")
    path=FIGURE_DIR/Path(name).name
    if not path.exists(): return jsonify({"error":"Not found"}),404
    path.unlink(); return jsonify({"ok":True})

@app.route("/figures/<path:filename>")
def serve_figure(filename):
    return send_from_directory(FIGURE_DIR, filename)


# ── XYZ data for 3-D viewer ──────────────────────────────────────────────────
@app.route("/api/get_xyz",methods=["POST"])
def get_xyz():
    name=(request.json or {}).get("file","")
    if not name: return jsonify({"error":"No file"}),400
    path=MOLECULES_DIR/Path(name).name
    if not path.exists(): return jsonify({"error":"Not found"}),404
    try:
        symbols,coords,comment=_load_coords(path)
        return jsonify({"symbols":symbols,"coords":coords.tolist(),"n":len(symbols),"comment":comment})
    except ValueError as e: return jsonify({"error":str(e)}),500


# ── Rotation ─────────────────────────────────────────────────────────────────
@app.route("/api/rotate",methods=["POST"])
def rotate_molecule():
    d=request.json or {}
    src=MOLECULES_DIR/Path(d.get("file","")).name
    if not src.exists(): return jsonify({"error":"Not found"}),404
    try: symbols,coords,_=_load_coords(src)
    except ValueError as e: return jsonify({"error":str(e)}),500
    if len(coords)==0: return jsonify({"error":"No atoms"}),400
    M=d.get("matrix")
    if M: R=np.array(M,dtype=float)
    else:
        rx=float(d.get("rx",0)); ry=float(d.get("ry",0)); rz=float(d.get("rz",0))
        R=_rot_euler(math.radians(rx),math.radians(ry),math.radians(rz))
    c=coords.mean(axis=0)
    rotated=(R@(coords-c).T).T+c
    stem=src.stem
    if stem.endswith("_rotated"): stem=stem[:-8]
    out=MOLECULES_DIR/f"{stem}_rotated.xyz"
    _write_xyz(out,symbols,rotated,f"rotated from {src.name}")
    return jsonify({"ok":True,"rotated_file":out.name,"atom_count":len(symbols)})


# ── Render → TEMP ────────────────────────────────────────────────────────────
@app.route("/api/render",methods=["POST"])
def render_molecule():
    d=request.json or {}

    mol_file=d.get("file",""); fmt=d.get("format","svg").lower()
    smi=d.get("smi",""); mol_frame=d.get("mol_frame","")
    rebuild=d.get("rebuild",False); threshold=d.get("threshold","")
    charge=d.get("charge",""); mult=d.get("multiplicity","")
    style=d.get("style","default"); canvas_size=d.get("canvas_size","")
    atom_scale=d.get("atom_scale",""); bond_width=d.get("bond_width","")
    atom_stroke=d.get("atom_stroke_width",""); bond_color=d.get("bond_color","")
    bg_color=d.get("bg_color",""); transparent=d.get("transparent",False)
    gradient_on=d.get("gradient",None); gradient_str=d.get("gradient_strength","")
    fog_on=d.get("fog",None); fog_str=d.get("fog_strength","")
    vdw_opacity=d.get("vdw_opacity",""); vdw_scale=d.get("vdw_scale","")
    vdw_grad=d.get("vdw_gradient",""); dpi=d.get("dpi","")
    bond_by_elem=d.get("bond_by_element",None); bond_grad_f=d.get("bond_gradient",None)
    bond_cutoff=d.get("bond_cutoff",""); no_bonds=d.get("no_bonds",False)
    ts_color=d.get("ts_color",""); nci_color=d.get("nci_color","")
    show_h=d.get("hydrogens",False); no_hy=d.get("no_hy",False)
    hy_indices=d.get("hy_indices",""); bond_orders=d.get("bond_orders",None)
    kekule=d.get("kekule",False); vdw_range=d.get("vdw",None)
    dof=d.get("dof",False); dof_strength=d.get("dof_strength","")
    mol_color=d.get("mol_color",""); highlights=d.get("highlights",[])
    idx_mode=d.get("idx",""); stereo=d.get("stereo",False)
    stereo_style=d.get("stereo_style",""); annotations=d.get("annotations","")
    label_size=d.get("label_size",""); cmap_data=d.get("cmap_data","")
    cmap_range_v=d.get("cmap_range",""); cmap_symm=d.get("cmap_symm",False)
    cmap_palette=d.get("cmap_palette",""); cbar=d.get("cbar",False)
    no_orient=d.get("no_orient",False)
    ts_detect=d.get("ts",False); ts_frame=d.get("ts_frame","")
    ts_bond_pairs=d.get("ts_bond",""); nci=d.get("nci",False)
    nci_bond_pairs=d.get("nci_bond",""); surface_style=d.get("surface_style","")
    mo=d.get("mo",False); mo_pos_color=d.get("mo_pos_color","")
    mo_neg_color=d.get("mo_neg_color",""); mo_blur=d.get("mo_blur","")
    mo_upsample=d.get("mo_upsample",""); flat_mo=d.get("flat_mo",False)
    dens=d.get("dens",False); dens_color=d.get("dens_color","")
    esp_file=d.get("esp_file",""); nci_surf=d.get("nci_surf_file","")
    nci_mode=d.get("nci_mode",""); nci_cutoff=d.get("nci_cutoff","")
    iso_val=d.get("iso",""); opacity=d.get("opacity","")
    hull=d.get("hull",""); hull_color=d.get("hull_color","")
    hull_opacity=d.get("hull_opacity",""); hull_edge=d.get("hull_edge",None)
    hull_edge_ratio=d.get("hull_edge_ratio",""); overlay_file=d.get("overlay_file","")
    overlay_color=d.get("overlay_color",""); ensemble=d.get("ensemble",False)
    ensemble_color=d.get("ensemble_color",""); align_atoms=d.get("align_atoms","")
    conf_opacity=d.get("conf_opacity",""); regions=d.get("regions",[])
    gif_rot=d.get("gif_rot","y"); gif_ts=d.get("gif_ts",False)
    gif_trj=d.get("gif_trj",False); gif_diffuse=d.get("gif_diffuse",False)
    gif_fps=d.get("gif_fps",""); rot_frames=d.get("rot_frames","")
    crystal=d.get("crystal",""); cell=d.get("cell",False)
    no_cell=d.get("no_cell",False); cell_color=d.get("cell_color","")
    cell_width=d.get("cell_width",""); ghosts=d.get("ghosts",None)
    ghost_opacity=d.get("ghost_opacity",""); axes_show=d.get("axes",None)
    axis_dir=d.get("axis",""); supercell=d.get("supercell","")
    custom_json=d.get("custom_json","")

    # Input path
    if smi: input_path=None; stem="smiles_render"
    else:
        if not mol_file: return jsonify({"error":"No file"}),400
        input_path=MOLECULES_DIR/Path(mol_file).name
        if not input_path.exists(): return jsonify({"error":f"Not found: {mol_file}"}),404
        stem=input_path.stem

    # Output goes to TEMP
    parts=[style]
    if show_h or hy_indices: parts.append("hy")
    if ts_detect: parts.append("ts")
    if nci: parts.append("nci")
    if dens: parts.append("dens")
    if mo: parts.append("mo")
    if esp_file and not mo and not dens: parts.append("esp")
    if nci_surf: parts.append("ncisurf")
    if vdw_range is not None: parts.append("vdw")
    if dof: parts.append("dof")
    if hull: parts.append("hull")
    if ensemble: parts.append("ens")
    if overlay_file: parts.append("ovl")
    if gif_ts: parts.append("gts")
    if gif_trj: parts.append("trj")
    if gif_diffuse: parts.append("dif")
    out_name=f"{stem}_{'_'.join(parts)}.{fmt}"
    out_path=TEMP_DIR/out_name  # ← TEMP, not FIGURE

    # Build CLI command
    cmd=(["xyzrender","--smi",smi] if smi else ["xyzrender",str(input_path)])
    if fmt=="gif": cmd+=["-go",str(out_path)]
    else: cmd+=["-o",str(out_path)]

    if charge: cmd+=["-c",str(charge)]
    if mult: cmd+=["-m",str(mult)]
    if mol_frame: cmd+=["--mol-frame",str(mol_frame)]
    if rebuild: cmd+=["--rebuild"]
    if threshold: cmd+=["--threshold",str(threshold)]
    if style and style!="default": cmd+=["--config",style]
    if canvas_size: cmd+=["-S",str(canvas_size)]
    if atom_scale: cmd+=["-a",str(atom_scale)]
    if bond_width: cmd+=["-b",str(bond_width)]
    if atom_stroke: cmd+=["-s",str(atom_stroke)]
    if bond_color: cmd+=["--bond-color",bond_color]
    if ts_color: cmd+=["--ts-color",ts_color]
    if nci_color: cmd+=["--nci-color",nci_color]
    if bg_color and not transparent: cmd+=["-B",bg_color]
    if transparent: cmd+=["-t"]
    if gradient_str: cmd+=["-G",str(gradient_str)]
    if fog_str: cmd+=["-F",str(fog_str)]
    if vdw_opacity: cmd+=["--vdw-opacity",str(vdw_opacity)]
    if vdw_scale: cmd+=["--vdw-scale",str(vdw_scale)]
    if vdw_grad: cmd+=["--vdw-gradient",str(vdw_grad)]
    if bond_cutoff: cmd+=["--bond-cutoff",str(bond_cutoff)]
    if no_bonds: cmd+=["--no-bonds"]
    if gradient_on is True: cmd+=["--grad"]
    elif gradient_on is False: cmd+=["--no-grad"]
    if fog_on is True: cmd+=["--fog"]
    elif fog_on is False: cmd+=["--no-fog"]
    if bond_by_elem is True: cmd+=["--bond-by-element"]
    elif bond_by_elem is False: cmd+=["--no-bond-by-element"]
    if bond_grad_f is True: cmd+=["--bond-gradient"]
    elif bond_grad_f is False: cmd+=["--no-bond-gradient"]
    if no_hy: cmd+=["--no-hy"]
    elif hy_indices: cmd+=["--hy"]+str(hy_indices).split()
    elif show_h: cmd+=["--hy"]
    if bond_orders is True: cmd+=["--bo"]
    elif bond_orders is False: cmd+=["--no-bo"]
    if kekule: cmd+=["-k"]
    if vdw_range is not None:
        r=str(vdw_range).strip(); cmd+=(["--vdw",r] if r else ["--vdw"])
    if dof:
        cmd+=["--dof"]
        if dof_strength: cmd+=["--dof-strength",str(dof_strength)]
    if mol_color: cmd+=["--mol-color",mol_color]
    for hl in highlights:
        a=str(hl.get("atoms","")).strip(); c2=str(hl.get("color","")).strip()
        if a: cmd+=(["--hl",a,c2] if c2 else ["--hl",a])
    if idx_mode:
        if idx_mode in("sn","s","n"): cmd+=["--idx",idx_mode]
        elif idx_mode=="true": cmd+=["--idx"]
    if stereo:
        cmd+=["--stereo"] if not isinstance(stereo,list) else ["--stereo"]+stereo
        if stereo_style: cmd+=["--stereo-style",stereo_style]
    if annotations:
        for line in annotations.strip().splitlines():
            if line.strip(): cmd+=["-l",line.strip()]
    if label_size: cmd+=["--label-size",str(label_size)]
    tmp_cmap=None
    if cmap_data:
        tmp_cmap=BASE_DIR/"tmp_cmap.txt"; tmp_cmap.write_text(cmap_data,encoding="utf-8")
        cmd+=["--cmap",str(tmp_cmap)]
        pr=cmap_range_v.strip().split()
        if len(pr)==2: cmd+=["--cmap-range"]+pr
        if cmap_symm: cmd+=["--cmap-symm"]
        if cmap_palette: cmd+=["--cmap-palette",cmap_palette]
        if cbar: cmd+=["--cbar"]
    if no_orient: cmd+=["--no-orient"]
    if ts_detect: cmd+=["--ts"]
    if ts_frame: cmd+=["--ts-frame",str(ts_frame)]
    if ts_bond_pairs: cmd+=["--ts-bond",ts_bond_pairs]
    if nci: cmd+=["--nci"]
    if nci_bond_pairs: cmd+=["--nci-bond",nci_bond_pairs]
    if surface_style: cmd+=["--surface-style",surface_style]
    if mo:
        cmd+=["--mo"]
        if flat_mo: cmd+=["--flat-mo"]
        if mo_blur: cmd+=["--mo-blur",str(mo_blur)]
        if mo_upsample: cmd+=["--mo-upsample",str(mo_upsample)]
        if mo_pos_color or mo_neg_color:
            cmd+=["--mo-colors",mo_pos_color or "steelblue",mo_neg_color or "maroon"]
    elif dens:
        cmd+=["--dens"]
        if dens_color: cmd+=["--dens-color",dens_color]
    elif esp_file:
        ep=MOLECULES_DIR/Path(esp_file).name
        if not ep.exists(): return jsonify({"error":f"ESP cube not found"}),404
        cmd+=["--esp",str(ep)]
    elif nci_surf:
        np2=MOLECULES_DIR/Path(nci_surf).name
        if not np2.exists(): return jsonify({"error":f"NCI-surf not found"}),404
        cmd+=["--nci-surf",str(np2)]
        if nci_mode: cmd+=["--nci-mode",nci_mode]
        if nci_cutoff: cmd+=["--nci-cutoff",str(nci_cutoff)]
    if iso_val: cmd+=["--iso",str(iso_val)]
    if opacity: cmd+=["--opacity",str(opacity)]
    if hull:
        hs=str(hull).strip()
        if hs in("all","true"): cmd+=["--hull"]
        elif hs=="rings": cmd+=["--hull","rings"]
        elif hs:
            for sub in hs.split("|"): cmd+=["--hull",sub.strip()]
        if hull_color:
            for hc in hull_color.split(","):
                if hc.strip(): cmd+=["--hull-color",hc.strip()]
        if hull_opacity: cmd+=["--hull-opacity",str(hull_opacity)]
        if hull_edge is True: cmd+=["--hull-edge"]
        elif hull_edge is False: cmd+=["--no-hull-edge"]
        if hull_edge_ratio: cmd+=["--hull-edge-width-ratio",str(hull_edge_ratio)]
    if overlay_file:
        ovl=MOLECULES_DIR/Path(overlay_file).name
        if ovl.exists():
            cmd+=["--overlay",str(ovl)]
            if overlay_color: cmd+=["--overlay-color",overlay_color]
            if align_atoms: cmd+=["--align-atoms",align_atoms]
    if ensemble:
        cmd+=["--ensemble"]
        if ensemble_color: cmd+=["--ensemble-color",ensemble_color]
        if align_atoms and not overlay_file: cmd+=["--align-atoms",align_atoms]
        if conf_opacity: cmd+=["--opacity",str(conf_opacity)]
    for reg in regions:
        ra=str(reg.get("atoms","")).strip(); rp=str(reg.get("preset","")).strip()
        if ra and rp: cmd+=["--region",ra,rp]
    if fmt=="gif":
        if gif_diffuse: cmd+=["--gif-diffuse"]
        elif gif_ts and gif_rot: cmd+=["--gif-ts","--gif-rot",gif_rot]
        elif gif_ts: cmd+=["--gif-ts"]
        elif gif_trj: cmd+=["--gif-trj"]
        else: cmd+=["--gif-rot",gif_rot]
        if gif_fps: cmd+=["--gif-fps",str(gif_fps)]
        if rot_frames: cmd+=["--rot-frames",str(rot_frames)]
    if crystal:
        if crystal in("vasp","qe"): cmd+=["--crystal",crystal]
        else: cmd+=["--crystal"]
    if cell: cmd+=["--cell"]
    if no_cell: cmd+=["--no-cell"]
    if cell_color: cmd+=["--cell-color",cell_color]
    if cell_width: cmd+=["--cell-width",str(cell_width)]
    if ghosts is True: cmd+=["--ghosts"]
    elif ghosts is False: cmd+=["--no-ghosts"]
    if ghost_opacity: cmd+=["--ghost-opacity",str(ghost_opacity)]
    if axes_show is True: cmd+=["--axes"]
    elif axes_show is False: cmd+=["--no-axes"]
    if axis_dir: cmd+=["--axis",axis_dir]
    if supercell:
        ps=supercell.strip().split()
        if len(ps)==3: cmd+=["--supercell"]+ps
    tmp_cfg=None
    try:
        if custom_json:
            cfg=json.loads(custom_json)
            if dpi: cfg.setdefault("dpi",int(dpi))
            tmp_cfg=BASE_DIR/"tmp_config.json"; tmp_cfg.write_text(json.dumps(cfg))
            cmd+=["--config",str(tmp_cfg)]
        elif dpi and fmt in("png","pdf"):
            tmp_cfg=BASE_DIR/"tmp_config.json"; tmp_cfg.write_text(json.dumps({"dpi":int(dpi)}))
            cmd+=["--config",str(tmp_cfg)]
    except json.JSONDecodeError: return jsonify({"error":"Invalid custom JSON"}),400

    try:
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
    except subprocess.TimeoutExpired: return jsonify({"error":"Render timed out"}),500
    finally:
        for tmp in [tmp_cfg,tmp_cmap]:
            if tmp and Path(tmp).exists(): Path(tmp).unlink(missing_ok=True)

    if result.returncode!=0:
        return jsonify({"error":(result.stderr or result.stdout or "Unknown").strip()}),500
    return jsonify({"ok":True,"output":out_name,"cmd":" ".join(cmd)})


# ── Static ───────────────────────────────────────────────────────────────────
@app.route("/molecules/<path:filename>")
def serve_molecule(filename): return send_from_directory(MOLECULES_DIR,filename)

if __name__=="__main__":
    print("="*60)
    print("  xyzrender Web App  v5")
    print(f"  Molecules : {MOLECULES_DIR.resolve()}")
    print(f"  TEMP      : {TEMP_DIR.resolve()}")
    print(f"  FIGURE    : {FIGURE_DIR.resolve()}")
    print("="*60)
    app.run(debug=True,port=5000)
