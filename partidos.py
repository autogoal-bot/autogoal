"""
Logica de negocio sobre partidos.
Filtra, ordena y detecta partidos recien terminados.

Adaptado al formato de football-data.org.
"""

import requests
from datetime import datetime, timedelta, timezone


ESTADO_TERMINADO = "FINISHED"

# Nombres cortos que preferimos frente al shortName de la API.
# La clave es el nombre completo (campo "name" de football-data.org).
NOMBRES_PERSONALIZADOS = {
    "RC Deportivo La Coruna": "Deportivo de La Coruña",
    "RC Deportivo La Coruña": "Deportivo de La Coruña",
    "Club Atletico de Madrid": "Atlético de Madrid",
    "Club Atlético de Madrid": "Atlético de Madrid",
    "Sevilla FC": "Sevilla",
    "Real Racing Club de Santander": "Racing de Santander",
}


def _nombre_corto(equipo):
    """Devuelve el nombre a mostrar, aplicando excepciones si las hay."""
    completo = equipo["name"]
    if completo in NOMBRES_PERSONALIZADOS:
        return NOMBRES_PERSONALIZADOS[completo]
    return equipo["shortName"] or completo

def _normalizar_nombre_espn(nombre):
    """
    Normaliza nombres para comparar football-data.org con ESPN.

    En vez de un diccionario a mano (que se rompe cada vez que asciende
    un equipo nuevo), elimina prefijos/sufijos de club y compara el
    nucleo del nombre. "RC Deportivo La Coruna" y "Deportivo" casan solos.
    """
    import unicodedata, re

    nombre = unicodedata.normalize("NFD", nombre)
    nombre = "".join(c for c in nombre if unicodedata.category(c) != "Mn")
    nombre = nombre.lower().strip()
    nombre = re.sub(r"[^a-z0-9 ]", " ", nombre)

    RUIDO = {
        "cf", "fc", "rc", "rcd", "cd", "ud", "ca", "sd", "sad",
        "club", "real", "de", "del", "la", "las", "el", "los",
        "futbol", "balompie", "deportivo1", "atletico1",
    }

    tokens = [t for t in nombre.split() if t and t not in RUIDO]

    # Casos donde el nucleo quedaria vacio o ambiguo al quitar "real"
    if not tokens:
        tokens = nombre.split()

    # Desambiguar los tres "Real" que comparten nucleo corto
    txt = nombre
    if "sociedad" in txt:
        return "sociedad"
    if "madrid" in txt and "atletico" in txt:
        return "atletico madrid"
    if "rayo" in txt:
        return "rayo vallecano"
    if "madrid" in txt:
        return "madrid"
    if "betis" in txt:
        return "betis"
    if "racing" in txt or "santander" in txt:
        return "racing"
    if "coruna" in txt or ("deportivo" in txt and "alaves" not in txt):
        return "deportivo"
    if "alaves" in txt:
        return "alaves"
    if "espanyol" in txt:
        return "espanyol"
    if "celta" in txt:
        return "celta"
    if "athletic" in txt:
        return "athletic"

    return " ".join(tokens)


