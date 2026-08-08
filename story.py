"""
Generador de imagenes verticales 1080x1920 para Instagram Stories.
Reutiliza los colores y estadios del modulo del feed.
IMPORTANTE: Instagram exige JPEG para Stories (no PNG).
"""

import unicodedata
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from equipos import get_equipo
from estadios import ESTADIOS

ANCHO = 1080
ALTO = 1920
CARPETA_FUENTES = Path("fuentes")
CARPETA_SALIDA = Path("imagenes_generadas")

FONDO = (245, 246, 248)
BLANCO = (255, 255, 255)
NEGRO = (20, 22, 26)
GRIS_MEDIO = (120, 125, 135)
ACENTO = (212, 175, 55)

# Zona segura: Instagram tapa arriba y abajo con su interfaz
SAFE_TOP = 300
SAFE_BOTTOM = ALTO - 300

CARD_TOP = 620
CARD_BOTTOM = 1400
CARD_ANCHO = 460


def _cargar_fuente(nombre, tamano):
    return ImageFont.truetype(str(CARPETA_FUENTES / nombre), tamano)


def _hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _texto(draw, texto, x, y, fuente, color, anchor="mm"):
    draw.text((x, y), texto, font=fuente, fill=color, anchor=anchor)


def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def _get_estadio(nombre):
    objetivo = _sin_tildes(nombre).lower()
    for clave, est in ESTADIOS.items():
        if _sin_tildes(clave).lower() == objetivo:
            return est
    return ""


def _formatear_fecha(utc_str):
    meses = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]
    f = datetime.fromisoformat(utc_str.replace("Z", "+00:00")) + timedelta(hours=2)
    return f"{f.day} {meses[f.month-1]}  -  {f.strftime('%H:%M')}"


def _ajustar_fuente(texto, archivo, smax, smin, max_ancho, draw):
    size = smax
    while size > smin:
        fuente = _cargar_fuente(archivo, size)
        bbox = draw.textbbox((0, 0), texto, font=fuente)
        if (bbox[2] - bbox[0]) <= max_ancho:
            return fuente
        size -= 3
    return _cargar_fuente(archivo, smin)


def _tarjeta(draw, x_izq, color_fondo, color_texto, nombre, goles, f_goles, es_ganador):
    x_der = x_izq + CARD_ANCHO
    cx = x_izq + CARD_ANCHO // 2
    draw.rectangle([x_izq, CARD_TOP, x_der, CARD_BOTTOM], fill=color_fondo)
    if es_ganador:
        draw.rectangle([x_izq, CARD_TOP, x_der, CARD_TOP + 14], fill=ACENTO)
    fn = _ajustar_fuente(nombre.upper(), "BebasNeue-Regular.ttf", 95, 40, CARD_ANCHO - 50, draw)
    _texto(draw, nombre.upper(), cx, CARD_TOP + 230, fn, color_texto)
    _texto(draw, str(goles), cx, CARD_BOTTOM - 230, f_goles, color_texto)


def generar_story_resultado(partido):
    """Genera la Story vertical 1080x1920 en JPEG. Devuelve la ruta."""
    home = partido["home"]
    away = partido["away"]
    gh = partido["goles_home"]
    ga = partido["goles_away"]
    jornada = partido.get("jornada", "")
    fecha_txt = _formatear_fecha(partido["fecha"]) if partido.get("fecha") else ""
    estadio = _get_estadio(home["full"])

    eh = get_equipo(home["full"])
    ea = get_equipo(away["full"])
    gana_h = gh > ga
    gana_a = ga > gh

    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    draw = ImageDraw.Draw(img)

    f_goles = _cargar_fuente("BebasNeue-Regular.ttf", 260)
    f_badge = _cargar_fuente("Montserrat-Bold.ttf", 34)
    f_sub = _cargar_fuente("Montserrat-SemiBold.ttf", 30)
    f_vs = _cargar_fuente("BebasNeue-Regular.ttf", 100)
    f_big = _cargar_fuente("Montserrat-Bold.ttf", 36)
    f_small = _cargar_fuente("Montserrat-Regular.ttf", 28)

    # Badge FINAL
    bw, bh = 190, 66
    bx = (ANCHO - bw) // 2
    by = 420
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=33, fill=NEGRO)
    _texto(draw, "FINAL", ANCHO // 2, by + bh // 2, f_badge, BLANCO)

    jt = f"JORNADA {jornada}  -  LALIGA" if jornada else "LALIGA"
    _texto(draw, jt, ANCHO // 2, 540, f_sub, GRIS_MEDIO)

    _tarjeta(draw, 0, _hex_a_rgb(eh["color"]), _hex_a_rgb(eh["texto"]),
             home["name"], gh, f_goles, gana_h)
    _tarjeta(draw, ANCHO - CARD_ANCHO, _hex_a_rgb(ea["color"]), _hex_a_rgb(ea["texto"]),
             away["name"], ga, f_goles, gana_a)

    _texto(draw, "VS", ANCHO // 2, (CARD_TOP + CARD_BOTTOM) // 2, f_vs, NEGRO)

    y = 1480
    if estadio:
        _texto(draw, estadio.upper(), ANCHO // 2, y, f_sub, GRIS_MEDIO)
        y += 50
    _texto(draw, fecha_txt, ANCHO // 2, y, f_small, GRIS_MEDIO)
    _texto(draw, "@autogoal.es", ANCHO // 2, 1600, f_big, NEGRO)

    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / f"story_{partido['id']}.jpg"
    img.save(ruta, "JPEG", quality=92)
    return str(ruta)
