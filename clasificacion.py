"""
Mini clasificacion premium, compartida por Story y feed.

Diseño:
  [pos]  Equipo .......... PTS
- Mismo orden de lectura en ambos lados (no espejado)
- Posicion en pastilla: se lee como ranking sin necesidad de etiqueta
- Puntos en Bebas grande: el numero dominante de la fila
- Fila del equipo del partido sobre fondo destacado
- Barra de color en el borde exterior segun zona europea o descenso
"""

import unicodedata
from pathlib import Path
from PIL import ImageFont

CARPETA_FUENTES = Path("fuentes")

BLANCO = (255, 255, 255)
NEGRO = (20, 22, 26)
GRIS_TEXTO = (128, 134, 146)
GRIS_NUM = (96, 103, 116)
PILL_BG = (214, 218, 226)
PILL_BG_HIT = (176, 182, 194)
FILA_HIT = (233, 236, 241)
LINEA = (226, 229, 235)

# Convencion LaLiga: 1-4 Champions, 5 Europa, 6 Conference, 18-20 descenso.
# Tonos desaturados a proposito: identifican sin gritar.
ZONAS = (
    (1, 4, (108, 143, 186)),
    (5, 5, (214, 163, 106)),
    (6, 6, (118, 172, 168)),
    (18, 20, (198, 128, 128)),
)



# Nombres cortos para la mini clasificacion. Se buscan sin tildes y en
# minusculas, asi coinciden con cualquier variante de la API.
ALIAS_CLASIF = {
    "rayo vallecano de madrid": "Rayo",
    "rayo vallecano": "Rayo",
    "real sociedad de futbol": "R. Sociedad",
    "rc deportivo la coruna": "Deportivo",
    "real racing club de santander": "Racing",
    "real racing club": "Racing",
    "rcd espanyol de barcelona": "Espanyol",
    "club atletico de madrid": "Atleti",
    "real betis balompie": "Betis",
    "real madrid cf": "Real Madrid",
    "fc barcelona": "Barça",
    "villarreal cf": "Villarreal",
}


def color_zona(pos):
    for lo, hi, color in ZONAS:
        if lo <= pos <= hi:
            return color
    return None


def _fuente(nombre, size):
    return ImageFont.truetype(str(CARPETA_FUENTES / nombre), size)


def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def extraer_tabla(tabla):
    if not tabla:
        return []
    if isinstance(tabla, list):
        return tabla
    if isinstance(tabla, dict):
        s = tabla.get("standings", [])
        if s:
            return s[0].get("table", [])
    return []


def dibujar(draw, x_izq, ancho, nombre_equipo, tabla, lado, y_inicio,
            alto_fila=48, escala=1.0):
    """
    Dibuja las 3 filas. 'escala' permite reducir todo para el feed
    manteniendo exactamente las mismas proporciones.
    """
    filas = extraer_tabla(tabla)
    if not filas:
        return

    objetivo = _sin_tildes(nombre_equipo).lower()
    idx = next((i for i, f in enumerate(filas)
                if _sin_tildes(f.get("team", {}).get("name", "")).lower() == objetivo),
               None)
    if idx is None:
        return

    ini = max(0, min(idx - 1, len(filas) - 3))
    trio = filas[ini:ini + 3]

    s = lambda v: max(int(v * escala), 1)

    f_pos = _fuente("Montserrat-Bold.ttf", s(20))
    f_nom = _fuente("Montserrat-Regular.ttf", s(27))
    f_hit = _fuente("Montserrat-Bold.ttf", s(27))
    f_pts = _fuente("BebasNeue-Regular.ttf", s(38))

    pill = s(34)
    pad = s(22)
    barra = s(5)
    x0 = x_izq + s(14)
    x1 = x_izq + ancho - s(14)

    for i, fila in enumerate(trio):
        y0 = y_inicio + alto_fila * i
        y1 = y0 + alto_fila
        cy = y0 + alto_fila // 2
        hit = (ini + i) == idx

        if hit:
            draw.rounded_rectangle([x0, y0 + 1, x1, y1 - 1],
                                   radius=s(7), fill=FILA_HIT)
        elif i > 0:
            draw.line([(x0 + pad, y0), (x1 - pad, y0)], fill=LINEA, width=1)

        pos_visual = ini + i + 1
        cz = color_zona(pos_visual)

        if cz:
            fondo_pill = cz
            color_num = BLANCO
        elif hit:
            fondo_pill = PILL_BG_HIT
            color_num = (58, 64, 76)
        else:
            fondo_pill = PILL_BG
            color_num = GRIS_NUM

        px = x0 + pad
        draw.rounded_rectangle([px, cy - pill // 2, px + pill, cy + pill // 2],
                               radius=s(6), fill=fondo_pill)
        draw.text((px + pill // 2, cy + 1), str(pos_visual),
                  font=f_pos, fill=color_num, anchor="mm")

        nombre_raw = fila["team"].get("shortName") or fila["team"].get("name", "")
        clave = _sin_tildes(nombre_raw).lower()
        nombre = ALIAS_CLASIF.get(clave, nombre_raw)
        if len(nombre) > 13:
            nombre = nombre[:12] + "."
        draw.text((px + pill + s(16), cy), nombre,
                  font=f_hit if hit else f_nom,
                  fill=NEGRO if hit else GRIS_TEXTO, anchor="lm")

        draw.text((x1 - pad, cy + s(2)), str(fila["points"]),
                  font=f_pts, fill=NEGRO if hit else GRIS_NUM, anchor="rm")
