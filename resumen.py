"""
Generador de imagenes de RESUMEN DE JORNADA.
Dos bloques: resultados (10 partidos) y clasificacion (20 equipos).
Cada uno en feed 1080x1080 y story 1080x1920. Todo JPEG.
NO toca imagen.py ni story.py.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from equipos import get_equipo

ANCHO = 1080
ALTO_FEED = 1080
ALTO_STORY = 1920
CARPETA_FUENTES = Path("fuentes")
CARPETA_SALIDA = Path("imagenes_generadas")

FONDO = (245, 246, 248)
NEGRO = (20, 22, 26)
GRIS_MEDIO = (120, 125, 135)
GRIS_FILA = (236, 238, 242)
GRIS_NEUTRO = (150, 155, 165)
VERDE_UCL = (0, 140, 90)
AZUL_UEL = (40, 110, 200)
ROJO_BAJA = (200, 50, 50)


def _f(nombre, tam):
    return ImageFont.truetype(str(CARPETA_FUENTES / nombre), int(tam))


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _t(draw, texto, x, y, fuente, color, anchor="mm"):
    draw.text((x, y), str(texto), font=fuente, fill=color, anchor=anchor)


def _color_equipo(nombre):
    """Color corporativo. Gris si el equipo no esta en equipos.py
    (p.ej. equipos de temporadas pasadas)."""
    try:
        eq = get_equipo(nombre)
        if eq and eq.get("color"):
            return _hex_rgb(eq["color"])
    except Exception:
        pass
    return GRIS_NEUTRO


def _color_zona(pos):
    if pos <= 4:
        return VERDE_UCL
    if pos <= 6:
        return AZUL_UEL
    if pos >= 18:
        return ROJO_BAJA
    return None


def _cabecera(draw, jornada, subtitulo, y1, y2):
    _t(draw, f"JORNADA {jornada}", ANCHO // 2, y1, _f("BebasNeue-Regular.ttf", 88), NEGRO)
    _t(draw, subtitulo, ANCHO // 2, y2, _f("Montserrat-SemiBold.ttf", 30), GRIS_MEDIO)


def _pie(draw, y):
    _t(draw, "@autogoal.es", ANCHO // 2, y, _f("Montserrat-Bold.ttf", 34), NEGRO)


def _bloque_resultados(draw, partidos, y_top, y_bot):
    n = max(len(partidos), 1)
    h = (y_bot - y_top) / n
    tam = min(38, h * 0.42)
    f_eq = _f("Montserrat-SemiBold.ttf", tam)
    f_gol = _f("BebasNeue-Regular.ttf", tam * 1.6)

    for i, p in enumerate(partidos):
        cy = y_top + h * i + h / 2
        gh, ga = p["goles_home"], p["goles_away"]
        c_home = _color_equipo(p["home"]["full"])
        c_away = _color_equipo(p["away"]["full"])
        pad = h * 0.18

        draw.rectangle([60, int(cy - h/2 + pad), 70, int(cy + h/2 - pad)], fill=c_home)
        draw.rectangle([1010, int(cy - h/2 + pad), 1020, int(cy + h/2 - pad)], fill=c_away)

        col_h = NEGRO if gh >= ga else GRIS_MEDIO
        col_a = NEGRO if ga >= gh else GRIS_MEDIO
        _t(draw, p["home"]["name"].upper(), 470, cy, f_eq, col_h, anchor="rm")
        _t(draw, f"{gh} - {ga}", 540, cy, f_gol, NEGRO)
        _t(draw, p["away"]["name"].upper(), 610, cy, f_eq, col_a, anchor="lm")


def _bloque_clasificacion(draw, tabla, y_top, y_bot):
    n = max(len(tabla), 1)
    h = (y_bot - y_top) / n
    tam = min(30, h * 0.60)
    f_row = _f("Montserrat-SemiBold.ttf", tam)
    f_num = _f("Montserrat-Bold.ttf", tam)
    f_hdr = _f("Montserrat-Bold.ttf", tam * 0.72)

    X_POS, X_EQ, X_PJ, X_DG, X_PTS = 95, 165, 780, 885, 990

    yh = y_top - h * 0.75
    _t(draw, "POS", X_POS, yh, f_hdr, GRIS_MEDIO)
    _t(draw, "EQUIPO", X_EQ, yh, f_hdr, GRIS_MEDIO, anchor="lm")
    _t(draw, "PJ", X_PJ, yh, f_hdr, GRIS_MEDIO)
    _t(draw, "DG", X_DG, yh, f_hdr, GRIS_MEDIO)
    _t(draw, "PTS", X_PTS, yh, f_hdr, GRIS_MEDIO)

    for i, fila in enumerate(tabla):
        cy = y_top + h * i + h / 2
        y0, y1 = int(cy - h/2), int(cy + h/2)
        if i % 2 == 0:
            draw.rectangle([50, y0, 1030, y1], fill=GRIS_FILA)

        pos = fila["position"]
        equipo = fila["team"].get("shortName") or fila["team"]["name"]
        zona = _color_zona(pos)
        if zona:
            draw.rectangle([50, y0, 58, y1], fill=zona)

        pad = h * 0.18
        draw.rectangle([128, int(y0 + pad), 136, int(y1 - pad)],
                       fill=_color_equipo(fila["team"]["name"]))

        dg = fila["goalDifference"]
        dg_txt = f"+{dg}" if dg > 0 else str(dg)

        _t(draw, pos, X_POS, cy, f_row, GRIS_MEDIO)
        _t(draw, equipo, X_EQ, cy, f_row, NEGRO, anchor="lm")
        _t(draw, fila["playedGames"], X_PJ, cy, f_row, GRIS_MEDIO)
        _t(draw, dg_txt, X_DG, cy, f_row, GRIS_MEDIO)
        _t(draw, fila["points"], X_PTS, cy, f_num, NEGRO)


def _lienzo(alto):
    img = Image.new("RGB", (ANCHO, alto), FONDO)
    return img, ImageDraw.Draw(img)


def _guardar(img, nombre):
    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / nombre
    img.save(ruta, "JPEG", quality=92)
    return str(ruta)


def generar_resultados_feed(partidos, jornada):
    img, d = _lienzo(ALTO_FEED)
    _cabecera(d, jornada, "RESULTADOS  -  LALIGA", 105, 175)
    _bloque_resultados(d, partidos, 240, 990)
    _pie(d, 1035)
    return _guardar(img, f"resumen_res_j{jornada}.jpg")


def generar_clasificacion_feed(tabla, jornada):
    img, d = _lienzo(ALTO_FEED)
    _cabecera(d, jornada, "CLASIFICACION  -  LALIGA", 90, 155)
    _bloque_clasificacion(d, tabla, 245, 1010)
    _pie(d, 1048)
    return _guardar(img, f"resumen_cla_j{jornada}.jpg")


def generar_resultados_story(partidos, jornada):
    img, d = _lienzo(ALTO_STORY)
    _cabecera(d, jornada, "RESULTADOS  -  LALIGA", 420, 500)
    _bloque_resultados(d, partidos, 600, 1450)
    _pie(d, 1540)
    return _guardar(img, f"story_res_j{jornada}.jpg")


def generar_clasificacion_story(tabla, jornada):
    img, d = _lienzo(ALTO_STORY)
    _cabecera(d, jornada, "CLASIFICACION  -  LALIGA", 360, 435)
    _bloque_clasificacion(d, tabla, 520, 1500)
    _pie(d, 1585)
    return _guardar(img, f"story_cla_j{jornada}.jpg")
