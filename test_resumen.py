"""Prueba visual del generador de resumen. No publica nada."""
from api_client import get_clasificacion
from resumen import (generar_resultados_feed, generar_clasificacion_feed,
                     generar_resultados_story, generar_clasificacion_story)

J = 1

PARTIDOS = [
    {"home": {"name": "Alaves", "full": "Deportivo Alaves"}, "away": {"name": "Getafe", "full": "Getafe CF"}, "goles_home": 2, "goles_away": 1},
    {"home": {"name": "Sevilla", "full": "Sevilla FC"}, "away": {"name": "Rayo", "full": "Rayo Vallecano"}, "goles_home": 1, "goles_away": 1},
    {"home": {"name": "Espanyol", "full": "RCD Espanyol"}, "away": {"name": "Levante", "full": "Levante UD"}, "goles_home": 3, "goles_away": 0},
    {"home": {"name": "Celta", "full": "RC Celta"}, "away": {"name": "Osasuna", "full": "CA Osasuna"}, "goles_home": 0, "goles_away": 2},
    {"home": {"name": "Barcelona", "full": "FC Barcelona"}, "away": {"name": "Valencia", "full": "Valencia CF"}, "goles_home": 4, "goles_away": 1},
    {"home": {"name": "Real Madrid", "full": "Real Madrid CF"}, "away": {"name": "Betis", "full": "Real Betis"}, "goles_home": 2, "goles_away": 0},
    {"home": {"name": "Athletic", "full": "Athletic Club"}, "away": {"name": "Girona", "full": "Girona FC"}, "goles_home": 1, "goles_away": 0},
    {"home": {"name": "Villarreal", "full": "Villarreal CF"}, "away": {"name": "Mallorca", "full": "RCD Mallorca"}, "goles_home": 2, "goles_away": 2},
    {"home": {"name": "Atletico", "full": "Club Atletico de Madrid"}, "away": {"name": "Malaga", "full": "Malaga CF"}, "goles_home": 3, "goles_away": 1},
    {"home": {"name": "Real Sociedad", "full": "Real Sociedad"}, "away": {"name": "Elche", "full": "Elche CF"}, "goles_home": 1, "goles_away": 2},
]

tabla = get_clasificacion()["standings"][0]["table"]
print("Equipos en tabla:", len(tabla))

print(generar_resultados_feed(PARTIDOS, J))
print(generar_clasificacion_feed(tabla, J))
print(generar_resultados_story(PARTIDOS, J))
print(generar_clasificacion_story(tabla, J))
print("\nHecho. Abre las 4 imagenes en imagenes_generadas/")
