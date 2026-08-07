"""
Logica de negocio sobre partidos.
Filtra, ordena y detecta partidos recien terminados.

Adaptado al formato de football-data.org.
"""

from datetime import datetime, timedelta, timezone


ESTADO_TERMINADO = "FINISHED"


def normalizar(match):
    """
    Convierte el JSON de football-data.org en un dict limpio.

    Usamos shortName (nombres cortos oficiales) y tla (siglas de 3 letras)
    que vienen directamente de la API. Incluimos jornada y fecha para
    mostrarlos en la imagen.
    """
    return {
        "id":         match["id"],
        "fecha":      match["utcDate"],
        "estado":     match["status"],
        "jornada":    match.get("matchday"),
        "home": {
            "name":  match["homeTeam"]["shortName"] or match["homeTeam"]["name"],
            "full":  match["homeTeam"]["name"],
            "tla":   match["homeTeam"]["tla"],
        },
        "away": {
            "name":  match["awayTeam"]["shortName"] or match["awayTeam"]["name"],
            "full":  match["awayTeam"]["name"],
            "tla":   match["awayTeam"]["tla"],
        },
        "goles_home": match["score"]["fullTime"]["home"],
        "goles_away": match["score"]["fullTime"]["away"],
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