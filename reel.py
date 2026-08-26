"""
Reel vertical de 3 segundos, tres pantallas secuenciales:

  0.0-1.0s  RESULTADOS de la jornada
  1.0-2.0s  CLASIFICACION completa (20 equipos)
  2.0-3.0s  PICHICHI top 10

Corte seco entre pantallas: con solo 1s cada una, cualquier transicion
robaria tiempo de lectura. El Reel hace loop, asi que el usuario ve el
ciclo 4-5 veces en 15 segundos y capta mas en cada pasada.
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
DUR_PANTALLA = 1.0
CARPETA_FUENTES = Path("fuentes")
CARPETA_SALIDA = Path("videos_generados")

FONDO = (245, 246, 248)
BLANCO = (255, 255, 255)
NEGRO = (20, 22, 26)
GRIS = (128, 134, 146)
GRIS_OSC = (62, 68, 80)
ORO = (212, 175, 55)
LINEA = (226, 229, 235)
FILA_ALT = (236, 239, 244)


def _f(nombre, size):
    return ImageFont.truetype(str(CARPETA_FUENTES / nombre), size)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def _corto(nombre):
    return clas.ALIAS_CLASIF.get(_sin_tildes(nombre).lower(), nombre)




# En la columna de resultados el espacio es estrecho: hay nombres que
# caben en la clasificacion pero chocan con el marcador. Version breve.
BREVE = {
    "Deportivo La Coruña": "Deportivo",
    "Real Sociedad": "R. Sociedad",
    "Rayo Vallecano": "Rayo",
    "Atleti": "Atletico Madrid",
    "Barça": "Barcelona",
}


def _breve(nombre):
    n = _corto(nombre)
    return BREVE.get(n, n)


def titular_jornada(partidos, tabla, pichichis):
    """
    Genera el gancho del primer frame. Prioridad: lo que mas para el pulgar.
    Una goleada gana a un liderato; un liderato gana a un dato de goleador.
    """
    jugados = [m for m in partidos if m["gh"] is not None]

    # 1) Goleada: diferencia de 3 o mas
    if jugados:
        g = max(jugados, key=lambda m: abs(m["gh"] - m["ga"]))
        dif = abs(g["gh"] - g["ga"])
        if dif >= 3:
            gana = g["home"] if g["gh"] > g["ga"] else g["away"]
            marcador = f"{max(g['gh'], g['ga'])}-{min(g['gh'], g['ga'])}"
            return f"{_corto(gana).upper()} GOLEA {marcador}"

    # 2) Lider en solitario
    if len(tabla) > 1 and tabla[0]["points"] > tabla[1]["points"]:
        lider = tabla[0]["team"].get("shortName") or tabla[0]["team"]["name"]
        return f"{_corto(lider).upper()} LIDERA EN SOLITARIO"

    # 3) Pichichi destacado
    if len(pichichis) > 1 and pichichis[0]["goles"] > pichichis[1]["goles"]:
        return f"{pichichis[0]['nombre'].upper()} MANDA CON {pichichis[0]['goles']} GOLES"

    return "RESULTADOS"


def _cabecera(d, titulo, subtitulo):
    # Marca arriba: si alguien comparte o graba el Reel, la marca viaja con el.
    d.text((ANCHO // 2, 78), "AUTOGOAL", font=_f("BebasNeue-Regular.ttf", 52),
           fill=NEGRO, anchor="mm")
    d.rectangle([ANCHO // 2 - 90, 108, ANCHO // 2 + 90, 113], fill=ORO)

    d.text((ANCHO // 2, 186), titulo, font=_f("BebasNeue-Regular.ttf", 92),
           fill=NEGRO, anchor="mm")
    d.text((ANCHO // 2, 250), subtitulo, font=_f("Montserrat-Bold.ttf", 30),
           fill=ORO, anchor="mm")


def _pie(d, progreso):
    d.text((ANCHO // 2, ALTO - 80), "@autogoal.es",
           font=_f("Montserrat-Bold.ttf", 36), fill=NEGRO, anchor="mm")
    d.rectangle([0, ALTO - 10, int(ANCHO * progreso), ALTO], fill=ORO)


def _pantalla_resultados(jornada, partidos, progreso, titular="RESULTADOS"):
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)
    _cabecera(d, f"JORNADA {jornada}", "RESULTADOS")

    f_eq = _f("Montserrat-SemiBold.ttf", 38)
    f_gol = _f("BebasNeue-Regular.ttf", 62)

    n = len(partidos[:10])
    alto = 122
    y = 330

    for i, m in enumerate(partidos[:10]):
        if i % 2 == 1:
            d.rectangle([50, y, ANCHO - 50, y + alto - 8], fill=FILA_ALT)

        cy = y + (alto - 8) // 2
        ch = _rgb(get_equipo(m["home_full"]).get("color", "#888888"))
        ca = _rgb(get_equipo(m["away_full"]).get("color", "#888888"))

        d.rectangle([64, cy - 26, 74, cy + 26], fill=ch)
        d.text((94, cy), _breve(m["home"])[:17], font=f_eq,
               fill=GRIS_OSC, anchor="lm")

        gh, ga = m["gh"], m["ga"]
        if gh is None or ga is None:
            d.text((ANCHO // 2, cy), m.get("cuando", "-"),
                   font=_f("Montserrat-Bold.ttf", 30), fill=ORO, anchor="mm")
        else:
            d.text((ANCHO // 2 - 26, cy + 4), str(gh), font=f_gol,
                   fill=NEGRO if gh >= ga else GRIS, anchor="rm")
            d.text((ANCHO // 2, cy), "-", font=f_eq, fill=GRIS, anchor="mm")
            d.text((ANCHO // 2 + 26, cy + 4), str(ga), font=f_gol,
                   fill=NEGRO if ga >= gh else GRIS, anchor="lm")

        d.text((ANCHO - 94, cy), _breve(m["away"])[:17], font=f_eq,
               fill=GRIS_OSC, anchor="rm")
        d.rectangle([ANCHO - 74, cy - 26, ANCHO - 64, cy + 26], fill=ca)

        y += alto

    _pie(d, progreso)
    return img


def _pantalla_clasificacion(tabla, progreso):
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)
    _cabecera(d, "CLASIFICACIÓN", "LALIGA")

    f_pos = _f("Montserrat-Bold.ttf", 26)
    f_nom = _f("Montserrat-SemiBold.ttf", 34)
    f_pts = _f("BebasNeue-Regular.ttf", 48)

    alto = 74
    y = 310

    for i, fila in enumerate(tabla[:20]):
        pos = i + 1
        cz = clas.color_zona(pos)
        cy = y + alto // 2

        if i % 2 == 1:
            d.rectangle([50, y, ANCHO - 50, y + alto - 4], fill=FILA_ALT)

        d.rounded_rectangle([64, cy - 22, 108, cy + 22], radius=8,
                            fill=cz if cz else (214, 218, 226))
        d.text((86, cy + 1), str(pos), font=f_pos,
               fill=BLANCO if cz else GRIS, anchor="mm")

        nom = fila["team"].get("shortName") or fila["team"]["name"]
        d.text((132, cy), _nombre_reel(nom)[:24], font=f_nom,
               fill=NEGRO, anchor="lm")
        d.text((ANCHO - 70, cy + 3), str(fila["points"]), font=f_pts,
               fill=NEGRO, anchor="rm")

        y += alto

    _pie(d, progreso)
    return img



# En el Reel hay espacio de sobra: nombres completos, no las abreviaturas
# de la mini clasificacion (donde la celda es estrecha).
ALIAS_REEL = {
    "barca": "Barcelona",
    "atleti": "Atlético de Madrid",
    "r. sociedad": "Real Sociedad",
    "deportivo la coruna": "Deportivo",
}


def _nombre_reel(nombre):
    n = _corto(nombre)
    return ALIAS_REEL.get(_sin_tildes(n).lower(), n)



# Equipos cuya camiseta es reconocible por una franja diagonal.
# El color de equipos.py es el de fondo; aqui va el de la franja.
FRANJA_DIAGONAL = {
    "rayo vallecano de madrid": ((255, 255, 255), (206, 30, 40)),
}


def _capsula_equipo(img, d, x0, y, x1, y1, radio, nombre_full, color):
    """
    Pinta la capsula. Si el equipo tiene franja diagonal reconocible,
    la dibuja recortada dentro de la capsula mediante mascara.
    """
    clave = _sin_tildes(nombre_full).lower()
    franja = FRANJA_DIAGONAL.get(clave)

    if not franja:
        d.rounded_rectangle([x0, y, x1, y1], radius=radio, fill=color)
        return

    base, color_franja = franja

    capa = Image.new("RGB", (x1 - x0, y1 - y), base)
    cd = ImageDraw.Draw(capa)
    w, h = capa.size
    cd.polygon([(w * 0.30, 0), (w * 0.52, 0), (w * 0.22, h), (0, h)],
               fill=color_franja)

    mask = Image.new("L", (x1 - x0, y1 - y), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1],
                                           radius=radio, fill=255)
    img.paste(capa, (x0, y), mask)


def _texto_sobre(color):
    """Blanco o negro segun luminancia, para que el nombre siempre se lea."""
    r, g, b = color
    return NEGRO if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else BLANCO


def _pantalla_pichichi(pichichis, progreso):
    """
    Estilo capsula: filas compactas en color de equipo, texto grande que
    llena la fila, y el lider en blanco rompiendo el patron cromatico.
    """
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)
    _cabecera(d, "PICHICHI", "MÁXIMOS GOLEADORES")

    alto = 122
    gap = 14
    y = 332
    x0, x1 = 70, ANCHO - 70

    for i, s in enumerate(pichichis[:10]):
        lider = (i == 0)
        cy = y + alto // 2

        col = _rgb(get_equipo(s.get("equipo_full", s.get("equipo", ""))).get("color", "#888888"))
        if lider:
            fondo, txt, sub = BLANCO, ORO, (130, 136, 148)
        else:
            fondo, txt = col, _texto_sobre(col)
            sub = txt

        # Capsula: radio = mitad del alto
        d.rounded_rectangle([x0, y, x1, y + alto], radius=alto // 2, fill=fondo)

        # Posicion dentro de la capsula, en circulo
        px = x0 + 54
        d.ellipse([px - 34, cy - 34, px + 34, cy + 34],
                  fill=ORO if lider else BLANCO)
        d.text((px, cy + 1), str(i + 1),
               font=_f("Montserrat-Bold.ttf", 32),
               fill=BLANCO if lider else col, anchor="mm")

        # Nombre grande + equipo pequeno, juntos
        d.text((px + 58, cy - 18), s["nombre"][:27],
               font=_f("Montserrat-Bold.ttf", 40), fill=txt, anchor="lm")
        d.text((px + 60, cy + 30), _nombre_reel(s.get("equipo", ""))[:22].upper(),
               font=_f("Montserrat-Bold.ttf", 28), fill=sub, anchor="lm")

        # Goles en circulo integrado al borde derecho
        gx = x1 - 56
        d.ellipse([gx - 40, cy - 40, gx + 40, cy + 40], fill=BLANCO,
                  outline=ORO if lider else None, width=5)
        d.text((gx, cy + 3), str(s["goles"]),
               font=_f("BebasNeue-Regular.ttf", 54),
               fill=NEGRO, anchor="mm")

        y += alto + gap

    _pie(d, progreso)
    return img


def generar_reel(jornada, partidos, tabla, pichichis):
    CARPETA_SALIDA.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDA / f"reel_jornada_{jornada}.mp4"

    tit = titular_jornada(partidos, tabla, pichichis)
    print("Titular:", tit)
    por_pantalla = int(FPS * DUR_PANTALLA)
    total = por_pantalla * 3

    writer = imageio.get_writer(str(ruta), fps=FPS, codec="libx264",
                                quality=8, macro_block_size=1)
    for i in range(total):
        prog = i / (total - 1)
        if i < por_pantalla:
            frame = _pantalla_resultados(jornada, partidos, prog, tit)
        elif i < por_pantalla * 2:
            frame = _pantalla_clasificacion(tabla, prog)
        else:
            frame = _pantalla_pichichi(pichichis, prog)
        writer.append_data(np.asarray(frame))
    writer.close()
    return str(ruta)
