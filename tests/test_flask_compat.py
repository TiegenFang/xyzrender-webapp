from app import app


def test_flask_default_render_and_capabilities():
    client = app.test_client()
    assert client.get("/").status_code == 200
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["ok"] is True
    capabilities = client.get("/api/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.get_json()["xyzrender_version"] == "0.3.1"
    response = client.post("/api/render", json={"file": "caffeine.xyz", "format": "svg", "style": "default"})
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_unmapped_web_option_uses_legacy_compatibility():
    response = app.test_client().post("/api/render", json={
        "file": "caffeine.xyz", "format": "svg", "style": "default", "h_scale": "0.7",
    })
    assert response.status_code == 200
    assert "--h-scale 0.7" in response.get_json()["cmd"]


def test_original_web_highlight_region_and_annotation_features():
    response = app.test_client().post("/api/render", json={
        "file": "caffeine.xyz",
        "format": "svg",
        "style": "default",
        "highlights": [{"atoms": "1-3", "color": "gold"}],
        "regions": [{"atoms": "4-6", "preset": "flat"}],
        "idx": "n",
        "ts_bond": "1-2",
    })
    assert response.status_code == 200
    command = response.get_json()["cmd"]
    assert "--hl 1-3 gold" in command
    assert "--region 4-6 flat" in command
    assert "--idx n" in command
    assert "--ts-bond 1-2" in command


def test_v1_embeds_orientation_canvas_beside_render_output():
    response = app.test_client().get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<span class="release-label">V1</span>' not in html
    assert "XYZRender Workstation V1" not in html
    assert 'id="view-workspace"' in html
    assert html.index('id="orientation-pane"') < html.index('id="render-pane"')
    assert 'id="molc"' in html
    assert 'id="viewer-style"' in html
    assert "style:'HoukMol'" in html
    assert "preserveAspectRatio','xMidYMid meet'" in html
    assert "for(const pair of bonds||[])" in html
    assert "if(st.crosshair)" not in html
    assert 'id="vapl"' in html
    assert 'loadViewer(name)' in html
    assert "mc.addEventListener('pointerdown'" in html
    assert 'id="vmodal"' not in html
    assert 'id="ovbtn"' not in html


def test_orientation_api_returns_file_or_conservative_connectivity():
    client = app.test_client()

    pdb = client.post("/api/get_xyz", json={"file": "c2c1im.pdb"})
    assert pdb.status_code == 200
    pdb_data = pdb.get_json()
    assert pdb_data["bond_source"] == "inferred"
    assert len(pdb_data["bonds"]) == 19
    assert [0, 2] not in pdb_data["bonds"]  # non-neighbouring ring atoms

    mol = client.post("/api/get_xyz", json={"file": "HAN.mol"})
    assert mol.status_code == 200
    mol_data = mol.get_json()
    assert mol_data["bond_source"] == "file"
    assert len(mol_data["bonds"]) == 7
