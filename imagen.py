"""
Generador de imagenes premium para resultados de LaLiga.
Tarjetas laterales de color por equipo sobre fondo claro.
Incluye: ganador resaltado, badge FINAL, estadio en footer.
"""

import unicodedata
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from equipos import get_equipo
from estadios import ESTADIOS

ANCHO = 1080
ALTO = 1080
CARPETA_FUENTES = Path("fuentes")
CARPETA_SALIDA = Path("imagenes_generadas")

FONDO = (245, 246, 248)
BLANCO = (255, 255, 255)
NEGRO = (20, 22, 26)
GRIS_MEDIO = (120, 125, 135)
ACENTO = (212, 175, 55)  # dorado para resaltar al ganador

CARD_TOP = 210
CARD_BOTTOM = 800
CARD_ANCHO = 460


def _cargar_fuente(nombre, tamano):
    return ImageFont.truetype(str(CARPETA_FUENTES / nombre), tamano)


def _hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _texto(draw, texto, x, y, fuente, color, anchor="mm"):
    draw.text((x, y), texto, font=fuente, fill=color, anchor=anchor)


def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def _get_estadio(nombre_equipo):
    objetivo = _sin_tildes(nombre_equipo).lower()
    for clave, estadio in ESTADIOS.items():
        if _sin_tildes(clave).lower() == objetivo:
            return estadio
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


def _partir_nombre(texto, draw, size=90, max_ancho=CARD_ANCHO - 50):
    """
    Devuelve (lineas, fuente) manteniendo el tamano grande.
    Si el nombre no cabe en una linea, lo parte en dos por la palabra
    que mejor equilibre. Solo reduce la fuente como ultimo recurso.
    """
    fuente = _cargar_fuente("BebasNeue-Regular.ttf", size)

    def ancho(t):
        b = draw.textbbox((0, 0), t, font=fuente)
        return b[2] - b[0]

    if ancho(texto) <= max_ancho:
        return [texto], fuente

    palabras = texto.split()
    if len(palabras) > 1:
        # Probar todos los cortes y quedarse con el mas equilibrado que quepa
        mejor = None
        for i in range(1, len(palabras)):
            l1 = " ".join(palabras[:i])
            l2 = " ".join(palabras[i:])
            if ancho(l1) <= max_ancho and ancho(l2) <= max_ancho:
                desviacion = abs(ancho(l1) - ancho(l2))
                if mejor is None or desviacion < mejor[0]:
                    mejor = (desviacion, [l1, l2])
        if mejor:
            return mejor[1], fuente

    # Ultimo recurso: una sola linea con fuente reducida
    return [texto], _ajustar_fuente(texto, "BebasNeue-Regular.ttf", size, 40, max_ancho, draw)


def _mini_clasificacion(draw, x_izq, nombre_equipo, tabla):
    """
    Dibuja 3 filas bajo la tarjeta: el equipo con su predecesor y perseguidor.
    Si no encuentra al equipo en la tabla, no dibuja nada.
    """
    if not tabla:
        return

    idx = None
    objetivo = _sin_tildes(nombre_equipo).lower()
    for i, fila in enumerate(tabla):
        if _sin_tildes(fila["team"]["name"]).lower() == objetivo:
            idx = i
            break
    if idx is None:
        return

    ini = max(0, min(idx - 1, len(tabla) - 3))
    trio = tabla[ini:ini + 3]

    f_row = _cargar_fuente("Montserrat-Regular.ttf", 21)
    f_hit = _cargar_fuente("Montserrat-Bold.ttf", 22)

    y0 = CARD_BOTTOM + 22
    alto_fila = 32
    x_pos = x_izq + 34
    x_nom = x_izq + 78
    x_pts = x_izq + CARD_ANCHO - 34

    for i, fila in enumerate(trio):
        cy = y0 + alto_fila * i + alto_fila // 2
        es_este = (ini + i) == idx
        fuente = f_hit if es_este else f_row
        color = NEGRO if es_este else GRIS_MEDIO

        if es_este:
            draw.rectangle([x_izq + 14, cy - 14, x_izq + 20, cy + 14], fill=ACENTO)

        nombre = fila["team"].get("shortName") or fila["team"]["name"]
        if len(nombre) > 16:
            nombre = nombre[:15] + "."

        _texto(draw, str(fila["position"]), x_pos, cy, fuente, color)
        _texto(draw, nombre, x_nom, cy, fuente, color, anchor="lm")
        _texto(draw, str(fila["points"]), x_pts, cy, fuente, color, anchor="rm")


