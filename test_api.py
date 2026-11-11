from fastapi.testclient import TestClient
from main import app

c = TestClient(app)


def ok(path, method="get", **kw):
    r = getattr(c, method)(path, **kw)
    assert r.status_code == 200, (path, r.status_code, r.text[:200])
    return r.json()


def test_core():
    assert ok("/health")["status"] == "ok"
    assert len(ok("/api/crops")) == 9
    assert 2025 in ok("/api/years")
    assert ok("/api/environment/2024")["year"] == 2024


def test_model():
    body = {"year": 2025, "ph": 7.5, "texture": "clay", "water_index": 55, "previous": "Maize", "season": "winter"}
    r = ok("/api/predict", "post", json=body)
    assert r["top_crop"]["crop"] and len(r["alternatives"]) == 2
    r = ok("/api/recommend", "post", json={"year": 2025, "next_season": "summer"})
    assert r["next_cycle"]["top_crop"] and r["two_season_rotations"]
    assert c.post("/api/predict", json={**body, "texture": "rock"}).status_code == 400


def test_data():
    s = ok("/api/data/summary")
    assert s["climate_daily"]["rows"] == 3653
    assert len(ok("/api/data/climate/daily?start=2020-01-01&end=2020-01-10&variables=T2M")["rows"]) == 10
    assert len(ok("/api/data/climate/monthly?year=2020")["rows"]) == 12
    assert ok("/api/data/vegetation?year=2020")["count"] > 0
    assert len(ok("/api/data/soil")["rows"]) == 6
    assert ok("/api/data/crops/yield?crop=Wheat")["count"] == 10
    assert c.get("/api/data/crops/yield?crop=Nope").status_code == 404
    assert c.get("/api/data/climate/daily?variables=BAD").status_code == 400


def test_grid_and_dashboard():
    assert len(ok("/api/grid/layers")) == 6
    assert ok("/api/grid/et/monthly?year=2020")["count"] == 12
    assert ok("/api/grid/lai/monthly?year=2020&lat=30.5&lon=31.0")["count"] == 12
    assert ok("/api/grid/ndmi/yearly")["count"] >= 9
    assert ok("/api/grid/aerosol/map?year=2020&month=6")["count"] > 0
    assert c.get("/api/grid/xyz/monthly").status_code == 404
    assert c.get("/api/grid/et/monthly?lat=30").status_code == 400
    d = ok("/api/dashboard/2024")
    assert d["annual_environment"]["year"] == 2024 and len(d["climate_monthly"]) == 12
    assert c.get("/api/dashboard/1999").status_code == 404
