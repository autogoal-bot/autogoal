from api_client import get_clasificacion
from story import generar_story_resultado

tabla = get_clasificacion()["standings"][0]["table"]

# (full para color/estadio, name visible en la tarjeta)
casos = [
    (("RC Deportivo La Coruña", "Deportivo de La Coruña"), ("Málaga CF", "Málaga")),
    (("Real Racing Club de Santander", "Racing de Santander"), ("Elche CF", "Elche")),
    (("Club Atlético de Madrid", "Atlético de Madrid"), ("Getafe CF", "Getafe")),
    (("Real Sociedad de Fútbol", "Real Sociedad"), ("FC Barcelona", "Barça")),
]

for i, ((fh, nh), (fa, na)) in enumerate(casos):
    p = {
        "id": f"NOMBRE_{i}",
        "fecha": "2026-08-24T19:30:00Z",
        "jornada": 2,
        "home": {"full": fh, "name": nh},
        "away": {"full": fa, "name": na},
        "goles_home": 2, "goles_away": 1,
        "goleadores_home": [{"nombre": "Yeremay", "minuto": "34'"}],
        "goleadores_away": [{"nombre": "Larrubia", "minuto": "77'"}],
    }
    print(f"{nh:<24} vs {na:<10} ->", generar_story_resultado(p, tabla))
