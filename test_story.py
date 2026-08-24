from api_client import get_clasificacion
from story import generar_story_resultado

tabla = get_clasificacion()["standings"][0]["table"]


def buscar(frag):
    for fila in tabla:
        if frag.lower() in fila["team"]["name"].lower():
            return fila["team"]
    raise SystemExit(f"No encuentro '{frag}' en la clasificacion")

th = buscar("elche")
ta = buscar("barcelona")

goles_barca = [
    {"nombre": "Raphinha", "minuto": "14'"},
    {"nombre": "Karim Adeyemi", "minuto": "45'+3'"},
    {"nombre": "Raphinha", "minuto": "67'"},
    {"nombre": "Fermin Lopez", "minuto": "71'"},
    {"nombre": "Fermin Lopez", "minuto": "79'"},
]

base = {
    "fecha": "2026-08-23T19:30:00Z",
    "jornada": 2,
    "home": {"full": th["name"], "name": th.get("shortName") or th["name"]},
    "away": {"full": ta["name"], "name": "Barca"},
}

# Caso A: 5 goleadores
a = dict(base, id="TEST_5GOLES", goles_home=0, goles_away=5,
         goleadores_home=[], goleadores_away=goles_barca)

# Caso B: 1 goleador (para ver el centrado con poco contenido)
b = dict(base, id="TEST_1GOL", goles_home=0, goles_away=1,
         goleadores_home=[], goleadores_away=goles_barca[:1])

for p in (a, b):
    print("Generada:", generar_story_resultado(p, tabla))
