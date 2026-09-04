"""
Autogoal - orquestador principal.

Flujo:
1. Consulta partidos de hoy en LaLiga
2. Filtra los que terminaron recientemente
3. Descarta los que ya publicamos (registro en publicados.json)
4. Para cada partido nuevo: feed primero, luego Story (si el feed fue OK)
5. Actualiza publicados.json (dos listas independientes: feed y story)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from api_client import get_partidos_por_rango, get_clasificacion
from partidos import filtrar_terminados, termino_hace_menos_de
from imagen import generar_imagen_resultado
from story import generar_story_resultado
from publicar import publicar_en_instagram, publicar_story
from equipos import get_equipo


ARCHIVO_PUBLICADOS = Path("publicados.json")
VENTANA_HORAS = 3

# Hashtags fijos que van en todos los posts
HASHTAGS_FIJOS = ["LaLiga", "futbol", "futbolespanol", "resultados", "EASPORTSFC", "DAZN"]


def cargar_publicados():
    """
    Devuelve dos sets: (feed_ids, story_ids).
    Compatible con el formato antiguo {"ids": [...]}: si lo encuentra,
    asume que esos IDs tenian feed hecho pero NO story.
    """
    if not ARCHIVO_PUBLICADOS.exists():
        return set(), set()
    with open(ARCHIVO_PUBLICADOS, "r", encoding="utf-8-sig") as f:
        datos = json.load(f)

    # Migracion suave desde el formato viejo
    if "ids" in datos:
        return set(datos.get("ids", [])), set()

    return set(datos.get("feed", [])), set(datos.get("story", []))


def guardar_publicados(feed_ids, story_ids):
    with open(ARCHIVO_PUBLICADOS, "w", encoding="utf-8") as f:
        json.dump(
            {"feed": sorted(feed_ids), "story": sorted(story_ids)},
            f,
            indent=2,
        )


# Marcador leido en la vuelta anterior, por ID de partido.
# Sobrevive entre vueltas porque bucle.py importa main una sola vez.
_LECTURA_ANTERIOR = {}

# Veces que hemos retenido cada partido por desacuerdo con ESPN.
_RETENCIONES = {}

# Tras este numero de vueltas (unos 10 min) publicamos con el dato de
# football-data.org aunque ESPN discrepe. Sin esta valvula, un fallo
# de ESPN bloquearia el partido para siempre y sin avisar.
MAX_RETENCIONES = 5


def marcador_fiable(partido):
    """
    Decide si el marcador es de fiar antes de publicarlo.

    football-data.org puede marcar FINISHED con un marcador que aun
    cambia (goles anulados por VAR). Publicar la primera lectura fue
    lo que saco un Betis 1-1 Real Madrid cuando el real era 1-0.

    Filtro 1: el marcador debe repetirse en dos lecturas seguidas.
    Filtro 2: si ESPN tiene el partido, el total de goles debe cuadrar.
    """
    pid = partido["id"]
    gh = partido["goles_home"]
    ga = partido["goles_away"]
    etq = f"{partido['home']['name']} {gh}-{ga} {partido['away']['name']}"

    anterior = _LECTURA_ANTERIOR.get(pid)
    _LECTURA_ANTERIOR[pid] = (gh, ga)

    if anterior is None:
        print(f"    RETENIDO {etq}: primera lectura, se confirma en 2 min.")
        return False

    if anterior != (gh, ga):
        print(f"    RETENIDO {etq}: cambio desde {anterior[0]}-{anterior[1]}.")
        return False

    if partido.get("espn_ok"):
        eh = len(partido["goleadores_home"])
        ea = len(partido["goleadores_away"])
        if (eh + ea) != (gh + ga):
            n = _RETENCIONES.get(pid, 0) + 1
            _RETENCIONES[pid] = n
            print(f"    {etq}: ESPN cuenta {eh + ea} goles, "
                  f"football-data {gh + ga}. Desacuerdo {n}/{MAX_RETENCIONES}.")
            if n < MAX_RETENCIONES:
                print("    RETENIDO. Se reintenta en 2 min.")
                return False
            print("    LIMITE ALCANZADO. Se publica con football-data.org.")
        if (eh, ea) != (gh, ga):
            print(f"    Aviso: ESPN reparte {eh}-{ea}. Revisar (posible gol en propia).")
    else:
        print(f"    Aviso: ESPN no tiene {etq}. Se publica sin contraste.")

    return True


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


def procesar_partido(partido, feed_ids, story_ids):
    """
    Publica feed primero; si el feed va bien, intenta la Story.
    Marca cada entregable por separado en cuanto sale bien y guarda al momento
    (asi, si algo peta a mitad, no se pierde lo ya logrado).
    Devuelve un string: 'completo', 'solo_feed' o 'fallo'.
    """
    partido_id = partido["id"]
    home = partido["home"]["name"]
    away = partido["away"]["name"]

    falta_feed = partido_id not in feed_ids
    falta_story = partido_id not in story_ids

    print(f"\n--- Procesando: {home} vs {away} (ID: {partido_id}) ---")
    print(f"    Falta feed: {falta_feed} | Falta story: {falta_story}")

    # --- FEED ---
    if falta_feed:
        try:
            try:
                tabla = get_clasificacion()["standings"][0]["table"]
            except Exception as e:
                print(f"    Aviso: no se pudo leer la clasificacion ({e}). Se publica sin ella.")
                tabla = None
            ruta_imagen = generar_imagen_resultado(partido, tabla)
            print(f"    Imagen feed generada: {ruta_imagen}")
            caption = construir_caption(partido)
            publicar_en_instagram(ruta_imagen, caption)
            feed_ids.add(partido_id)
            guardar_publicados(feed_ids, story_ids)
            print(f"    FEED publicado y registrado.")
        except Exception as e:
            print(f"    ERROR en FEED del partido {partido_id}: {e}")
            print(f"    Se aborta este partido; se reintentara en el proximo run.")
            return "fallo"

    # --- STORY (solo si el feed esta OK, sea de ahora o de un run anterior) ---
    if falta_story:
        try:
            try:
                tabla_story = get_clasificacion()["standings"][0]["table"]
            except Exception as e:
                print(f"    Aviso: no se pudo leer la clasificacion para Story ({e}).")
                tabla_story = None

            ruta_story = generar_story_resultado(partido, tabla_story)
            print(f"    Imagen story generada: {ruta_story}")
            publicar_story(ruta_story)
            story_ids.add(partido_id)
            guardar_publicados(feed_ids, story_ids)
            print(f"    STORY publicada y registrada.")
        except Exception as e:
            print(f"    ERROR en STORY del partido {partido_id}: {e}")
            print(f"    El feed quedo publicado; solo se reintentara la Story.")
            return "solo_feed"

    return "completo"


def main():
    print("=" * 60)
    print(f"AUTOGOAL - Ejecucion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    feed_ids, story_ids = cargar_publicados()
    print(f"Feed publicados historicamente: {len(feed_ids)}")
    print(f"Story publicadas historicamente: {len(story_ids)}")

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

    # Pendiente = le falta feed O story
    # Pendiente = le falta feed O story.
    #
    # IMPORTANTE:
    # No limitamos los pendientes a las ultimas 3 horas.
    # Si el bot estuvo apagado, fallo o no tuvo conexion,
    # el partido debe seguir pendiente hasta publicarse.
    pendientes = [
        p for p in terminados
        if p["id"] not in feed_ids or p["id"] not in story_ids
    ]
    print(f"Pendientes de publicar (feed o story): {len(pendientes)}")

    if pendientes:
        print("\nVerificando marcadores...")
        pendientes = [p for p in pendientes if marcador_fiable(p)]
        print(f"Con marcador confirmado: {len(pendientes)}")

    if not pendientes:
        print("\nNada que publicar. Fin.")
        return

    print(f"\n{'=' * 60}")
    print(f"PUBLICANDO {len(pendientes)} PARTIDOS")
    print(f"{'=' * 60}")

    completos = 0
    solo_feed = 0
    fallos = 0
    for partido in pendientes:
        resultado = procesar_partido(partido, feed_ids, story_ids)
        if resultado == "completo":
            completos += 1
        elif resultado == "solo_feed":
            solo_feed += 1
        else:
            fallos += 1

    print(f"\n{'=' * 60}")
    print(f"RESUMEN: {completos} completos, {solo_feed} solo-feed, {fallos} fallidos")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
