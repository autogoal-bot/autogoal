# -*- coding: utf-8 -*-
"""
metricas.py — Extractor de métricas de @autogoal.es vía Instagram Graph API.

SOLO LECTURA. No publica, no borra, no toca nada del bot.
Genera 3 CSV:
    metricas_posts.csv       -> una fila por publicación (feed, carruseles, reels)
    metricas_seguidores.csv  -> seguidores ganados/perdidos por día (últimos 30 días)
    metricas_stories.csv     -> stories ACTIVAS ahora mismo (ventana de 24h)

Uso:
    python metricas.py
"""

import os
import csv
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------------------

API_VERSION = "v25.0"          # última versión estable (feb 2026)
BASE = f"https://graph.facebook.com/{API_VERSION}"

CSV_POSTS = "metricas_posts.csv"
CSV_SEGUIDORES = "metricas_seguidores.csv"
CSV_STORIES = "metricas_stories.csv"

MAX_PAGINAS = 30               # tope de seguridad en la paginación
PAUSA = 0.4                    # segundos entre llamadas (rate limit)

load_dotenv()
TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# Zona horaria española (necesita el paquete 'tzdata' en Windows)
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Madrid")
except Exception:
    TZ = timezone(timedelta(hours=2))
    print("[AVISO] No se pudo cargar 'Europe/Madrid'. Instala tzdata:")
    print("        pip install tzdata")
    print("        Mientras tanto uso UTC+2 fijo (puede fallar en invierno).\n")

# Métricas por tipo de contenido
METRICAS = {
    "FEED": ["reach", "views", "saved", "shares",
             "total_interactions", "follows", "profile_visits"],
    "REELS": ["reach", "views", "saved", "shares",
              "total_interactions", "follows", "profile_visits",
              "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"],
    "STORY": ["reach", "views", "replies",
              "total_interactions", "follows", "profile_visits"],
}

COLUMNAS_METRICAS = [
    "reach", "views", "saved", "shares", "total_interactions",
    "follows", "profile_visits", "replies",
    "ig_reels_avg_watch_time", "ig_reels_video_view_total_time",
]

DIAS = ["lunes", "martes", "miércoles", "jueves",
        "viernes", "sábado", "domingo"]

metricas_no_soportadas = set()   # para avisar una sola vez al final


# ----------------------------------------------------------------------
# UTILIDADES HTTP
# ----------------------------------------------------------------------

def pedir(url, params, intentos=3):
    """GET con reintentos. Devuelve (json, error_dict|None)."""
    params = dict(params)
    params["access_token"] = TOKEN

    for i in range(intentos):
        try:
            r = requests.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            print(f"   [red] {e} — reintento {i+1}/{intentos}")
            time.sleep(3)
            continue

        if r.status_code == 200:
            time.sleep(PAUSA)
            return r.json(), None

        try:
            err = r.json().get("error", {})
        except Exception:
            err = {"message": r.text[:200]}

        codigo = err.get("code")

        # Rate limit -> esperar y reintentar
        if codigo in (4, 17, 32, 613) or r.status_code == 429:
            espera = 60 * (i + 1)
            print(f"   [rate limit] esperando {espera}s...")
            time.sleep(espera)
            continue

        time.sleep(PAUSA)
        return None, err

    return None, {"message": "Se agotaron los reintentos"}


def token_ok():
    """Comprueba que el token existe y es válido antes de gastar llamadas."""
    if not TOKEN or not IG_ID:
        print("ERROR: faltan PAGE_ACCESS_TOKEN o INSTAGRAM_ACCOUNT_ID en el .env")
        return False

    data, err = pedir(f"{BASE}/{IG_ID}",
                      {"fields": "username,followers_count,media_count"})
    if err:
        print(f"ERROR de token o de cuenta: {err.get('message')}")
        print("  -> Si dice 'Session has expired' o 'Invalid OAuth', "
              "regenera el token con obtener_token.py")
        return False

    print(f"Cuenta: @{data.get('username')}")
    print(f"Seguidores ahora: {data.get('followers_count')}")
    print(f"Publicaciones en el feed: {data.get('media_count')}\n")
    return True


# ----------------------------------------------------------------------
# INSIGHTS
# ----------------------------------------------------------------------

def _extraer_valor(item):
    """Normaliza las 2 formas en que la API devuelve un valor."""
    valores = item.get("values")
    if valores:
        v = valores[0].get("value")
        if isinstance(v, dict):
            return sum(x for x in v.values() if isinstance(x, (int, float)))
        return v
    tv = item.get("total_value")
    if isinstance(tv, dict):
        return tv.get("value")
    return None


