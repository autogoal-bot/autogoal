"""
Genera el reel de una jornada con el titular elegido por titulares.py.

Uso:  python3 generar_reel_jornada.py 5
NO escribe titulares.json: generar es repetible y sin efectos.
Cuando publiques de verdad, llama a titulares.recordar(jornada, club).
"""
import sys
import requests
from datetime import datetime, timedelta

from api_client import (get_partidos_jornada, get_clasificacion,
                        get_temporada_terminada)
from config import FOOTBALL_DATA_TOKEN, FOOTBALL_DATA_BASE, LALIGA_CODE
import titulares
import reel
from reel import generar_reel

JORNADA = int(sys.argv[1]) if len(sys.argv) > 1 else 5
DIAS = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]

partidos = []
for m in get_partidos_jornada(JORNADA):
    fin = m["status"] == "FINISHED"
    f = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")) + timedelta(hours=2)
    partidos.append({
        "home_full": m["homeTeam"]["name"], "away_full": m["awayTeam"]["name"],
        "home": m["homeTeam"].get("shortName") or m["homeTeam"]["name"],
        "away": m["awayTeam"].get("shortName") or m["awayTeam"]["name"],
        "gh": m["score"]["fullTime"]["home"] if fin else None,
        "ga": m["score"]["fullTime"]["away"] if fin else None,
        "cuando": f"{DIAS[f.weekday()]} {f.strftime('%H:%M')}",
    })

pendientes = sum(1 for p in partidos if p["gh"] is None)
print(f"Partidos: {len(partidos)} ({pendientes} pendientes)")
if pendientes:
    print("AVISO: jornada incompleta, el titular puede quedarse corto.")

tabla = get_clasificacion()["standings"][0]["table"]
r = requests.get(f"{FOOTBALL_DATA_BASE}/competitions/{LALIGA_CODE}/scorers",
                 headers={"X-Auth-Token": FOOTBALL_DATA_TOKEN}, timeout=20)
pichichis = [{"nombre": s["player"]["name"], "goles": s.get("goals", 0),
              "equipo": s["team"].get("shortName") or s["team"]["name"],
              "equipo_full": s["team"]["name"]}
             for s in r.json().get("scorers", [])]

cands = titulares.candidatos(JORNADA, partidos, tabla,
                             get_temporada_terminada(), reel._corto)
print("\nCandidatos:")
for f_, t_, c_ in cands[:5]:
    print(f"  {f_:>4}  {t_}")

tit, club = titulares.elegir(JORNADA, cands)
print(f"\nELEGIDO: {tit}   [club: {club}]")
print("Reel:", generar_reel(JORNADA, partidos, tabla, pichichis, titular=tit, club=club))
