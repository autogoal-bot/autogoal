"""
Cliente de football-data.org.
Todas las llamadas a la API pasan por aqui.

Docs: https://www.football-data.org/documentation/quickstart
"""

import requests
from config import FOOTBALL_DATA_TOKEN, FOOTBALL_DATA_BASE, LALIGA_CODE


def _headers():
    """Cabecera de autenticacion que va en cada request."""
    return {"X-Auth-Token": FOOTBALL_DATA_TOKEN}


def get_partidos_por_rango(fecha_desde, fecha_hasta):
    """
    Devuelve los partidos de LaLiga entre dos fechas.
    Fechas en formato 'YYYY-MM-DD'.

    football-data.org usa el endpoint:
    /competitions/PD/matches?dateFrom=...&dateTo=...
    """
    url = f"{FOOTBALL_DATA_BASE}/competitions/{LALIGA_CODE}/matches"
    params = {
        "dateFrom": fecha_desde,
        "dateTo": fecha_hasta,
    }

    response = requests.get(url, headers=_headers(), params=params, timeout=30)
    response.raise_for_status()  # lanza excepcion si algo va mal
    data = response.json()

    # football-data.org devuelve los partidos en la clave "matches"
    return data.get("matches", [])