def insights_de(media_id, tipo):
    """
    Pide las métricas de un media. Si la API rechaza el lote entero
    (porque alguna métrica no aplica a ese tipo de contenido),
    reintenta métrica a métrica y se queda con las que funcionan.
    """
    lista = METRICAS.get(tipo, METRICAS["FEED"])
    resultado = {}

    data, err = pedir(f"{BASE}/{media_id}/insights",
                      {"metric": ",".join(lista)})

    if data and "data" in data:
        for item in data["data"]:
            resultado[item["name"]] = _extraer_valor(item)
        return resultado

    # Código 10 = "Not enough viewers" (stories con menos de 5 visualizaciones)
    if err and err.get("code") == 10:
        return {"_nota": "menos de 5 visualizaciones"}

    # Plan B: una a una
    for m in lista:
        d, e = pedir(f"{BASE}/{media_id}/insights", {"metric": m})
        if d and d.get("data"):
            resultado[m] = _extraer_valor(d["data"][0])
        else:
            metricas_no_soportadas.add(m)

    return resultado


# ----------------------------------------------------------------------
# 1) PUBLICACIONES DEL FEED + REELS
# ----------------------------------------------------------------------

def descargar_publicaciones():
    campos = ("id,caption,media_type,media_product_type,timestamp,"
              "permalink,like_count,comments_count")
    url = f"{BASE}/{IG_ID}/media"
    params = {"fields": campos, "limit": 50}

    publicaciones = []
    pagina = 0

    while url and pagina < MAX_PAGINAS:
        data, err = pedir(url, params)
        if err:
            print(f"ERROR bajando el listado: {err.get('message')}")
            break

        publicaciones.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        params = {}            # la URL 'next' ya trae todos los parámetros
        pagina += 1

    return publicaciones


