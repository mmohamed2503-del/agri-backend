# Field Shift API (FastAPI)

```bash
pip install -r requirements.txt
uvicorn main:app --reload      # http://127.0.0.1:8000/docs
python -m pytest -q            # tests
```

Model: POST /api/predict, POST /api/recommend, GET /api/crops, /api/years, /api/environment/{year}
Data:  GET /api/data/summary | climate/daily | climate/monthly | vegetation | soil | crops | crops/yield
Grid layers: GET /api/grid/layers | /{layer}/monthly | /{layer}/yearly | /{layer}/map   (layers: et, aerosol, solar, lai, gpp, ndmi)
Dashboard: GET /api/dashboard/{year}
NASA POWER (needs internet): POST /api/nasa-power, /api/wheat-weather, /api/compare-weather
