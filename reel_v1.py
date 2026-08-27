"""
Reel vertical de 3 segundos con el resumen de la jornada.

Filosofia: los Reels hacen loop. En 3s no se puede secuenciar, pero si
mostrar todo a la vez y dejar que el bucle haga el resto: el usuario ve
la composicion 4-5 veces en 15 segundos y capta mas en cada pasada.

  0.0-0.4s  los tres bloques entran deslizando
  0.4-2.6s  composicion completa, legible
  2.6-3.0s  barra dorada de progreso
"""

import unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import imageio.v2 as imageio

from equipos import get_equipo
import clasificacion as clas

ANCHO, ALTO = 1080, 1920
FPS = 30
DURACION = 3.0
CARPETA_FUENTES = Path("fuentes")
CARPETA_SALIDA = Path("videos_generados")

FONDO = (245, 246, 248)
BLANCO = (255, 255, 255)
NEGRO = (20, 22, 26)
GRIS = (128, 134, 146)
GRIS_OSC = (62, 68, 80)
ORO = (212, 175, 55)
LINEA = (226, 229, 235)


def _f(nombre, size):
    return ImageFont.truetype(str(CARPETA_FUENTES / nombre), size)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def _ease(t):
    """Easing out cubico: entra rapido y frena. Da sensacion premium."""
    return 1 - (1 - t) ** 3


def _corto(nombre):
    clave = _sin_tildes(nombre).lower()
    return clas.ALIAS_CLASIF.get(clave, nombre)


def _frame(jornada, partidos, tabla, pichichis, progreso):
    """Dibuja un frame. 'progreso' va de 0.0 a 1.0."""
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)

    # Animacion de entrada: los bloques deslizan en los primeros 0.4s
    p = _ease(min(progreso / 0.133, 1.0))
    off = int((1 - p) * 260)

    f_titulo = _f("BebasNeue-Regular.ttf", 92)
    f_sub = _f("Montserrat-Bold.ttf", 30)
    f_eq = _f("Montserrat-SemiBold.ttf", 31)
    f_gol = _f("BebasNeue-Regular.ttf", 46)
    f_sec = _f("Montserrat-Bold.ttf", 26)
    f_pos = _f("Montserrat-Bold.ttf", 22)
    f_nom = _f("Montserrat-Regular.ttf", 29)
    f_pts = _f("BebasNeue-Regular.ttf", 40)
    f_pie = _f("Montserrat-Bold.ttf", 34)

    # ── CABECERA ──
    d.text((ANCHO // 2, 150), f"JORNADA {jornada}", font=f_titulo,
           fill=NEGRO, anchor="mm")
    d.text((ANCHO // 2, 215), "LALIGA", font=f_sub, fill=ORO, anchor="mm")

    # ── RESULTADOS (entran desde la izquierda) ──
    y = 300
    d.text((60 - off, y), "RESULTADOS", font=f_sec, fill=GRIS, anchor="lm")
    y += 46

    for m in partidos[:10]:
        h = _corto(m["home"])
        a = _corto(m["away"])
        gh, ga = m["gh"], m["ga"]

        ch = _rgb(get_equipo(m["home_full"]).get("color", "#888888"))
        ca = _rgb(get_equipo(m["away_full"]).get("color", "#888888"))

        d.rectangle([60 - off, y + 8, 68 - off, y + 42], fill=ch)
        d.text((84 - off, y + 25), h[:14], font=f_eq, fill=GRIS_OSC, anchor="lm")

        d.text((ANCHO // 2 - 34 - off, y + 26), str(gh), font=f_gol,
               fill=NEGRO if gh > ga else GRIS, anchor="rm")
        d.text((ANCHO // 2 - off, y + 25), "-", font=f_eq, fill=GRIS, anchor="mm")
        d.text((ANCHO // 2 + 34 - off, y + 26), str(ga), font=f_gol,
               fill=NEGRO if ga > gh else GRIS, anchor="lm")

        d.text((ANCHO - 84 - off, y + 25), a[:14], font=f_eq,
               fill=GRIS_OSC, anchor="rm")
        d.rectangle([ANCHO - 68 - off, y + 8, ANCHO - 60 - off, y + 42], fill=ca)

        y += 52

    # ── CLASIFICACION (entra desde la derecha) ──
    y += 24
    d.line([(60, y), (ANCHO - 60, y)], fill=LINEA, width=2)
    y += 30
    d.text((60 + off, y), "CLASIFICACION", font=f_sec, fill=GRIS, anchor="lm")
    y += 46

    for i, fila in enumerate(tabla[:5]):
        pos = i + 1
        cz = clas.color_zona(pos)
        cy = y + 24

        d.rounded_rectangle([60 + off, cy - 18, 96 + off, cy + 18],
                            radius=7, fill=cz if cz else (214, 218, 226))
        d.text((78 + off, cy + 1), str(pos), font=f_pos,
               fill=BLANCO if cz else GRIS, anchor="mm")

        nom = fila["team"].get("shortName") or fila["team"]["name"]
        d.text((116 + off, cy), _corto(nom)[:20], font=f_nom,
               fill=NEGRO, anchor="lm")
        d.text((ANCHO - 60 + off, cy + 2), str(fila["points"]),
               font=f_pts, fill=NEGRO, anchor="rm")

        y += 50

    # ── PICHICHI (entra desde la izquierda) ──
    y += 24
    d.line([(60, y), (ANCHO - 60, y)], fill=LINEA, width=2)
    y += 30
    d.text((60 - off, y), "PICHICHI", font=f_sec, fill=GRIS, anchor="lm")
    y += 46

    for i, s in enumerate(pichichis[:3]):
        cy = y + 24
        d.text((60 - off, cy), f"{i+1}", font=f_pos, fill=ORO, anchor="lm")
        d.text((100 - off, cy), s["nombre"][:24], font=f_nom,
               fill=NEGRO, anchor="lm")
        d.text((ANCHO - 60 - off, cy + 2), str(s["goles"]),
               font=f_pts, fill=NEGRO, anchor="rm")
        y += 50

    # ── BARRA DE PROGRESO + PIE ──
    d.rectangle([0, ALTO - 12, int(ANCHO * progreso), ALTO], fill=ORO)
    d.text((ANCHO // 2, ALTO - 90), "@autogoal.es", font=f_pie,
           fill=NEGRO, anchor="mm")

    return img


def generar_reel(jornada, partidos, tabla, pichichis):
    """Genera el MP4. Devuelve la ruta."""
    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / f"reel_jornada_{jornada}.mp4"

    total = int(FPS * DURACION)
    writer = imageio.get_writer(str(ruta), fps=FPS, codec="libx264",
                                quality=8, macro_block_size=1)
    for i in range(total):
        frame = _frame(jornada, partidos, tabla, pichichis, i / (total - 1))
        writer.append_data(np.asarray(frame))
    writer.close()
    return str(ruta)
