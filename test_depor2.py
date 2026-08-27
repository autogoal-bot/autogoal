from api_client import get_clasificacion
from story import generar_story_resultado
from imagen import generar_imagen_resultado

tabla = get_clasificacion()["standings"][0]["table"]
p = {
    "id": "DEPOR2", "fecha": "2026-08-24T19:30:00Z", "jornada": 2,
    "home": {"full": "Málaga CF", "name": "Málaga"},
    "away": {"full": "RC Deportivo La Coruña", "name": "Deportivo de La Coruña"},
    "goles_home": 1, "goles_away": 1,
    "goleadores_home": [{"nombre": "Chupete", "minuto": "34'"}],
    "goleadores_away": [{"nombre": "Pierre-Emerick Aubameyang", "minuto": "21'"}],
}
print("Story:", generar_story_resultado(p, tabla))
print("Feed :", generar_imagen_resultado(p, tabla))
