"""
Generador de imagenes verticales 1080x1920 para Instagram Stories.

Mismo lenguaje visual que el feed (imagen.py), escalado x1.24 y con
el bloque de contenido CENTRADO verticalmente: se calcula su altura
real antes de dibujar, asi nunca queda hueco muerto abajo.

Modulo autonomo: no importa nada interno de imagen.py.
IMPORTANTE: Instagram exige JPEG para Stories (no PNG).
"""

import unicodedata
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from equipos import get_equipo
from estadios import ESTADIOS
import clasificacion

ANCHO = 1080
ALTO = 1920
CARPETA_FUENTES = Path("fuentes")
CARPETA_SALIDA = Path("imagenes_generadas")

FONDO = (245, 246, 248)
BLANCO = (255, 255, 255)
NEGRO = (20, 22, 26)
GRIS_MEDIO = (120, 125, 135)
ACENTO = (212, 175, 55)
GRIS_SUAVE = (188, 193, 203)
GRIS_OSCURO = (62, 68, 80)

CARD_ANCHO = 460
CARD_ALTO = 470

# Centro visual del bloque. Algo por encima del centro geometrico (960)
# porque la barra de respuesta de Instagram ocupa mas espacio abajo.
CENTRO_Y = 940

# Alturas y separaciones del bloque, en px.
H_BADGE = 68
GAP_BADGE = 30
H_JORNADA = 40
H_ESTADIO = 38
H_FECHA = 38
GAP_CABECERA = 30
GAP_TARJETA = 24
H_FILA_GOLEADOR = 36
GAP_GOLEADORES = 22
H_FILA_CLASIF = 48
GAP_CLASIF = 70
H_PIE = 44


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
    meses = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
             "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
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



# Nombres que queremos partir por un punto concreto, no por el mas equilibrado.
CORTES_FORZADOS = {
    "RACING DE SANTANDER": ["RACING", "DE SANTANDER"],
    "REAL RACING CLUB": ["REAL RACING", "CLUB"],
    "REAL SOCIEDAD DE FUTBOL": ["REAL", "SOCIEDAD"],
    "REAL SOCIEDAD DE FÚTBOL": ["REAL", "SOCIEDAD"],
    "RAYO VALLECANO DE MADRID": ["RAYO", "VALLECANO"],
    "RCD ESPANYOL DE BARCELONA": ["RCD", "ESPANYOL"],
    "DEPORTIVO DE LA CORUNA": ["DEPORTIVO", "DE LA CORUÑA"],
    "DEPORTIVO DE LA CORUÑA": ["DEPORTIVO", "DE LA CORUÑA"],
    "ATLETICO DE MADRID": ["ATLETICO", "DE MADRID"],
    "ATLÉTICO DE MADRID": ["ATLÉTICO", "DE MADRID"],
}


def _partir_nombre(texto, draw, size=95, max_ancho=CARD_ANCHO - 55):
    """
    Igual que en el feed: mantiene la fuente grande y parte el nombre
    en dos lineas equilibradas si no cabe. Solo reduce como ultimo recurso.
    """
    fuente = _cargar_fuente("BebasNeue-Regular.ttf", size)

    forzado = CORTES_FORZADOS.get(texto.upper())
    if forzado:
        f = _cargar_fuente("BebasNeue-Regular.ttf", size)
        if all(draw.textbbox((0, 0), l, font=f)[2] <= max_ancho for l in forzado):
            return forzado, f


    def ancho(t):
        b = draw.textbbox((0, 0), t, font=fuente)
        return b[2] - b[0]

    if ancho(texto) <= max_ancho:
        return [texto], fuente

    palabras = texto.split()
    if len(palabras) > 1:
        mejor = None
        for i in range(1, len(palabras)):
            l1 = " ".join(palabras[:i])
            l2 = " ".join(palabras[i:])
            if ancho(l1) <= max_ancho and ancho(l2) <= max_ancho:
                desv = abs(ancho(l1) - ancho(l2))
                if mejor is None or desv < mejor[0]:
                    mejor = (desv, [l1, l2])
        if mejor:
            return mejor[1], fuente

    return [texto], _ajustar_fuente(
        texto, "BebasNeue-Regular.ttf", size, 40, max_ancho, draw
    )


