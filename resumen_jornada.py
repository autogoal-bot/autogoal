"""
Resumen de jornada: detecta jornada cerrada y publica
carrusel (resultados + clasificacion) + 2 Stories.

INDEPENDIENTE: no se ejecuta desde main.py ni desde bot.yml.
Se lanza a mano: python resumen_jornada.py
Registro propio en resumenes.json (no toca publicados.json).
"""

import json
import sys
from pathlib import Path

from api_client import get_clasificacion, get_partidos_jornada
from resumen import (generar_resultados_feed, generar_clasificacion_feed,
                     generar_resultados_story, generar_clasificacion_story)
from publicar import publicar_carrusel, publicar_story

ARCHIVO_RESUMENES = Path("resumenes.json")
ESTADO_TERMINADO = "FINISHED"


def cargar_resumenes():
    if not ARCHIVO_RESUMENES.exists():
        return set(), set()
    with open(ARCHIVO_RESUMENES, "r", encoding="utf-8") as f:
        datos = json.load(f)
    return set(datos.get("feed", [])), set(datos.get("story", []))


def guardar_resumenes(feed_j, story_j):
    with open(ARCHIVO_RESUMENES, "w", encoding="utf-8") as f:
        json.dump({"feed": sorted(feed_j), "story": sorted(story_j)}, f, indent=2)


def normalizar(partido):
    """Convierte el JSON de football-data.org al formato que usa resumen.py."""
    ft = partido["score"]["fullTime"]
    h, a = partido["homeTeam"], partido["awayTeam"]
    return {
        "home": {"name": h.get("shortName") or h["name"], "full": h["name"]},
        "away": {"name": a.get("shortName") or a["name"], "full": a["name"]},
        "goles_home": ft["home"],
        "goles_away": ft["away"],
    }


def jornada_completa(numero):
    """Devuelve (esta_completa, lista_partidos_normalizados)."""
    bruto = get_partidos_jornada(numero)
    if not bruto:
        return False, []
    completa = all(p["status"] == ESTADO_TERMINADO for p in bruto)
    return completa, [normalizar(p) for p in bruto]


def construir_caption(jornada, partidos):
    lineas = [f"JORNADA {jornada} - LaLiga\n"]
    for p in partidos:
        lineas.append(f"{p['home']['name']} {p['goles_home']}-{p['goles_away']} {p['away']['name']}")
    tags = ["LaLiga", "futbol", "futbolespanol", "resultados",
            "clasificacion", f"jornada{jornada}", "EASPORTSFC", "DAZN"]
    lineas.append("\nClasificacion completa en la segunda imagen ->")
    lineas.append("\n" + " ".join(f"#{t}" for t in tags))
    return "\n".join(lineas)


def procesar(jornada, forzar=False):
    feed_j, story_j = cargar_resumenes()

    if not forzar and jornada in feed_j and jornada in story_j:
        print(f">>> Jornada {jornada} ya publicada por completo. Nada que hacer.")
        return

    completa, partidos = jornada_completa(jornada)
    print(f"Jornada {jornada}: {len(partidos)} partidos | completa: {completa}")

    if not completa:
        print(">>> La jornada aun no ha terminado. Se reintentara mas tarde.")
        return

    tabla = get_clasificacion()["standings"][0]["table"]

    # --- FEED (carrusel de 2 slides) ---
    if forzar or jornada not in feed_j:
        try:
            slide1 = generar_resultados_feed(partidos, jornada)
            slide2 = generar_clasificacion_feed(tabla, jornada)
            publicar_carrusel([slide1, slide2], construir_caption(jornada, partidos))
            feed_j.add(jornada)
            guardar_resumenes(feed_j, story_j)
            print("    FEED (carrusel) publicado y registrado.")
        except Exception as e:
            print(f"    ERROR en FEED de la jornada {jornada}: {e}")
            return

    # --- STORIES (2 seguidas) ---
    if forzar or jornada not in story_j:
        try:
            st1 = generar_resultados_story(partidos, jornada)
            publicar_story(st1)
            st2 = generar_clasificacion_story(tabla, jornada)
            publicar_story(st2)
            story_j.add(jornada)
            guardar_resumenes(feed_j, story_j)
            print("    STORIES publicadas y registradas.")
        except Exception as e:
            print(f"    ERROR en STORIES de la jornada {jornada}: {e}")
            return

    print(f"\n>>> Resumen de la jornada {jornada} COMPLETO.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python resumen_jornada.py <numero_jornada> [--forzar]")
        print("Ejemplo: python resumen_jornada.py 1")
        sys.exit(1)
    numero = int(sys.argv[1])
    forzar = "--forzar" in sys.argv
    procesar(numero, forzar)