def _obtener_goleadores_espn(fecha_utc, equipo_home, equipo_away):
    """
    Busca el partido en ESPN y devuelve los goleadores separados
    entre equipo local y visitante.
    """

    goleadores_home = []
    goleadores_away = []
    encontrado = False

    try:
        fecha = fecha_utc[:10].replace("-", "")

        # 1. Buscar partidos de esa fecha en ESPN
        scoreboard = requests.get(
            "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
            params={"dates": fecha},
            timeout=15
        ).json()

        evento_encontrado = None

        nombre_home = _normalizar_nombre_espn(equipo_home)
        nombre_away = _normalizar_nombre_espn(equipo_away)

        for event in scoreboard.get("events", []):
            competicion = event.get("competitions", [{}])[0]

            equipos = {}

            for competitor in competicion.get("competitors", []):
                nombre = competitor.get("team", {}).get("displayName")
                local_visitante = competitor.get("homeAway")

                equipos[local_visitante] = nombre

            if (
                _normalizar_nombre_espn(equipos.get("home", "")) == nombre_home
                and
                _normalizar_nombre_espn(equipos.get("away", "")) == nombre_away
            ):
                evento_encontrado = event
                break

        if not evento_encontrado:
            print(
                f"[ESPN] No encontrado: "
                f"{equipo_home} vs {equipo_away} ({fecha})"
            )
            return goleadores_home, goleadores_away, False

        espn_id = evento_encontrado["id"]

        # 2. Obtener el resumen del partido
        summary = requests.get(
            "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/summary",
            params={"event": espn_id},
            timeout=15
        ).json()

        # ESPN tiene el partido: su marcador sirve para contrastar
        # el de football-data.org antes de publicar.
        encontrado = True

        # 3. Extraer los goles
        for evento in summary.get("keyEvents", []):

            if evento.get("scoringPlay") is not True:
                continue

            participants = evento.get("participants", [])

            if not participants:
                continue

            jugador = (
                participants[0]
                .get("athlete", {})
                .get("displayName")
            )

            if not jugador:
                continue

            minuto = evento.get("clock", {}).get("displayValue", "")
            equipo = evento.get("team", {}).get("displayName", "")

            goleador = {
                "nombre": jugador,
                "minuto": minuto,
            }

            if _normalizar_nombre_espn(equipo) == nombre_home:
                goleadores_home.append(goleador)

            elif _normalizar_nombre_espn(equipo) == nombre_away:
                goleadores_away.append(goleador)

    except Exception as e:
        print(f"[ESPN] Error obteniendo goleadores: {e}")
        return goleadores_home, goleadores_away, False

    return goleadores_home, goleadores_away, encontrado

def normalizar(match):
    """
    Convierte el JSON de football-data.org en un dict limpio.

    Además, obtiene desde ESPN los goleadores y sus minutos.
    """

    fecha = match["utcDate"]

    home_full = match["homeTeam"]["name"]
    away_full = match["awayTeam"]["name"]

    # Obtener goleadores desde ESPN
    goleadores_home, goleadores_away, espn_ok = _obtener_goleadores_espn(
        fecha,
        home_full,
        away_full
    )

    return {
        "id": match["id"],
        "fecha": fecha,
        "estado": match["status"],
        "jornada": match.get("matchday"),

        "home": {
            "name": _nombre_corto(match["homeTeam"]),
            "full": home_full,
            "tla": match["homeTeam"]["tla"],
        },

        "away": {
            "name": _nombre_corto(match["awayTeam"]),
            "full": away_full,
            "tla": match["awayTeam"]["tla"],
        },

        "goles_home": match["score"]["fullTime"]["home"],
        "goles_away": match["score"]["fullTime"]["away"],

        "goleadores_home": goleadores_home,
        "goleadores_away": goleadores_away,
        "espn_ok": espn_ok,
    }

def esta_terminado(partido):
    """True si el partido ya acabo."""
    return partido["estado"] == ESTADO_TERMINADO


def termino_hace_menos_de(partido, minutos):
    """
    True si el partido termino hace menos de X minutos.
    """
    if not esta_terminado(partido):
        return False

    fecha_str = partido["fecha"].replace("Z", "+00:00")
    fecha_partido = datetime.fromisoformat(fecha_str)
    ahora = datetime.now(timezone.utc)

    fin_estimado = fecha_partido + timedelta(hours=2)
    diferencia = ahora - fin_estimado

    return timedelta(0) <= diferencia <= timedelta(minutes=minutos)


def filtrar_terminados(matches):
    """Devuelve solo los partidos ya finalizados, normalizados."""
    return [
        normalizar(m) for m in matches
        if m["status"] == ESTADO_TERMINADO
    ]