def _extraer_tabla(tabla):
    """Acepta la respuesta completa de football-data.org o una lista ya lista."""
    if not tabla:
        return []
    if isinstance(tabla, list):
        return tabla
    if isinstance(tabla, dict):
        standings = tabla.get("standings", [])
        if standings:
            return standings[0].get("table", [])
    return []


def _texto_goleador(g):
    """Normaliza un goleador a texto. NO añade apostrofo: el minuto ya lo trae."""
    if isinstance(g, dict):
        nombre = g.get("nombre") or g.get("name") or g.get("jugador") or ""
        minuto = g.get("minuto") or g.get("minute") or ""
    else:
        nombre = str(g)
        minuto = ""
    return f"{nombre}  {minuto}".strip()


def _mini_clasificacion(draw, x_izq, nombre_equipo, tabla_real, lado, y_inicio):
    """
    Mini clasificacion propia de la Story: mismo diseño que el feed
    pero con fuentes un 40% mayores (27/28 frente a 20/21) y filas de 34px.
    """
    if not tabla_real:
        return

    objetivo = _sin_tildes(nombre_equipo).lower()
    idx = None
    for i, fila in enumerate(tabla_real):
        if _sin_tildes(fila.get("team", {}).get("name", "")).lower() == objetivo:
            idx = i
            break
    if idx is None:
        return

    ini = max(0, min(idx - 1, len(tabla_real) - 3))
    trio = tabla_real[ini:ini + 3]

    f_row = _cargar_fuente("Montserrat-Regular.ttf", 27)
    f_hit = _cargar_fuente("Montserrat-Bold.ttf", 28)

    if lado == "izq":
        x_pos = x_izq + 28
        x_nom = x_izq + 86
        x_pts = x_izq + CARD_ANCHO - 28
        a_pos, a_nom, a_pts = "lm", "lm", "rm"
    else:
        x_pos = x_izq + CARD_ANCHO - 28
        x_nom = x_izq + CARD_ANCHO - 86
        x_pts = x_izq + 24
        a_pos, a_nom, a_pts = "rm", "rm", "lm"

    for i, fila in enumerate(trio):
        cy = y_inicio + H_FILA_CLASIF * i + H_FILA_CLASIF // 2
        es_este = (ini + i) == idx
        fuente = f_hit if es_este else f_row
        color = NEGRO if es_este else GRIS_MEDIO

        nombre = fila["team"].get("shortName") or fila["team"].get("name", "")
        if len(nombre) > 14:
            nombre = nombre[:13] + "."

        _texto(draw, str(fila["position"]), x_pos, cy, fuente, color, anchor=a_pos)
        _texto(draw, nombre, x_nom, cy, fuente, color, anchor=a_nom)
        _texto(draw, str(fila["points"]), x_pts, cy, fuente, color, anchor=a_pts)



def _cabecera_estadio(draw, cx, cy, estadio, asistencia, max_ancho=ANCHO - 110):
    """
    Pinta "MARTINEZ VALERO  .  30.704 ESPECTADORES" en UNA linea centrada,
    con jerarquia: cifra en Bold oscuro, resto en gris.
    Reduce el cuerpo entero si no cabe. Sin asistencia, solo el estadio.
    """
    try:
        num = f"{int(asistencia):,}".replace(",", ".") if asistencia else ""
    except (TypeError, ValueError):
        num = ""

    size = 29
    while True:
        f_semi = _cargar_fuente("Montserrat-SemiBold.ttf", size)
        f_bold = _cargar_fuente("Montserrat-Bold.ttf", size)
        f_reg = _cargar_fuente("Montserrat-Regular.ttf", max(size - 3, 16))

        segmentos = [(estadio.upper(), f_reg, GRIS_MEDIO)]
        if num:
            segmentos += [
                ("   \u00b7   ", f_reg, GRIS_SUAVE),
                (num, f_reg, GRIS_MEDIO),
                (" ESPECTADORES", f_reg, GRIS_MEDIO),
            ]

        total = sum(draw.textlength(t, font=f) for t, f, _ in segmentos)
        if total <= max_ancho or size <= 20:
            break
        size -= 2

    x = cx - total / 2
    for texto, fuente, color in segmentos:
        draw.text((x, cy), texto, font=fuente, fill=color, anchor="lm")
        x += draw.textlength(texto, font=fuente)


