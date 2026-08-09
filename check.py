"""
Chequeo de salud de Autogoal. NO publica nada.
Verifica los 6 puntos que pueden tumbar el bot.
Sale con codigo 1 si algo falla (GitHub lo marca en rojo y manda email).
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

resultados = []


def check(nombre, funcion):
    try:
        detalle = funcion()
        resultados.append((True, nombre, detalle))
    except Exception as e:
        resultados.append((False, nombre, str(e)))


def c_credenciales():
    from config import (FOOTBALL_DATA_TOKEN, PAGE_ACCESS_TOKEN,
                        INSTAGRAM_ACCOUNT_ID, IMGBB_API_KEY)
    faltan = [n for n, v in [
        ("FOOTBALL_DATA_TOKEN", FOOTBALL_DATA_TOKEN),
        ("PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN),
        ("INSTAGRAM_ACCOUNT_ID", INSTAGRAM_ACCOUNT_ID),
        ("IMGBB_API_KEY", IMGBB_API_KEY)] if not v]
    if faltan:
        raise Exception(f"Faltan credenciales: {', '.join(faltan)}")
    return "las 4 presentes"


def c_token():
    import requests
    from config import PAGE_ACCESS_TOKEN as t
    r = requests.get("https://graph.facebook.com/v21.0/debug_token",
                     params={"input_token": t, "access_token": t},
                     timeout=30).json()
    d = r.get("data", {})
    if not d.get("is_valid"):
        raise Exception(f"Token NO valido: {r}")
    if d.get("type") != "PAGE":
        raise Exception(f"Token es {d.get('type')}, deberia ser PAGE")
    if d.get("expires_at") != 0:
        raise Exception(f"Token CADUCA (expires_at={d.get('expires_at')}), no es permanente")
    return "PAGE, permanente, valido"


def c_api_futbol():
    from api_client import get_partidos_por_rango
    hoy = datetime.now().date()
    ayer = hoy - timedelta(days=1)
    p = get_partidos_por_rango(ayer.strftime("%Y-%m-%d"), hoy.strftime("%Y-%m-%d"))
    return f"responde OK ({len(p)} partidos en el rango)"


def c_registros():
    detalles = []
    for archivo in ["publicados.json", "resumenes.json"]:
        ruta = Path(archivo)
        if not ruta.exists():
            detalles.append(f"{archivo}: no existe (se creara solo)")
            continue
        with open(ruta, "r", encoding="utf-8-sig") as f:
            datos = json.load(f)
        detalles.append(f"{archivo}: OK ({len(datos.get('feed', []))} feed)")
    return " | ".join(detalles)


def c_modulos():
    import main, story, imagen, publicar, resumen, resumen_jornada, equipos, estadios
    return "todos importan"


def c_imagen():
    from imagen import generar_imagen_resultado
    from story import generar_story_resultado
    falso = {
        "id": 999999999,
        "fecha": datetime.now().isoformat() + "Z",
        "jornada": 1,
        "home": {"name": "Athletic", "full": "Athletic Club", "tla": "ATH"},
        "away": {"name": "Getafe", "full": "Getafe CF", "tla": "GET"},
        "goles_home": 1,
        "goles_away": 0,
    }
    generar_imagen_resultado(falso)
    generar_story_resultado(falso)
    return "feed y story se generan sin error"


print("=" * 60)
print(f"CHEQUEO AUTOGOAL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

check("1. Credenciales", c_credenciales)
check("2. Token Instagram", c_token)
check("3. API football-data", c_api_futbol)
check("4. Registros JSON", c_registros)
check("5. Modulos Python", c_modulos)
check("6. Generacion de imagenes", c_imagen)

print()
fallos = 0
for ok, nombre, detalle in resultados:
    marca = "OK  " if ok else "FALLO"
    print(f"[{marca}] {nombre}: {detalle}")
    if not ok:
        fallos += 1

print("\n" + "=" * 60)
if fallos:
    print(f"RESULTADO: {fallos} FALLO(S). Revisar arriba.")
    print("=" * 60)
    sys.exit(1)
print("RESULTADO: TODO CORRECTO. El bot esta sano.")
print("=" * 60)
