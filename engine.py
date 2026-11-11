"""Field Shift: transparent, educational crop suitability and rotation prototype.
Rules are illustrative assumptions, NOT agronomic recommendations or learned labels.
"""
from pathlib import Path
import argparse, json, math
import pandas as pd

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'outputs'/'annual_environment.csv'
# Example thresholds only: must be replaced with location-specific agronomist-reviewed crop data.
# Water is a *relative planning index*, not measured crop irrigation in mm.
CROPS={
 'Wheat':dict(season='winter',family='cereal',temp=(12,23),ph=(6,8),textures=['loam','clay'],water=45),
 'Barley':dict(season='winter',family='cereal',temp=(10,23),ph=(6,8.5),textures=['loam','clay','sand'],water=30),
 'Fava beans':dict(season='winter',family='legume',temp=(12,23),ph=(6,8),textures=['loam','clay'],water=40),
 'Peas':dict(season='winter',family='legume',temp=(10,22),ph=(6,7.8),textures=['loam','clay'],water=35),
 'Sugar beet':dict(season='winter',family='root',temp=(12,24),ph=(6.5,8),textures=['loam','clay'],water=55),
 'Onions':dict(season='winter',family='allium',temp=(12,25),ph=(6,7.8),textures=['loam','sand'],water=40),
 'Maize':dict(season='summer',family='cereal',temp=(22,34),ph=(5.8,7.8),textures=['loam','clay'],water=70),
 'Tomatoes':dict(season='summer',family='solanaceae',temp=(18,32),ph=(6,7.5),textures=['loam','sand'],water=60),
 'Watermelon':dict(season='summer',family='cucurbit',temp=(22,35),ph=(6,7.5),textures=['loam','sand'],water=65),
}

def triangular_fit(value, low, high, soft_margin):
    """1 within illustrative range, linearly declining outside it."""
    if low <= value <= high: return 1.0
    return max(0.,1.-(low-value if value<low else value-high)/soft_margin)

def season_temperature(annual_temp,season):
    # Annual NASA temperature is NOT crop-season temperature. This is an illustrative
    # seasonal offset, to be replaced with actual seasonal NASA composites.
    return annual_temp + (-5 if season=='winter' else 6)

def score_crop(name, env, farm, previous=None):
    c=CROPS[name]
    annual_temp = finite_number(env.get('T2M'))
    if annual_temp is None:
        raise ValueError('Regional mean temperature (T2M) is unavailable for this year.')
    t=season_temperature(annual_temp,c['season'])
    components={
      'temperature':triangular_fit(t,*c['temp'],soft_margin=10),
      'soil_ph':triangular_fit(float(farm['ph']),*c['ph'],soft_margin=1.5),
      'soil_texture':1. if farm['texture'] in c['textures'] else 0.45,
      'water':min(1.,float(farm['water_index'])/c['water']),
    }
    # Legume sequence credit is illustrative; it does not quantify nitrogen fixation.
    rotation_factor=0.65 if previous and previous in CROPS and CROPS[previous]['family']==c['family'] else 1.
    weights={'temperature':0.30,'soil_ph':0.20,'soil_texture':0.20,'water':0.30}
    score=100*sum(components[k]*weights[k] for k in weights)*rotation_factor
    reasons=[k for k,v in components.items() if v<0.8]
    if rotation_factor<1:reasons.append('same_crop_family_as_previous')
    return {'crop':name,'season':c['season'],'score':round(score,1), 'components':{k:round(v,2) for k,v in components.items()},'limiting_factors':reasons,'water_index_required':c['water'],'previous_crop':previous,'model_type':'illustrative_rules_not_trained_ml'}

def recommend(env,farm,previous=None,season=None):
    rows=[score_crop(n,env,farm,previous) for n,c in CROPS.items() if season is None or c['season']==season]
    return sorted(rows,key=lambda x:x['score'],reverse=True)

ROTATION_PRIORITIES = ("balanced", "water", "diversity")


