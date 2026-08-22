"""
Logica de negocio sobre partidos.
Filtra, ordena y detecta partidos recien terminados.

Adaptado al formato de football-data.org.
"""

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
            "name":  _nombre_corto(match["homeTeam"]),
            "full":  match["homeTeam"]["name"],
            "tla":   match["homeTeam"]["tla"],
        },
        "away": {
            "name":  _nombre_corto(match["awayTeam"]),
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