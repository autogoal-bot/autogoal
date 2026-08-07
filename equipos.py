"""
Base de datos de equipos de LaLiga 2026-27 con colores corporativos.
Los colores son aproximaciones libres, no copian marcas registradas.
Los nombres coinciden EXACTAMENTE con los que devuelve football-data.org.
Cada equipo incluye su hashtag popular para las publicaciones.
"""

EQUIPOS = {
    "Real Madrid CF":                  {"abrev": "RMA", "color": "#FEBE10", "texto": "#000000", "hashtag": "RealMadrid"},
    "FC Barcelona":                    {"abrev": "BAR", "color": "#A50044", "texto": "#FFFFFF", "hashtag": "Barcelona"},
    "Club Atletico de Madrid":         {"abrev": "ATM", "color": "#CB3524", "texto": "#FFFFFF", "hashtag": "Atletico"},
    "Athletic Club":                   {"abrev": "ATH", "color": "#EE2523", "texto": "#FFFFFF", "hashtag": "AthleticClub"},
    "Real Sociedad de Futbol":         {"abrev": "RSO", "color": "#0067B1", "texto": "#FFFFFF", "hashtag": "RealSociedad"},
    "Real Betis Balompie":             {"abrev": "BET", "color": "#00954C", "texto": "#FFFFFF", "hashtag": "RealBetis"},
    "Villarreal CF":                   {"abrev": "VIL", "color": "#FFE667", "texto": "#000000", "hashtag": "Villarreal"},
    "Sevilla FC":                      {"abrev": "SEV", "color": "#D80028", "texto": "#FFFFFF", "hashtag": "SevillaFC"},
    "Valencia CF":                     {"abrev": "VAL", "color": "#F18E00", "texto": "#FFFFFF", "hashtag": "Valencia"},
    "Getafe CF":                       {"abrev": "GET", "color": "#005CA9", "texto": "#FFFFFF", "hashtag": "Getafe"},
    "RC Celta de Vigo":                {"abrev": "CEL", "color": "#8AC3EE", "texto": "#000000", "hashtag": "Celta"},
    "CA Osasuna":                      {"abrev": "OSA", "color": "#D91A21", "texto": "#FFFFFF", "hashtag": "Osasuna"},
    "Rayo Vallecano de Madrid":        {"abrev": "RAY", "color": "#E53027", "texto": "#FFFFFF", "hashtag": "RayoVallecano"},
    "Deportivo Alaves":                {"abrev": "ALA", "color": "#1E3A8A", "texto": "#FFFFFF", "hashtag": "Alaves"},
    "RCD Espanyol de Barcelona":       {"abrev": "ESP", "color": "#007FC8", "texto": "#FFFFFF", "hashtag": "Espanyol"},
    "Elche CF":                        {"abrev": "ELC", "color": "#046A38", "texto": "#FFFFFF", "hashtag": "Elche"},
    "Levante UD":                      {"abrev": "LEV", "color": "#9F1D35", "texto": "#FFFFFF", "hashtag": "Levante"},
    "Malaga CF":                       {"abrev": "MAL", "color": "#00A0E1", "texto": "#FFFFFF", "hashtag": "Malaga"},
    "RC Deportivo La Coruna":          {"abrev": "DEP", "color": "#0067B1", "texto": "#FFFFFF", "hashtag": "Deportivo"},
    "Real Racing Club de Santander":   {"abrev": "RAC", "color": "#008000", "texto": "#FFFFFF", "hashtag": "RacingSantander"},
}


def get_equipo(nombre):
    """
    Devuelve la info del equipo. Si no lo encuentra, devuelve valores neutros.
    Busca ignorando tildes para tolerar variaciones de la API.
    """
    import unicodedata
    def sin_tildes(t):
        return "".join(c for c in unicodedata.normalize("NFD", t)
                       if unicodedata.category(c) != "Mn")
    objetivo = sin_tildes(nombre).lower()
    for clave, info in EQUIPOS.items():
        if sin_tildes(clave).lower() == objetivo:
            return info
    return {
        "abrev": nombre[:3].upper(),
        "color": "#333333",
        "texto": "#FFFFFF",
        "hashtag": "".join(c for c in nombre if c.isalnum()),
    }
