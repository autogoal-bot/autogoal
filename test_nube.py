"""
Prueba de humo para la NUBE. Archivo independiente, no toca produccion.
Inyecta un partido falso "recien terminado" y lo pasa por la maquinaria real
(procesar_partido de main.py): feed + Story + registro en publicados.json.

Objetivo: lanzar el workflow DOS veces y verificar que la 2a NO republica.
"""

from datetime import datetime, timezone

from main import cargar_publicados, procesar_partido

# ID muy alto para no chocar jamas con un partido real de football-data.org
PARTIDO_TEST = {
    "id": 999000001,
    "fecha": datetime.now(timezone.utc).isoformat(),
    "jornada": 99,
    "home": {"name": "Athletic", "full": "Athletic Club", "tla": "ATH"},
    "away": {"name": "Getafe", "full": "Getafe CF", "tla": "GET"},
    "goles_home": 3,
    "goles_away": 1,
}


def main():
    print("=" * 60)
    print("PRUEBA DE NUBE - partido falso recien terminado")
    print("=" * 60)

    feed_ids, story_ids = cargar_publicados()
    pid = PARTIDO_TEST["id"]

    ya_feed = pid in feed_ids
    ya_story = pid in story_ids
    print(f"Estado previo -> feed: {ya_feed} | story: {ya_story}")

    if ya_feed and ya_story:
        print("\n>>> El partido de prueba YA estaba publicado por completo.")
        print(">>> ANTI-DUPLICADOS OK: no se republica nada.")
        return

    print("\nProcesando partido de prueba...")
    resultado = procesar_partido(PARTIDO_TEST, feed_ids, story_ids)
    print(f"\nResultado: {resultado}")


if __name__ == "__main__":
    main()
