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
import clasificacion

ANCHO = 1080
ALTO = 1080
CARPETA_FUENTES = Path("fuentes")
CARPETA_SALIDA = Path("imagenes_generadas")

FONDO = (245, 246, 248)
BLANCO = (255, 255, 255)
NEGRO = (20, 22, 26)
GRIS_MEDIO = (120, 125, 135)
ACENTO = (212, 175, 55)  # dorado para resaltar al ganador

CARD_TOP = 270
CARD_BOTTOM = 880
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


def _partir_nombre(texto, draw, size=90, max_ancho=CARD_ANCHO - 50):
    """
    Devuelve (lineas, fuente) manteniendo el tamano grande.
    Si el nombre no cabe en una linea, lo parte en dos por la palabra
    que mejor equilibre. Solo reduce la fuente como ultimo recurso.
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


def _extraer_tabla_clasificacion(tabla):
    """
    Extrae la lista de equipos desde la respuesta completa de
    football-data.org.

    Acepta tanto la respuesta completa de la API como una lista ya
    preparada, para mantener la funcion robusta.
    """
    if not tabla:
        return []

    if isinstance(tabla, list):
        return tabla

    if isinstance(tabla, dict):
        standings = tabla.get("standings", [])
        if standings:
            return standings[0].get("table", [])

    return []


def _mini_clasificacion(
    draw,
    x_izq,
    nombre_equipo,
    tabla,
    lado="izq",
    y_inicio=670,
):
    """
    Mini clasificación:

        predecesor
        equipo del partido  <- destacado
        perseguidor

    La clasificación se coloca debajo de los goleadores.
    """

    tabla_real = _extraer_tabla_clasificacion(tabla)

    if not tabla_real:
        return

    objetivo = _sin_tildes(nombre_equipo).lower()
    idx = None

    for i, fila in enumerate(tabla_real):
        nombre = fila.get("team", {}).get("name", "")

        if _sin_tildes(nombre).lower() == objetivo:
            idx = i
            break

    if idx is None:
        return

    ini = max(0, min(idx - 1, len(tabla_real) - 3))
    trio = tabla_real[ini:ini + 3]

    f_row = _cargar_fuente("Montserrat-Regular.ttf", 20)
    f_hit = _cargar_fuente("Montserrat-Bold.ttf", 21)

    # --------------------------------------------------------
    # POSICIÓN VERTICAL
    # --------------------------------------------------------

    # La posición ya viene calculada desde generar_imagen_resultado.
    # Así local y visitante pueden tener una posición distinta
    # dependiendo de cuántos goleadores tenga cada uno.
    y0 = y_inicio

    alto_fila = 25

    # --------------------------------------------------------
    # POSICIÓN HORIZONTAL
    # --------------------------------------------------------

    if lado == "izq":
        x_pos = x_izq + 34
        x_nom = x_izq + 78
        x_pts = x_izq + CARD_ANCHO - 34

        anchor_pos = "lm"
        anchor_nom = "lm"
        anchor_pts = "rm"

    else:
        x_pos = x_izq + CARD_ANCHO - 34
        x_nom = x_izq + CARD_ANCHO - 78
        x_pts = x_izq + 34

        anchor_pos = "rm"
        anchor_nom = "rm"
        anchor_pts = "lm"

    # --------------------------------------------------------
    # DIBUJAR LAS 3 FILAS
    # --------------------------------------------------------

    for i, fila in enumerate(trio):

        cy = y0 + alto_fila * i + alto_fila // 2

        es_este = (ini + i) == idx

        fuente = f_hit if es_este else f_row
        color = NEGRO if es_este else GRIS_MEDIO

        nombre = (
            fila["team"].get("shortName")
            or fila["team"].get("name", "")
        )

        if len(nombre) > 16:
            nombre = nombre[:15] + "."

        _texto(
            draw,
            str(fila["position"]),
            x_pos,
            cy,
            fuente,
            color,
            anchor=anchor_pos,
        )

        _texto(
            draw,
            nombre,
            x_nom,
            cy,
            fuente,
            color,
            anchor=anchor_nom,
        )

        _texto(
            draw,
            str(fila["points"]),
            x_pts,
            cy,
            fuente,
            color,
            anchor=anchor_pts,
        )


def _dibujar_tarjeta(
    draw,
    x_izq,
    color_fondo,
    color_texto,
    nombre,
    goles,
    fuentes,
    es_ganador,
    goleadores=None,
    lado="izq",
):
    """
    Dibuja la tarjeta superior del equipo y sus goleadores debajo.

    Los goleadores quedan fuera del fondo de color:
    - local: alineados a la izquierda
    - visitante: alineados a la derecha
    """
    x_der = x_izq + CARD_ANCHO
    cx = x_izq + CARD_ANCHO // 2

    # Tarjeta de color compacta.
    card_bottom_nuevo = 650

    draw.rectangle(
        [x_izq, CARD_TOP, x_der, card_bottom_nuevo],
        fill=color_fondo
    )

    if es_ganador:
        draw.rectangle(
            [x_izq, CARD_TOP, x_der, CARD_TOP + 10],
            fill=ACENTO
        )

    # Nombre del equipo mas arriba.
    lineas, fn = _partir_nombre(
        nombre.upper(),
        draw,
        size=82,
        max_ancho=CARD_ANCHO - 55
    )

    if len(lineas) == 1:
        _texto(
            draw,
            lineas[0],
            cx,
            CARD_TOP + 115,
            fn,
            color_texto
        )
    else:
        _texto(
            draw,
            lineas[0],
            cx,
            CARD_TOP + 82,
            fn,
            color_texto
        )
        _texto(
            draw,
            lineas[1],
            cx,
            CARD_TOP + 155,
            fn,
            color_texto
        )

    # Resultado.
    _texto(
        draw,
        str(goles),
        cx,
        CARD_TOP + 275,
        fuentes["goles"],
        color_texto
    )

    # --------------------------------------------------------
    # GOLEADORES FUERA DE LA TARJETA
    # --------------------------------------------------------

    if not goleadores:
        return

    f_goleador = _cargar_fuente(
        "Montserrat-Regular.ttf", 24
    )

    f_minuto = _cargar_fuente(
        "Montserrat-Regular.ttf", 22
    )

    # Posicion de inicio de los goleadores.
    y_gol = 670

    if lado == "izq":
        x_texto = x_izq + 28
        anchor = "lm"
    else:
        x_texto = x_der - 28
        anchor = "rm"

    for gol in goleadores:
        nombre_gol = gol.get("nombre", "")
        minuto = gol.get("minuto", "")

        texto_gol = f"{nombre_gol}  {minuto}"

        # Si es demasiado largo, reducimos antes de cortar.
        max_ancho = CARD_ANCHO - 55
        bbox = draw.textbbox(
            (0, 0),
            texto_gol,
            font=f_goleador
        )

        if bbox[2] - bbox[0] > max_ancho:
            f_tmp = _ajustar_fuente(
                texto_gol,
                "Montserrat-SemiBold.ttf",
                24,
                17,
                max_ancho,
                draw
            )
        else:
            f_tmp = f_goleador

        _texto(
            draw,
            texto_gol,
            x_texto,
            y_gol,
            f_tmp,
            GRIS_MEDIO,
            anchor=anchor
        )

        y_gol += 29


def generar_imagen_resultado(partido, tabla=None):
    home = partido["home"]
    away = partido["away"]
    goles_home = partido["goles_home"]
    goles_away = partido["goles_away"]
    goleadores_home = partido.get("goleadores_home", [])
    goleadores_away = partido.get("goleadores_away", [])
    jornada = partido.get("jornada", "")
    fecha_txt = _formatear_fecha(partido["fecha"]) if partido.get("fecha") else ""
    estadio = _get_estadio(home["full"])

    eh = get_equipo(home["full"])
    ea = get_equipo(away["full"])

    gana_home = goles_home > goles_away
    gana_away = goles_away > goles_home

    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    draw = ImageDraw.Draw(img)

    fuentes = {"goles": _cargar_fuente("BebasNeue-Regular.ttf", 190)}
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
    _texto(draw, jt, ANCHO // 2, 150, f_sub, GRIS_MEDIO)

    # Estadio + fecha/hora debajo de la jornada.
    info_y = 190

    if estadio:
        _texto(
            draw,
            estadio.upper(),
            ANCHO // 2,
            info_y,
            f_estadio,
            GRIS_MEDIO
        )
        info_y += 34

    _texto(
        draw,
        fecha_txt,
        ANCHO // 2,
        info_y,
        f_fsmall,
        GRIS_MEDIO
    )

    # ── TARJETAS ──
    _dibujar_tarjeta(
        draw,
        0,
        _hex_a_rgb(eh["color"]),
        _hex_a_rgb(eh["texto"]),
        home["name"],
        goles_home,
        fuentes,
        gana_home,
        goleadores_home,
        "izq",
    )

    _dibujar_tarjeta(
        draw,
        ANCHO - CARD_ANCHO,
        _hex_a_rgb(ea["color"]),
        _hex_a_rgb(ea["texto"]),
        away["name"],
        goles_away,
        fuentes,
        gana_away,
        goleadores_away,
        "der",
    )

    # ── MINI CLASIFICACIÓN ──
    # Ambas mini-clasificaciones empiezan EXACTAMENTE a la misma altura.
    # Reservamos espacio según el equipo que tenga más goleadores.
    # Así nunca se solapan con los goleadores de ninguno de los dos lados.

    alto_goleador = 29
    margen_clasificacion = 18

    max_goleadores = max(
        len(goleadores_home),
        len(goleadores_away),
    )

    y_clas = (
        670
        + max_goleadores * alto_goleador
        + margen_clasificacion
    )

    clasificacion.dibujar(draw, 0, CARD_ANCHO, home["full"], tabla,
                          "izq", y_clas, alto_fila=35, escala=0.72)

    clasificacion.dibujar(draw, ANCHO - CARD_ANCHO, CARD_ANCHO, away["full"],
                          tabla, "der", y_clas, alto_fila=35, escala=0.72)

    _texto(draw, "VS", ANCHO // 2, CARD_TOP + 265, f_vs, NEGRO)

    # ── FOOTER ──
    # Se coloca justo debajo del contenido, no clavado al fondo,
    # para que el bloque no quede descolgado en marcadores cortos.
    y_footer = max(y_clas + 3 * 35 + 70, 980)
    _texto(draw, "@autogoal.es", ANCHO // 2, y_footer, f_fbig, NEGRO)

    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / f"partido_{partido['id']}.jpg"
    img.save(ruta, "JPEG", quality=92)
    return str(ruta)
