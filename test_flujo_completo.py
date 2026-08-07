from imagen import generar_imagen_resultado
from publicar import publicar_en_instagram

partido = {
    "id": 777001,
    "fecha": "2026-08-15T17:30:00Z",
    "estado": "FINISHED",
    "jornada": 1,
    "home": {"name": "Alaves", "full": "Deportivo Alaves", "tla": "ALA"},
    "away": {"name": "Getafe", "full": "Getafe CF", "tla": "GET"},
    "goles_home": 2,
    "goles_away": 1,
}

print("1. Generando imagen...")
ruta = generar_imagen_resultado(partido)
print("   OK:", ruta)

caption = "Alaves 2-1 Getafe\n\nJornada 1 - LaLiga\n\n#LaLiga #Futbol #Autogoal"
print("2. Publicando en Instagram...")
publicar_en_instagram(ruta, caption)
print("   OK - Publicado")
