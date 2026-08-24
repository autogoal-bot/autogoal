from api_client import get_clasificacion
from story import generar_story_resultado
from imagen import generar_imagen_resultado

tabla = get_clasificacion()["standings"][0]["table"]

p = {
    "id": "FINAL_OSASUNA", "fecha": "2026-08-24T19:30:00Z", "jornada": 2,
    "home": {"full": "CA Osasuna", "name": "Osasuna"},
    "away": {"full": "Levante UD", "name": "Levante"},
    "goles_home": 0, "goles_away": 0,
    "goleadores_home": [], "goleadores_away": [],
}

print("Story:", generar_story_resultado(p, tabla))
print("Feed :", generar_imagen_resultado(p, tabla))
