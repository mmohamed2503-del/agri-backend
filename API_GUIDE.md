# Field Shift API — دليل الفرونت

**Base URL (محلي):** `http://127.0.0.1:8000`
**التوثيق التفاعلي:** `http://127.0.0.1:8000/docs`
**الصيغة:** كل الردود JSON. الـ POST بيستقبل JSON مع `Content-Type: application/json`.

## التشغيل
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## الأخطاء
| الكود | المعنى | الشكل |
|---|---|---|
| 400 | قيمة غلط (مثلاً texture غير مدعومة) | `{"detail": "رسالة نصية"}` |
| 404 | سنة/محصول/طبقة مش موجودة | `{"detail": "رسالة نصية"}` |
| 422 | نوع بيانات غلط (مثلاً حروف مكان رقم) | `{"detail": [ {loc, msg, ...} ]}` |
| 503 | ملف داتا ناقص على السيرفر | `{"detail": "..."}` |

القيم الفاضية (NaN) بترجع `null`.

---

## 1) الموديل

### `POST /api/predict` — أنسب محصول للموسم الجاي
**Body** (كله اختياري وله قيم افتراضية):
```json
{ "year": 2025, "ph": 7.5, "texture": "clay", "water_index": 55, "previous": "Maize", "season": "winter" }
```
| الحقل | القيم المسموحة |
|---|---|
| year | 2016 – 2025 |
| ph | 3 – 10 |
| texture | `clay` / `loam` / `sand` |
| water_index | 0 – 100 (مؤشر نسبي لتوفر المياه) |
| previous | اسم محصول من `/api/crops` أو `null` |
| season | `winter` / `summer` |

**Response:**
```json
{
  "model_type": "trained_rule_surrogate",
  "season": "winter",
  "top_crop": { "crop": "Fava beans", "score": 100.0 },
  "alternatives": [ { "crop": "Peas", "score": 100.0 }, { "crop": "Sugar beet", "score": 100.0 } ],
  "tied_top_crops": ["Fava beans", "Peas", "Sugar beet"]
}
```
> لو `tied_top_crops` فيها أكتر من محصول، يبقوا متساويين في الدرجة، اعرضهم كلهم مش بس `top_crop`.

### `POST /api/recommend` — ترتيب كل المحاصيل + التناوب الزراعي
**Body:**
```json
{ "year": 2025, "ph": 7.5, "texture": "clay", "water_index": 55, "previous": null,
  "next_season": "summer", "rotation_priority": "balanced" }
```
`rotation_priority`: `balanced` / `water` (أقل استهلاك مياه) / `diversity` (أكتر تنوع).
`next_season` اختياري (`winter` / `summer`)، ولو اتبعت بيظهر `next_cycle` في الرد.

**Response (المفاتيح):** `crop_recommendations` (كل المحاصيل مرتبة) و`two_season_rotations` (أفضل 5 تناوبات) و`next_cycle` و`limitations` و`farm_inputs`.
```json
// عنصر من crop_recommendations
{ "crop": "Wheat", "season": "winter", "score": 100.0,
  "components": { "temperature": 1.0, "soil_ph": 1.0, "soil_texture": 1.0, "water": 1.0 },
  "limiting_factors": [], "water_index_required": 45 }

// عنصر من two_season_rotations
{ "winter_crop": "Fava beans", "summer_crop": "Maize", "planning_score": 100,
  "winter_suitability": 100.0, "summer_suitability": 93.6,
  "relative_water_demand_index": 110, "distinct_crop_families": 2,
  "legume_in_rotation": true, "warnings": ["water"] }
```
`limiting_factors` / `warnings` = العوامل اللي بتقلل الدرجة (`temperature`, `soil_ph`, `soil_texture`, `water`, `same_crop_family_as_previous`).
`limitations` = نصوص تحفظات لازم تتعرض للمستخدم في الواجهة.

### مساعدة
- `GET /api/crops` ← المحاصيل التسعة، كل واحد فيه season وfamily ونطاقات الملاءمة.
- `GET /api/years` ← `[2025, 2024, ..., 2016]` (لقائمة اختيار السنة).
- `GET /api/environment/{year}` ← قياسات السنة (T2M, rainfall, RH2M, NDVI, EVI, ...).
- `GET /api/environment/all` ← كل السنين.

