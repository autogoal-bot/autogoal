"""
Estadios de los equipos de LaLiga 2026-27.
Dato fijo por equipo (el equipo local juega siempre en su estadio).
Las claves coinciden con el nombre completo de football-data.org.
"""

ESTADIOS = {
    "Real Madrid CF":                  "Santiago Bernabeu",
    "FC Barcelona":                    "Spotify Camp Nou",
    "Club Atletico de Madrid":         "Riyadh Air Metropolitano",
    "Athletic Club":                   "San Mames",
    "Real Sociedad de Futbol":         "Reale Arena",
    "Real Betis Balompie":             "Benito Villamarin",
    "Villarreal CF":                   "Estadio de la Ceramica",
    "Sevilla FC":                      "Ramon Sanchez-Pizjuan",
    "Valencia CF":                     "Mestalla",
    "Getafe CF":                       "Coliseum",
    "RC Celta de Vigo":                "Balaidos",
    "CA Osasuna":                      "El Sadar",
    "Rayo Vallecano de Madrid":        "Estadio de Vallecas",
    "Deportivo Alaves":                "Mendizorroza",
    "RCD Espanyol de Barcelona":       "RCDE Stadium",
    "Elche CF":                        "Martinez Valero",
    "Levante UD":                      "Ciutat de Valencia",
    "Malaga CF":                       "La Rosaleda",
    "RC Deportivo La Coruna":          "Riazor",
    "Real Racing Club de Santander":   "El Sardinero",
}


def get_estadio(nombre_equipo):
    """Devuelve el estadio del equipo local, o cadena vacia si no se encuentra."""
    return ESTADIOS.get(nombre_equipo, "")
