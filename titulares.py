"""
Eleccion del titular (hook) del reel de jornada.

Prioridad: racha > salto de tabla > anomalia numerica > goleada.
La goleada va la ultima: el marcador YA se ve en la tabla de resultados,
asi que como hook no aporta nada nuevo.

Devuelve candidatos ordenados por fuerza, cada uno con el club al que
señala, para que la capa de veto pueda descartar repeticiones.
"""

from collections import defaultdict


def _resultado(gf, gc):
    return "G" if gf > gc else ("E" if gf == gc else "P")


def _historial(partidos, hasta_jornada):
    """{club: [resultados en orden]} contando SOLO jornadas <= hasta_jornada.

    Filtra por jornada y no por fecha: LaLiga adelanta y aplaza partidos,
    asi que el orden cronologico mete partidos de jornadas futuras.
    """
    h = defaultdict(list)
    ms = [m for m in partidos
          if m["matchday"] <= hasta_jornada and m["status"] == "FINISHED"]
    ms.sort(key=lambda m: (m["matchday"], m["utcDate"]))
    for m in ms:
        ft = m["score"]["fullTime"]
        hn = m["homeTeam"].get("shortName") or m["homeTeam"]["name"]
        an = m["awayTeam"].get("shortName") or m["awayTeam"]["name"]
        h[hn].append(_resultado(ft["home"], ft["away"]))
        h[an].append(_resultado(ft["away"], ft["home"]))
    return h


def _racha_final(seq, letra):
    n = 0
    for r in reversed(seq):
        if r != letra:
            break
        n += 1
    return n


ORD = {2: "SEGUNDA", 3: "TERCERA", 4: "CUARTA", 5: "QUINTA",
       6: "SEXTA", 7: "SEPTIMA", 8: "OCTAVA"}


def candidatos(jornada, partidos_jornada, tabla, todos_partidos, corto):
    """
    Lista de (fuerza, texto, club) ordenada de mas a menos potente.
    `corto` es la funcion que acorta nombres de equipo.
    """
    out = []
    hist = _historial(todos_partidos, jornada)
    jug = [m for m in partidos_jornada if m["gh"] is not None]

    # --- 1. RACHAS (lo que la tabla de resultados no puede contar)
    for club, seq in hist.items():
        C = corto(club).upper()
        # Un pleno solo es noticia cuando ya es raro. A 5 jornadas no lo es.
        if len(seq) >= 6 and all(r == "G" for r in seq):
            out.append((86 + len(seq), f"EL {C} GANA LOS {len(seq)}", club))
            continue
        p = _racha_final(seq, "P")
        if p >= 3:
            out.append((92, f"{ORD.get(p, str(p))} DERROTA SEGUIDA DEL {C}", club))
        g = _racha_final(seq, "G")
        if g >= 3:
            out.append((88, f"{ORD.get(g, str(g))} VICTORIA SEGUIDA DEL {C}", club))
        if len(seq) >= 4 and "G" not in seq:
            # Sin ganar perdiendo pesa mas que sin ganar empatando.
            out.append((90 + seq.count("P"), f"EL {C} SIGUE SIN GANAR", club))

    # --- 2. TABLA (consecuencias invisibles en los marcadores)
    for f in tabla:
        club = f["team"].get("shortName") or f["team"]["name"]
        C = corto(club).upper()
        pos, pj = f["position"], f.get("playedGames", 0)
        if pj >= 4 and f["goalsFor"] <= 2:
            # Menos goles = mas extremo = mas fuerte. 1 gol gana a 2 goles.
            out.append((100 - f["goalsFor"], f"EL {C} LLEVA {f['goalsFor']} GOL EN {pj} JORNADAS"
                        if f["goalsFor"] == 1 else
                        f"EL {C} LLEVA {f['goalsFor']} GOLES EN {pj} JORNADAS", club))
        if pos == 20:
            out.append((85, f"EL {C} ES ULTIMO", club))
        elif pos >= 18:
            out.append((80, f"EL {C}, EN PUESTOS DE DESCENSO", club))

    # --- 3. ANOMALIA DE LA JORNADA (sin club: nunca se veta)
    if jug:
        goles = sum(m["gh"] + m["ga"] for m in jug)
        fuera = sum(1 for m in jug if m["ga"] > m["gh"])
        emp = sum(1 for m in jug if m["gh"] == m["ga"])
        if goles >= 32:
            out.append((75, f"{goles} GOLES EN UNA JORNADA", None))
        if fuera == 0:
            out.append((78, "NADIE GANO FUERA DE CASA", None))
        elif fuera >= 6:
            out.append((72, f"{fuera} VICTORIAS VISITANTES", None))
        if emp >= 5:
            out.append((70, f"{emp} EMPATES EN UNA JORNADA", None))

    # --- 4. GOLEADA (ultimo recurso: ya se ve en la tabla)
    if jug:
        g = max(jug, key=lambda m: abs(m["gh"] - m["ga"]))
        dif = abs(g["gh"] - g["ga"])
        if dif >= 3:
            gana = g["home"] if g["gh"] > g["ga"] else g["away"]
            out.append((40, f"{corto(gana).upper()} GOLEA "
                        f"{max(g['gh'], g['ga'])}-{min(g['gh'], g['ga'])}", gana))

    out.sort(key=lambda x: -x[0])
    return out


# --- Memoria de titulares -------------------------------------------------
# Evita señalar al mismo club dos jornadas seguidas. Con el Valencia a 1 gol
# saldria el Valencia cinco semanas seguidas, y eso parece mania, no datos.
#
# NO lo escribe reel.py: generar el reel debe poder repetirse sin efectos.
# Solo el paso de publicar llama a recordar().

import json as _json
from pathlib import Path as _Path

ARCHIVO_TITULARES = _Path("titulares.json")


def _memoria():
    if not ARCHIVO_TITULARES.exists():
        return {}
    with open(ARCHIVO_TITULARES, "r", encoding="utf-8") as f:
        return _json.load(f)


def recordar(jornada, club):
    m = _memoria()
    m[str(jornada)] = club
    with open(ARCHIVO_TITULARES, "w", encoding="utf-8") as f:
        _json.dump(m, f, indent=2, ensure_ascii=False)


def elegir(jornada, candidatos_lista):
    """Mejor candidato que no repita el club de la jornada anterior.

    Si TODOS apuntan al club vetado, se levanta el veto: mejor repetir
    club que publicar un titular flojo.
    """
    if not candidatos_lista:
        return "RESULTADOS", None
    vetado = _memoria().get(str(jornada - 1))
    for fuerza, texto, club in candidatos_lista:
        if club is None or club != vetado:
            return texto, club
    return candidatos_lista[0][1], candidatos_lista[0][2]
