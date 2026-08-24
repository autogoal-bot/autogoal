from api_client import get_clasificacion
from story import generar_story_resultado

tabla = get_clasificacion()["standings"][0]["table"]

print("Clasificacion actual:")
for f in tabla:
    print(f"  {f['position']:>2}  {f['team']['name'][:24]:<24} {f['points']:>2} pts")

casos = [
    ("ZONA_TOP", "FC Barcelona", "Barça", "Real Madrid CF", "Real Madrid"),
    ("ZONA_MEDIA", "CA Osasuna", "Osasuna", "Levante UD", "Levante"),
]

for cid, fh, nh, fa, na in casos:
    p = {
        "id": cid, "fecha": "2026-08-24T19:30:00Z", "jornada": 2,
        "home": {"full": fh, "name": nh},
        "away": {"full": fa, "name": na},
        "goles_home": 0, "goles_away": 0,
        "goleadores_home": [], "goleadores_away": [],
    }
    print("Generada:", generar_story_resultado(p, tabla))
