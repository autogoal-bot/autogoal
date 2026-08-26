from api_client import get_partidos_jornada, get_clasificacion
from reel import generar_reel
from datetime import datetime, timedelta

DIAS = ["LUN","MAR","MIE","JUE","VIE","SAB","DOM"]
partidos = []
for m in get_partidos_jornada(1):
    fin = m["status"] == "FINISHED"
    f = datetime.fromisoformat(m["utcDate"].replace("Z","+00:00")) + timedelta(hours=2)
    partidos.append({
        "home_full": m["homeTeam"]["name"], "away_full": m["awayTeam"]["name"],
        "home": m["homeTeam"].get("shortName") or m["homeTeam"]["name"],
        "away": m["awayTeam"].get("shortName") or m["awayTeam"]["name"],
        "gh": m["score"]["fullTime"]["home"] if fin else None,
        "ga": m["score"]["fullTime"]["away"] if fin else None,
        "cuando": f"{DIAS[f.weekday()]} {f.strftime('%H:%M')}",
    })

tabla = get_clasificacion()["standings"][0]["table"]

pich = [
    {"nombre": "Kylian Mbappé", "goles": 3, "equipo": "Real Madrid", "equipo_full": "Real Madrid CF"},
    {"nombre": "Nico Williams", "goles": 3, "equipo": "Athletic", "equipo_full": "Athletic Club"},
    {"nombre": "Julián Alvarez", "goles": 2, "equipo": "Atleti", "equipo_full": "Club Atlético de Madrid"},
    {"nombre": "Álvaro García", "goles": 2, "equipo": "Rayo", "equipo_full": "Rayo Vallecano de Madrid"},
    {"nombre": "Raphinha", "goles": 2, "equipo": "Barça", "equipo_full": "FC Barcelona"},
    {"nombre": "Oihan Sancet", "goles": 1, "equipo": "Athletic", "equipo_full": "Athletic Club"},
    {"nombre": "Antoine Griezmann", "goles": 1, "equipo": "Atleti", "equipo_full": "Club Atlético de Madrid"},
    {"nombre": "Jon Guridi", "goles": 1, "equipo": "Sevilla FC", "equipo_full": "Sevilla FC"},
    {"nombre": "Mariano Díaz", "goles": 1, "equipo": "Alavés", "equipo_full": "Deportivo Alavés"},
    {"nombre": "Fermín López", "goles": 1, "equipo": "Barça", "equipo_full": "FC Barcelona"},
]

print("Reel:", generar_reel(99, partidos, tabla, pich))