def _dibujar_tarjeta(draw, x_izq, color_fondo, color_texto, nombre, goles, fuentes, es_ganador):
    x_der = x_izq + CARD_ANCHO
    cx = x_izq + CARD_ANCHO // 2
    draw.rectangle([x_izq, CARD_TOP, x_der, CARD_BOTTOM], fill=color_fondo)
    # Linea de acento dorada arriba si es el ganador
    if es_ganador:
        draw.rectangle([x_izq, CARD_TOP, x_der, CARD_TOP + 12], fill=ACENTO)
    lineas, fn = _partir_nombre(nombre.upper(), draw)
    if len(lineas) == 1:
        _texto(draw, lineas[0], cx, CARD_TOP + 200, fn, color_texto)
    else:
        _texto(draw, lineas[0], cx, CARD_TOP + 158, fn, color_texto)
        _texto(draw, lineas[1], cx, CARD_TOP + 252, fn, color_texto)
    _texto(draw, str(goles), cx, CARD_BOTTOM - 190, fuentes["goles"], color_texto)


def generar_imagen_resultado(partido, tabla=None):
    home = partido["home"]
    away = partido["away"]
    goles_home = partido["goles_home"]
    goles_away = partido["goles_away"]
    jornada = partido.get("jornada", "")
    fecha_txt = _formatear_fecha(partido["fecha"]) if partido.get("fecha") else ""
    estadio = _get_estadio(home["full"])

    eh = get_equipo(home["full"])
    ea = get_equipo(away["full"])

    gana_home = goles_home > goles_away
    gana_away = goles_away > goles_home

    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    draw = ImageDraw.Draw(img)

    fuentes = {"goles": _cargar_fuente("BebasNeue-Regular.ttf", 240)}
    f_badge = _cargar_fuente("Montserrat-Bold.ttf", 28)
    f_sub = _cargar_fuente("Montserrat-SemiBold.ttf", 26)
    f_vs = _cargar_fuente("BebasNeue-Regular.ttf", 90)
    f_fbig = _cargar_fuente("Montserrat-Bold.ttf", 30)
    f_fsmall = _cargar_fuente("Montserrat-Regular.ttf", 24)
    f_estadio = _cargar_fuente("Montserrat-SemiBold.ttf", 24)

    # ── BADGE FINAL (pildora redondeada) ──
    badge_w, badge_h = 160, 54
    bx0 = (ANCHO - badge_w) // 2
    by0 = 55
    draw.rounded_rectangle([bx0, by0, bx0 + badge_w, by0 + badge_h],
                           radius=27, fill=NEGRO)
    _texto(draw, "FINAL", ANCHO // 2, by0 + badge_h // 2, f_badge, BLANCO)

    jt = f"JORNADA {jornada}  -  LALIGA" if jornada else "LALIGA"
    _texto(draw, jt, ANCHO // 2, 160, f_sub, GRIS_MEDIO)

    # ── TARJETAS ──
    _dibujar_tarjeta(draw, 0, _hex_a_rgb(eh["color"]), _hex_a_rgb(eh["texto"]),
                     home["name"], goles_home, fuentes, gana_home)
    _dibujar_tarjeta(draw, ANCHO - CARD_ANCHO, _hex_a_rgb(ea["color"]), _hex_a_rgb(ea["texto"]),
                     away["name"], goles_away, fuentes, gana_away)

    _mini_clasificacion(draw, 0, home["full"], tabla)
    _mini_clasificacion(draw, ANCHO - CARD_ANCHO, away["full"], tabla)

    _texto(draw, "VS", ANCHO // 2, (CARD_TOP + CARD_BOTTOM) // 2, f_vs, NEGRO)

    # ── FOOTER ──
    y = 935
    if estadio:
        _texto(draw, estadio.upper(), ANCHO // 2, y, f_estadio, GRIS_MEDIO)
        y += 40
    _texto(draw, fecha_txt, ANCHO // 2, y, f_fsmall, GRIS_MEDIO)
    _texto(draw, "@autogoal.es", ANCHO // 2, 1035, f_fbig, NEGRO)

    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / f"partido_{partido['id']}.jpg"
    img.save(ruta, "JPEG", quality=92)
    return str(ruta)
