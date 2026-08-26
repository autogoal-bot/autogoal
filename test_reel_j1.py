import requests
from datetime import datetime, timedelta
from api_client import get_partidos_jornada, get_clasificacion
from config import FOOTBALL_DATA_TOKEN, FOOTBALL_DATA_BASE, LALIGA_CODE
from reel import generar_reel

JORNADA = 1
DIAS = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]

partidos = []
for m in get_partidos_jornada(JORNADA):
    fin = m["status"] == "FINISHED"
    f = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")) + timedelta(hours=2)
    partidos.append({
        "home_full": m["homeTeam"]["name"],
        "away_full": m["awayTeam"]["name"],
        "home": m["homeTeam"].get("shortName") or m["homeTeam"]["name"],
        "away": m["awayTeam"].get("shortName") or m["awayTeam"]["name"],
        "gh": m["score"]["fullTime"]["home"] if fin else None,
        "ga": m["score"]["fullTime"]["away"] if fin else None,
        "cuando": f"{DIAS[f.weekday()]} {f.strftime('%H:%M')}",
    })

print(f"Partidos: {len(partidos)} ({sum(1 for p in partidos if p['gh'] is None)} pendientes)")

tabla = get_clasificacion()["standings"][0]["table"]
print("Lider:", tabla[0]["team"]["name"], tabla[0]["points"], "pts")

r = requests.get(f"{FOOTBALL_DATA_BASE}/competitions/{LALIGA_CODE}/scorers",
                 headers={"X-Auth-Token": FOOTBALL_DATA_TOKEN}, timeout=20)
pichichis = [{"nombre": s["player"]["name"], "goles": s.get("goals", 0),
              "equipo": s["team"].get("shortName") or s["team"]["name"],
              "equipo_full": s["team"]["name"]}
             for s in r.json().get("scorers", [])]

print("Reel:", generar_reel(JORNADA, partidos, tabla, pichichis))
