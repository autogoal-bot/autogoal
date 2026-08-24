from api_client import get_partidos_jornada, get_clasificacion
from partidos import procesar_partido as _p
import imagen, story, inspect

# Buscar el partido de Osasuna pendiente
crudo = None
for j in (1, 2):
    for p in get_partidos_jornada(j):
        n = (p['homeTeam']['name'] + p['awayTeam']['name']).lower()
        if 'osasuna' in n and p.get('status') != 'FINISHED':
            crudo = p
            break
    if crudo:
        break

if not crudo:
    raise SystemExit("No hay partido de Osasuna pendiente. Revisa el paso 1.")

print(f"Partido: {crudo['homeTeam']['name']} vs {crudo['awayTeam']['name']}")
print(f"Estado:  {crudo['status']}")
print(f"Fecha:   {crudo['utcDate']}")
print()
print("Funciones disponibles en partidos.py:")
for nombre, obj in inspect.getmembers(__import__('partidos'), inspect.isfunction):
    print("  ", nombre, inspect.signature(obj))
