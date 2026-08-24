from api_client import get_clasificacion
from story import generar_story_resultado
from imagen import generar_imagen_resultado

tabla = get_clasificacion()["standings"][0]["table"]

p = {
    "id": "TEST_DEPOR",
    "fecha": "2026-08-24T19:30:00Z",
    "jornada": 2,
    "home": {"full": "Málaga CF", "name": "Málaga"},
    "away": {"full": "RC Deportivo La Coruña", "name": "Deportivo de La Coruña"},
    "goles_home": 1,
    "goles_away": 2,
    "goleadores_home": [{"nombre": "Larrubia", "minuto": "23'"}],
    "goleadores_away": [
        {"nombre": "Yeremay Hernández", "minuto": "51'"},
        {"nombre": "Mfulu", "minuto": "88'"},
    ],
}

print("Story:", generar_story_resultado(p, tabla))
print("Feed :", generar_imagen_resultado(p, tabla))