---

## 2) الداتا

### `GET /api/dashboard/{year}` — كل اللي الداشبورد محتاجه في طلب واحد
**Response (المفاتيح):** `year`, `annual_environment`, `climate_monthly` (12 صف), `vegetation_16day`, `soil` (6 أعماق), `crop_yields`.

### المناخ والنبات والتربة والمحاصيل
| Endpoint | Query | الوصف |
|---|---|---|
| `GET /api/data/summary` | — | ملخص كل الداتا |
| `GET /api/data/climate/daily` | `start`, `end` (YYYY-MM-DD), `variables` (مثلاً `T2M,RH2M`), `limit` | مناخ يومي |
| `GET /api/data/climate/monthly` | `year` | مناخ شهري |
| `GET /api/data/vegetation` | `year` | EVI و NDVI كل 16 يوم |
| `GET /api/data/soil` | — | خصائص التربة حسب العمق |
| `GET /api/data/crops` | — | أسماء المحاصيل (إنجليزي + عربي) |
| `GET /api/data/crops/yield` | `crop` (مثلاً `Wheat`) | المساحة والإنتاج والإنتاجية سنوياً |

متغيرات المناخ: `T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, RH2M, ALLSKY_SFC_SW_DWN, WS2M, GWETTOP, GWETROOT`.
> بيانات المحاصيل لمصر كلها مش للدلتا فقط.

### الطبقات الشبكية (للخرائط والرسوم)
الطبقات: `et`, `aerosol`, `solar`, `lai`, `gpp`, `ndmi`.

| Endpoint | Query | الوصف |
|---|---|---|
| `GET /api/grid/layers` | — | قائمة الطبقات ومتغيراتها وفترتها |
| `GET /api/grid/{layer}/monthly` | `year`, `lat`+`lon` | متوسط شهري (لو lat/lon اتبعتوا = أقرب خلية، وإلا متوسط الكل) |
| `GET /api/grid/{layer}/yearly` | `lat`+`lon` | متوسط سنوي |
| `GET /api/grid/{layer}/map` | `year` (مطلوب), `month` | قيمة لكل خلية: `{lat, lon, ...}` للخريطة |

`lat` و`lon` لازم يتبعتوا مع بعض أو يتسابوا مع بعض.

---

## 3) NASA POWER (طقس حي — محتاج إنترنت على السيرفر)
- `POST /api/nasa-power` ← `{ "latitude": 30.8, "longitude": 31.0, "year": 2024 }`
- `POST /api/wheat-weather` ← `{ "latitude": 30.8, "longitude": 31.0, "start_date": "2024-11-15", "end_date": "2025-04-30" }`
- `POST /api/compare-weather` ← `{ latitude, longitude, selected_start, selected_end, reference_start, reference_end }`

---

## أمثلة JavaScript
```javascript
const API = "http://127.0.0.1:8000";

async function api(path, body) {
  const res = await fetch(API + path, body ? {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  } : undefined);
  const data = await res.json();
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Invalid input");
  return data;
}

// داشبورد سنة
const dash = await api("/api/dashboard/2024");

// المحصول المقترح
const pred = await api("/api/predict", { year: 2025, ph: 7.5, texture: "clay", water_index: 55, previous: "Maize", season: "winter" });

// خريطة طبقة ET لشهر معين
const map = await api("/api/grid/et/map?year=2024&month=6");
```

## ملاحظات مهمة
1. **الدرجات (0–100) مؤشرات تخطيط مش احتمالات نجاح**، والموديل بيحاكي قواعد تقييم افتراضية (مش مُدرَّب على إنتاج حقلي فعلي). اعرض `limitations` في الواجهة.
2. بيانات البيئة لمنطقة الدلتا ككل مش لمزرعة معينة.
3. بعض قيم 2025 فاضية (`null`) زي GPP، فتعامل معاها في الرسوم.
4. الـ CORS مفتوح للكل حالياً، ويتقفل على دومين الفرونت قبل النشر.
