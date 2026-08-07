"""
Autogoal - orquestador principal.

Flujo:
1. Consulta partidos de hoy en LaLiga
2. Filtra los que terminaron recientemente
3. Descarta los que ya publicamos (registro en publicados.json)
4. Para cada partido nuevo: genera imagen + publica en Instagram
5. Actualiza publicados.json
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from api_client import get_partidos_por_rango
from partidos import filtrar_terminados, termino_hace_menos_de
from imagen import generar_imagen_resultado
from publicar import publicar_en_instagram
from equipos import get_equipo


ARCHIVO_PUBLICADOS = Path("publicados.json")
VENTANA_HORAS = 3

# Hashtags fijos que van en todos los posts
HASHTAGS_FIJOS = ["LaLiga", "futbol", "futbolespanol", "resultados", "EASPORTSFC", "DAZN"]


def cargar_publicados():
    if not ARCHIVO_PUBLICADOS.exists():
        return set()
    with open(ARCHIVO_PUBLICADOS, "r", encoding="utf-8") as f:
        datos = json.load(f)
    return set(datos.get("ids", []))


def guardar_publicados(ids_publicados):
    with open(ARCHIVO_PUBLICADOS, "w", encoding="utf-8") as f:
        json.dump({"ids": sorted(ids_publicados)}, f, indent=2)


def construir_caption(partido):
    home = partido["home"]["name"]
    away = partido["away"]["name"]
    gh = partido["goles_home"]
    ga = partido["goles_away"]
    jornada = partido.get("jornada", "")

    # Hashtags de los equipos (populares, sin tildes)
    tag_home = get_equipo(partido["home"]["full"])["hashtag"]
    tag_away = get_equipo(partido["away"]["full"])["hashtag"]

    # Construir lista de hashtags: liga + equipos + fijos + jornada
    tags = ["LaLiga", tag_home, tag_away, "futbol", "futbolespanol",
            "resultados", f"jornada{jornada}", "EASPORTSFC", "DAZN"]
    hashtags = " ".join(f"#{t}" for t in tags)

    return (
        f"{home} {gh}-{ga} {away}\n\n"
        f"Jornada {jornada} - LaLiga\n\n"
        f"{hashtags}"
    )


def procesar_partido(partido, ids_publicados):
    partido_id = partido["id"]
    home = partido["home"]["name"]
    away = partido["away"]["name"]

    print(f"\n--- Procesando: {home} vs {away} (ID: {partido_id}) ---")

    try:
        ruta_imagen = generar_imagen_resultado(partido)
        print(f"    Imagen generada: {ruta_imagen}")

        caption = construir_caption(partido)
        publicar_en_instagram(ruta_imagen, caption)

        ids_publicados.add(partido_id)
        guardar_publicados(ids_publicados)
        print(f"    Registrado en publicados.json")
        return True

    except Exception as e:
        print(f"    ERROR procesando partido {partido_id}: {e}")
        return False


def main():
    print("=" * 60)
    print(f"AUTOGOAL - Ejecucion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    ids_publicados = cargar_publicados()
    print(f"Partidos ya publicados historicamente: {len(ids_publicados)}")

    hoy = datetime.now().date()
    ayer = hoy - timedelta(days=1)
    fecha_desde = ayer.strftime("%Y-%m-%d")
    fecha_hasta = hoy.strftime("%Y-%m-%d")

    print(f"\nConsultando LaLiga entre {fecha_desde} y {fecha_hasta}...")

    fixtures = get_partidos_por_rango(fecha_desde, fecha_hasta)
    print(f"Total partidos en el rango: {len(fixtures)}")

    terminados = filtrar_terminados(fixtures)
    print(f"Partidos ya terminados: {len(terminados)}")

    ventana_min = VENTANA_HORAS * 60
    recien_terminados = [
        p for p in terminados if termino_hace_menos_de(p, ventana_min)
    ]
    print(f"Terminados en las ultimas {VENTANA_HORAS}h: {len(recien_terminados)}")

    pendientes = [p for p in recien_terminados if p["id"] not in ids_publicados]
    print(f"Pendientes de publicar: {len(pendientes)}")

    if not pendientes:
        print("\nNada que publicar. Fin.")
        return

    print(f"\n{'=' * 60}")
    print(f"PUBLICANDO {len(pendientes)} PARTIDOS")
    print(f"{'=' * 60}")

    exitos = 0
    fallos = 0
    for partido in pendientes:
        if procesar_partido(partido, ids_publicados):
            exitos += 1
        else:
            fallos += 1

    print(f"\n{'=' * 60}")
    print(f"RESUMEN: {exitos} publicados, {fallos} fallidos")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