def rotations(env,farm,previous=None,top=5,*,priority="balanced"):
    """Generate two-season winter→summer sequences with a simple family-diversity bonus."""
    if priority not in ROTATION_PRIORITIES:
        raise ValueError("Unknown rotation priority")
    options=[]
    for winter in CROPS:
        if CROPS[winter]['season']!='winter':continue
        a=score_crop(winter,env,farm,previous)
        for summer in CROPS:
            if CROPS[summer]['season']!='summer':continue
            b=score_crop(summer,env,farm,winter)
            diversity_bonus=5 if CROPS[winter]['family']!=CROPS[summer]['family'] else 0
            # Legume credit is an illustrative planning preference, not measured soil outcome.
            legume_bonus=3 if CROPS[winter]['family']=='legume' else 0
            combined=round((a['score']+b['score'])/2+diversity_bonus+legume_bonus,1)
            families = {CROPS[winter]['family'], CROPS[summer]['family']}
            if previous in CROPS:
                families.add(CROPS[previous]['family'])
            options.append({'winter_crop':winter,'summer_crop':summer,'planning_score':min(100,combined),'winter_suitability':a['score'],'summer_suitability':b['score'],'relative_water_demand_index':CROPS[winter]['water']+CROPS[summer]['water'],'distinct_crop_families':len(families),'legume_in_rotation':CROPS[winter]['family']=='legume','warnings':list(dict.fromkeys(a['limiting_factors']+b['limiting_factors']))})
    ranking_keys = {
        "balanced": lambda row: -row["planning_score"],
        "water": lambda row: (row["relative_water_demand_index"], -row["planning_score"]),
        "diversity": lambda row: (-row["distinct_crop_families"], -row["planning_score"]),
    }
    return sorted(options, key=ranking_keys[priority])[:top]

def finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def read_environment():
    table = pd.read_csv(DATA)
    if 'year' not in table:
        raise ValueError('The regional environmental CSV needs a year column.')
    years = pd.to_numeric(table['year'], errors='coerce')
    valid = years.between(1, 9999) & years.mod(1).eq(0)
    table = table.loc[valid].copy()
    table['year'] = years[valid].astype(int)
    if table['year'].duplicated().any():
        raise ValueError('The regional environmental CSV contains duplicate years.')
    return table.set_index('year')


def available_years():
    return sorted(read_environment().index.tolist(), reverse=True)


def load_environment(year=2024):
    table = read_environment()
    if year not in table.index:
        raise ValueError(f'No regional annual environmental data for {year}.')
    return {'year': year, **{key: finite_number(value) for key, value in table.loc[year].items()}}

def run(year=2024,ph=7.5,texture='clay',water_index=55,previous='Maize',*,next_season=None,rotation_priority="balanced"):
    if next_season not in (None, 'winter', 'summer'):
        raise ValueError('next_season must be winter or summer')
    if not 3<=ph<=10:raise ValueError('pH must be 3–10')
    if texture not in ('clay','loam','sand'):raise ValueError('texture must be clay, loam, or sand')
    if not 0<=water_index<=100:raise ValueError('water_index must be 0–100')
    env=load_environment(year)
    farm={'ph':ph,'texture':texture,'water_index':water_index}
    result = {'study_area':'Approximate Nile Delta aggregate; not a farm geolocation','environment_year':year,'environment_source':'Uploaded NASA-derived annual_environment.csv','farm_inputs':farm,'previous_crop':previous,'crop_recommendations':recommend(env,farm,previous),'rotation_priority':rotation_priority,'two_season_rotations':rotations(env,farm,previous,priority=rotation_priority),'limitations':['Heuristic scores and thresholds are illustrative, not scientifically calibrated or validated.','Temperature uses approximate seasonal offsets from annual NASA averages, not actual crop-season observations.','Water index is user-provided relative availability (0–100), not irrigation volume or crop water demand in mm.','NASA data is Nile Delta aggregate, not farm-specific.','No validated crop-rotation, soil nutrient, salinity, economics, or yield response data.','Do not use for real planting decisions without local agronomist review.']}
    if next_season is not None:
        candidates = [row for row in result['crop_recommendations'] if row['season'] == next_season]
        first, *alternatives = candidates
        result['next_cycle'] = {
            'season': next_season,
            'top_crop': first,
            'alternatives': alternatives[:2],
            'tied_top_crops': [row['crop'] for row in candidates if row['score'] == first['score']],
        }
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--year',type=int,default=2024);p.add_argument('--ph',type=float,default=7.5);p.add_argument('--texture',choices=['clay','loam','sand'],default='clay');p.add_argument('--water-index',type=float,default=55);p.add_argument('--previous',default='Maize');p.add_argument('--output',default=str(ROOT/'outputs'/'demo_recommendations.json'))
    a=p.parse_args();result=run(a.year,a.ph,a.texture,a.water_index,a.previous)
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Saved',a.output)
    for r in result['crop_recommendations'][:5]:print(r['crop'],r['score'],r['limiting_factors'])
