"""
Prueba de humo FINAL para la nube. Verifica la cadena completa de
publicacion (ImgBB + Instagram) con el token que hay AHORA en el Secret.
Se borra despues de la prueba.
"""

from datetime import datetime, timezone
from main import cargar_publicados, procesar_partido

PARTIDO_TEST = {
    "id": 999000002,
    "fecha": datetime.now(timezone.utc).isoformat(),
    "jornada": 99,
    "home": {"name": "Athletic", "full": "Athletic Club", "tla": "ATH"},
    "away": {"name": "Getafe", "full": "Getafe CF", "tla": "GET"},
    "goles_home": 2,
    "goles_away": 0,
}


def main():
    print("=" * 60)
    print("PRUEBA FINAL DE NUBE - cadena completa de publicacion")
    print("=" * 60)

    feed_ids, story_ids = cargar_publicados()
    pid = PARTIDO_TEST["id"]
    print(f"Estado previo -> feed: {pid in feed_ids} | story: {pid in story_ids}")

    if pid in feed_ids and pid in story_ids:
        print("\n>>> Ya publicado. ANTI-DUPLICADOS OK.")
        return

    resultado = procesar_partido(PARTIDO_TEST, feed_ids, story_ids)
    print(f"\nResultado: {resultado}")


if __name__ == "__main__":
    main()
