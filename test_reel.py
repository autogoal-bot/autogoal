import requests
from api_client import get_partidos_jornada, get_clasificacion
from config import FOOTBALL_DATA_TOKEN, FOOTBALL_DATA_BASE, LALIGA_CODE
from reel import generar_reel

JORNADA = 2

# --- Resultados ---
partidos = []
for m in get_partidos_jornada(JORNADA):
    if m["status"] != "FINISHED":
        continue
    partidos.append({
        "home_full": m["homeTeam"]["name"],
        "away_full": m["awayTeam"]["name"],
        "home": m["homeTeam"].get("shortName") or m["homeTeam"]["name"],
        "away": m["awayTeam"].get("shortName") or m["awayTeam"]["name"],
        "gh": m["score"]["fullTime"]["home"],
        "ga": m["score"]["fullTime"]["away"],
    })
print(f"Partidos terminados: {len(partidos)}")

# --- Clasificacion ---
tabla = get_clasificacion()["standings"][0]["table"]

# --- Pichichi ---
r = requests.get(f"{FOOTBALL_DATA_BASE}/competitions/{LALIGA_CODE}/scorers",
                 headers={"X-Auth-Token": FOOTBALL_DATA_TOKEN}, timeout=20)
pichichis = [{"nombre": s["player"]["name"], "goles": s.get("goals", 0), "equipo": s["team"].get("shortName") or s["team"]["name"]}
             for s in r.json().get("scorers", [])]
print(f"Pichichis: {len(pichichis)}")

ruta = generar_reel(JORNADA, partidos, tabla, pichichis)
print("Reel generado:", ruta)