def generar_story_resultado(partido, tabla=None):
    """Genera la Story vertical 1080x1920 en JPEG. Devuelve la ruta."""
    home = partido["home"]
    away = partido["away"]
    gh = partido["goles_home"]
    ga = partido["goles_away"]

    jornada = partido.get("jornada", "")
    fecha_txt = _formatear_fecha(partido["fecha"]) if partido.get("fecha") else ""
    estadio = _get_estadio(home["full"])
    # Asistencia: sin fuente automatica fiable (football-data.org no la
    # incluye; el endpoint interno de FotMob devuelve 404). El helper de
    # cabecera ya la soporta: basta con asignar aqui un entero si algun
    # dia hay una fuente estable.
    asistencia = None

    eh = get_equipo(home["full"])
    ea = get_equipo(away["full"])

    goleadores_home = partido.get("goleadores_home", []) or []
    goleadores_away = partido.get("goleadores_away", []) or []
    max_goleadores = max(len(goleadores_home), len(goleadores_away))

    tabla_real = _extraer_tabla(tabla)
    hay_clasif = bool(tabla_real)

    gana_h = gh > ga
    gana_a = ga > gh

    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    draw = ImageDraw.Draw(img)

    f_goles = _cargar_fuente("BebasNeue-Regular.ttf", 220)
    f_badge = _cargar_fuente("Montserrat-Bold.ttf", 34)
    f_sub = _cargar_fuente("Montserrat-SemiBold.ttf", 32)
    f_estadio = _cargar_fuente("Montserrat-SemiBold.ttf", 29)
    f_fecha = _cargar_fuente("Montserrat-Regular.ttf", 29)
    f_vs = _cargar_fuente("BebasNeue-Regular.ttf", 108)
    f_goleador = _cargar_fuente("Montserrat-Regular.ttf", 30)
    f_pie = _cargar_fuente("Montserrat-Bold.ttf", 37)

    # ------------------------------------------------------------
    # 1) ALTURA TOTAL DEL BLOQUE (para poder centrarlo)
    # ------------------------------------------------------------
    total = H_BADGE + GAP_BADGE + H_JORNADA
    if estadio:
        total += H_ESTADIO

    total += H_FECHA + GAP_CABECERA + CARD_ALTO

    if max_goleadores:
        total += GAP_TARJETA + max_goleadores * H_FILA_GOLEADOR
    if hay_clasif:
        total += (GAP_GOLEADORES if max_goleadores else GAP_TARJETA)
        total += 3 * H_FILA_CLASIF
    total += GAP_CLASIF + H_PIE

    y = CENTRO_Y - total // 2

    # ------------------------------------------------------------
    # 2) CABECERA
    # ------------------------------------------------------------
    bw = 200
    bx = (ANCHO - bw) // 2
    draw.rounded_rectangle(
        [bx, y, bx + bw, y + H_BADGE], radius=H_BADGE // 2, fill=NEGRO
    )
    _texto(draw, "FINAL", ANCHO // 2, y + H_BADGE // 2, f_badge, BLANCO)
    y += H_BADGE + GAP_BADGE

    jt = f"JORNADA {jornada}  -  LALIGA" if jornada else "LALIGA"
    _texto(draw, jt, ANCHO // 2, y + H_JORNADA // 2, f_sub, GRIS_MEDIO)
    y += H_JORNADA

    if estadio:
        _cabecera_estadio(
            draw, ANCHO // 2, y + H_ESTADIO // 2, estadio, asistencia
        )
        y += H_ESTADIO

    _texto(draw, fecha_txt, ANCHO // 2, y + H_FECHA // 2, f_fecha, GRIS_MEDIO)
    y += H_FECHA + GAP_CABECERA

    # ------------------------------------------------------------
    # 3) TARJETAS
    # ------------------------------------------------------------
    top = y
    bottom = top + CARD_ALTO

    def tarjeta(x_izq, color_fondo, color_texto, nombre, goles, ganador):
        x_der = x_izq + CARD_ANCHO
        cx = x_izq + CARD_ANCHO // 2

        draw.rectangle([x_izq, top, x_der, bottom], fill=color_fondo)
        if ganador:
            draw.rectangle([x_izq, top, x_der, top + 14], fill=ACENTO)

        lineas, fn = _partir_nombre(
            nombre.upper(), draw, size=95, max_ancho=CARD_ANCHO - 55
        )
        if len(lineas) == 1:
            _texto(draw, lineas[0], cx, top + 145, fn, color_texto)
        else:
            _texto(draw, lineas[0], cx, top + 108, fn, color_texto)
            _texto(draw, lineas[1], cx, top + 188, fn, color_texto)

        _texto(draw, str(goles), cx, top + 335, f_goles, color_texto)

    tarjeta(0, _hex_a_rgb(eh["color"]), _hex_a_rgb(eh["texto"]),
            home["name"], gh, gana_h)
    tarjeta(ANCHO - CARD_ANCHO, _hex_a_rgb(ea["color"]), _hex_a_rgb(ea["texto"]),
            away["name"], ga, gana_a)

    _texto(draw, "VS", ANCHO // 2, top + 330, f_vs, NEGRO)

    y = bottom

    # ------------------------------------------------------------
    # 4) GOLEADORES
    # ------------------------------------------------------------
    if max_goleadores:
        y += GAP_TARJETA
        max_ancho_gol = 500

        for i in range(max_goleadores):
            cy = y + i * H_FILA_GOLEADOR + H_FILA_GOLEADOR // 2

            for lista, x_texto, anchor in (
                (goleadores_home, 28, "lm"),
                (goleadores_away, ANCHO - 28, "rm"),
            ):
                if i >= len(lista):
                    continue

                texto = _texto_goleador(lista[i])
                bbox = draw.textbbox((0, 0), texto, font=f_goleador)

                if bbox[2] - bbox[0] > max_ancho_gol:
                    fuente = _ajustar_fuente(
                        texto, "Montserrat-Regular.ttf",
                        30, 20, max_ancho_gol, draw
                    )
                else:
                    fuente = f_goleador

                _texto(draw, texto, x_texto, cy, fuente,
                       GRIS_MEDIO, anchor=anchor)

        y += max_goleadores * H_FILA_GOLEADOR
        y += GAP_GOLEADORES
    else:
        y += GAP_TARJETA

    # ------------------------------------------------------------
    # 5) MINI CLASIFICACION
    # ------------------------------------------------------------
    if hay_clasif:
        clasificacion.dibujar(draw, 0, CARD_ANCHO, home["full"], tabla_real,
                              "izq", y, alto_fila=H_FILA_CLASIF)
        clasificacion.dibujar(draw, ANCHO - CARD_ANCHO, CARD_ANCHO, away["full"],
                              tabla_real, "der", y, alto_fila=H_FILA_CLASIF)
        y += 3 * H_FILA_CLASIF

    # ------------------------------------------------------------
    # 6) PIE
    # ------------------------------------------------------------
    y += GAP_CLASIF
    _texto(draw, "@autogoal.es", ANCHO // 2, y + H_PIE // 2, f_pie, NEGRO)

    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / f"story_{partido['id']}.jpg"
    img.save(ruta, "JPEG", quality=92)
    return str(ruta)