def procesar_publicaciones(publicaciones):
    filas = []
    total = len(publicaciones)

    for i, p in enumerate(publicaciones, 1):
        tipo = p.get("media_product_type", "FEED")
        print(f"  [{i}/{total}] {tipo:6s} {p.get('timestamp','')[:10]}")

        ins = insights_de(p["id"], tipo)

        # UTC -> hora española
        ts = datetime.strptime(p["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        local = ts.astimezone(TZ)

        caption = (p.get("caption") or "").replace("\n", " ").replace(";", ",")

        fila = {
            "id": p["id"],
            "fecha": local.strftime("%Y-%m-%d"),
            "hora": local.strftime("%H:%M"),
            "dia_semana": DIAS[local.weekday()],
            "tipo": tipo,
            "formato": p.get("media_type", ""),
            "titular": caption[:70],
            "likes": p.get("like_count", 0),
            "comentarios": p.get("comments_count", 0),
            "permalink": p.get("permalink", ""),
            "nota": ins.get("_nota", ""),
        }
        for m in COLUMNAS_METRICAS:
            fila[m] = ins.get(m, "")

        filas.append(fila)

    return filas


def guardar_posts(filas):
    columnas = (["id", "fecha", "hora", "dia_semana", "tipo", "formato",
                 "titular", "likes", "comentarios"]
                + COLUMNAS_METRICAS
                + ["permalink", "nota"])

    # utf-8-sig + ';' para que Excel en español lo abra bien y con acentos
    with open(CSV_POSTS, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columnas, delimiter=";",
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


# ----------------------------------------------------------------------
# 2) SEGUIDORES DÍA A DÍA (últimos 30 días)
# ----------------------------------------------------------------------

def descargar_seguidores():
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=29)

    filas = []
    for metrica in ("follower_count", "reach"):
        data, err = pedir(f"{BASE}/{IG_ID}/insights", {
            "metric": metrica,
            "period": "day",
            "since": int(desde.timestamp()),
            "until": int(hasta.timestamp()),
        })
        if err:
            print(f"  [aviso] '{metrica}' no disponible: {err.get('message')}")
            continue

        for bloque in data.get("data", []):
            for v in bloque.get("values", []):
                fecha = v.get("end_time", "")[:10]
                filas.append({"fecha": fecha,
                              "metrica": metrica,
                              "valor": v.get("value")})

    if not filas:
        return []

    filas.sort(key=lambda x: (x["fecha"], x["metrica"]))
    with open(CSV_SEGUIDORES, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["fecha", "metrica", "valor"],
                           delimiter=";")
        w.writeheader()
        w.writerows(filas)

    return filas


# ----------------------------------------------------------------------
# 3) STORIES ACTIVAS (solo las de las últimas 24h)
# ----------------------------------------------------------------------

def descargar_stories():
    data, err = pedir(f"{BASE}/{IG_ID}/stories",
                      {"fields": "id,media_type,timestamp,permalink"})
    if err:
        print(f"  [aviso] stories no disponibles: {err.get('message')}")
        return []

    stories = data.get("data", [])
    if not stories:
        print("  No hay stories activas ahora mismo.")
        return []

    filas = []
    for s in stories:
        ins = insights_de(s["id"], "STORY")
        ts = datetime.strptime(s["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        local = ts.astimezone(TZ)

        fila = {
            "id": s["id"],
            "fecha": local.strftime("%Y-%m-%d"),
            "hora": local.strftime("%H:%M"),
            "formato": s.get("media_type", ""),
            "nota": ins.get("_nota", ""),
        }
        for m in ("reach", "views", "replies", "total_interactions",
                  "follows", "profile_visits"):
            fila[m] = ins.get(m, "")
        filas.append(fila)

    columnas = ["id", "fecha", "hora", "formato", "reach", "views", "replies",
                "total_interactions", "follows", "profile_visits", "nota"]

    # Modo 'append': cada ejecución añade, no pisa. Así construimos histórico.
    existe = os.path.exists(CSV_STORIES)
    ids_previos = set()
    if existe:
        with open(CSV_STORIES, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f, delimiter=";"):
                ids_previos.add(r.get("id"))

    nuevas = [f for f in filas if f["id"] not in ids_previos]

    with open(CSV_STORIES, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columnas, delimiter=";",
                           extrasaction="ignore")
        if not existe:
            w.writeheader()
        w.writerows(nuevas)

    return nuevas


# ----------------------------------------------------------------------
# RESUMEN EN PANTALLA
# ----------------------------------------------------------------------

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def resumen(filas):
    if not filas:
        return

    grupos = {}
    for f in filas:
        grupos.setdefault(f["tipo"], []).append(f)

    print("\n" + "=" * 62)
    print("RESUMEN POR TIPO DE CONTENIDO")
    print("=" * 62)

    for tipo, g in sorted(grupos.items()):
        n = len(g)
        alcance = sum(_num(x["reach"]) for x in g)
        guardados = sum(_num(x["saved"]) for x in g)
        seguidores = sum(_num(x["follows"]) for x in g)
        interac = sum(_num(x["total_interactions"]) for x in g)

        plural = "publicación" if n == 1 else "publicaciones"
        print(f"\n{tipo}  ({n} {plural})")
        print(f"  Alcance total ........ {alcance:>10,.0f}")
        print(f"  Alcance medio ........ {alcance/n:>10,.1f}")
        print(f"  Guardados totales .... {guardados:>10,.0f}")
        print(f"  Seguidores captados .. {seguidores:>10,.0f}")
        if alcance > 0:
            print(f"  Interacción / alcance  {100*interac/alcance:>9,.2f} %")
            print(f"  Seguidor / 1000 alc.   {1000*seguidores/alcance:>9,.2f}")

    print("\n" + "=" * 62)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    print("=" * 62)
    print("AUTOGOAL — EXTRACCIÓN DE MÉTRICAS (solo lectura)")
    print("=" * 62 + "\n")

    if not token_ok():
        sys.exit(1)

    print("1/3 Descargando listado de publicaciones...")
    pubs = descargar_publicaciones()
    print(f"    {len(pubs)} publicaciones encontradas.\n")

    if pubs:
        print("2/3 Pidiendo métricas de cada una...")
        filas = procesar_publicaciones(pubs)
        guardar_posts(filas)
        print(f"\n    -> {CSV_POSTS} generado ({len(filas)} filas)")
    else:
        filas = []

    print("\n3/3 Seguidores y alcance por día (últimos 30)...")
    segs = descargar_seguidores()
    if segs:
        print(f"    -> {CSV_SEGUIDORES} generado ({len(segs)} filas)")

    print("\n    Stories activas (ventana de 24h)...")
    st = descargar_stories()
    if st:
        print(f"    -> {CSV_STORIES}: {len(st)} stories nuevas añadidas")

    resumen(filas)

    if metricas_no_soportadas:
        print("Métricas que la API no ha devuelto para algún contenido:")
        print("  " + ", ".join(sorted(metricas_no_soportadas)))
        print("  (normal: no todas aplican a todos los formatos)\n")

    print("Listo. Pásame el CSV y lo analizamos.")


if __name__ == "__main__":
    main()