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


PESO = {
    "Real Madrid": 8, "Barça": 8,
    "Atleti": 5, "Athletic": 4, "Sevilla FC": 4, "Valencia": 4,
    "Real Betis": 4, "Real Sociedad": 3,
    "Villarreal": 2, "Celta": 2, "Espanyol": 2,
    "Deportivo": 2, "Rayo Vallecano": 2,
}

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
            out.append((92, f"¿{p} DERROTAS SEGUIDAS?", club))
        g = _racha_final(seq, "G")
        if g >= 3:
            out.append((88, f"{ORD.get(g, str(g))} VICTORIA SEGUIDA DEL {C}", club))
        if len(seq) >= 4 and "G" not in seq:
            # Sin ganar perdiendo pesa mas que sin ganar empatando.
            out.append((90 + seq.count("P"), f"¿{len(seq)} JORNADAS SIN GANAR?", club))

    # --- 2. TABLA (consecuencias invisibles en los marcadores)
    for f in tabla:
        club = f["team"].get("shortName") or f["team"]["name"]
        C = corto(club).upper()
        # playedGames viene de la clasificacion EN VIVO: con partidos aplazados
        # dos equipos llevan jornadas distintas y el titular acaba diciendo
        # "6 JORNADAS" debajo de "JORNADA 7". Contamos hasta ESTA jornada.
        pos = f["position"]
        pj = len(hist.get(club, []))
        if pj >= 4 and f["goalsFor"] <= 2:
            # Menos goles = mas extremo = mas fuerte. 1 gol gana a 2 goles.
            _n = f["goalsFor"]
            out.append((100 - _n,
                        f"¿{_n} GOL EN {pj} JORNADAS?" if _n == 1
                        else f"¿SOLO {_n} GOLES EN {pj} JORNADAS?", club))
        if pos == 20:
            out.append((85, f"EL {C} ES ÚLTIMO", club))
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

    # --- 3.5 PARTIDO ENTRE GRANDES (la conversacion de la jornada)
    # No hay lista de rivalidades a mano: "grande" es PESO >= 4, que ya
    # mide audiencia. Un Atleti-Madrid entra; un Getafe-Malaga no.
    for m in jug:
        ph, pa = PESO.get(m["home"], 0), PESO.get(m["away"], 0)
        if min(ph, pa) < 4:
            continue
        if m["gh"] == m["ga"]:
            continue
        gana = m["home"] if m["gh"] > m["ga"] else m["away"]
        pierde = m["away"] if m["gh"] > m["ga"] else m["home"]
        G, P = corto(gana).upper(), corto(pierde).upper()
        # El perdedor es el gancho: el aficionado dolido comenta, el
        # satisfecho pasa de largo.
        out.append((96 + max(ph, pa), f"EL {P} CAE ANTE EL {G}", pierde))

    # --- 4. GOLEADA (ultimo recurso: ya se ve en la tabla)
    if jug:
        g = max(jug, key=lambda m: abs(m["gh"] - m["ga"]))
        dif = abs(g["gh"] - g["ga"])
        if dif >= 3:
            gana = g["home"] if g["gh"] > g["ga"] else g["away"]
            out.append((40, f"{corto(gana).upper()} GOLEA "
                        f"{max(g['gh'], g['ga'])}-{min(g['gh'], g['ga'])}", gana))

    # A igualdad de interes del dato, gana el club que mueve mas gente.
    # Sin esto los titulares son siempre del colista: las malas rachas las
    # tienen los equipos pequeños, y son los que menos audiencia atraen.
    out = [(f + PESO.get(c, 0), tx, c) for f, tx, c in out]
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
