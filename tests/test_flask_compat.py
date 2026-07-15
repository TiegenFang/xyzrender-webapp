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
