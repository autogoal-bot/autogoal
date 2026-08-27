"""
Envoltorio de main.py para GitHub Actions.

Motivo: el cron de Actions es "best effort". Con carga alta GitHub
descarta ejecuciones enteras — se han visto huecos de 7 horas. Un cron
cada 10 min que corre 3 veces al dia no sirve para publicar al instante.

Solucion: una sola ejecucion que se queda viva haciendo polling interno.
Aunque GitHub retrase el arranque, dentro del bucle se publica a los
~2 minutos del pitido final.

Los workflows tienen limite de 6h; 50 min deja margen de sobra.
"""

import time
import traceback
from datetime import datetime, timezone

import main

DURACION_MIN = 50
INTERVALO_SEG = 120


def _log(msg):
    ahora = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ahora} UTC] {msg}", flush=True)


def ejecutar():
    fin = time.time() + DURACION_MIN * 60
    vuelta = 0
    fallos = 0

    _log(f"Bucle iniciado. Duracion {DURACION_MIN} min, "
         f"comprobacion cada {INTERVALO_SEG // 60} min.")

    while time.time() < fin:
        vuelta += 1
        _log(f"--- Vuelta {vuelta} ---")

        try:
            main.main()
            fallos = 0
        except Exception:
            fallos += 1
            _log(f"ERROR en la vuelta {vuelta} (fallo consecutivo {fallos}):")
            traceback.print_exc()

            # Tres fallos seguidos = algo roto de verdad (token, API caida).
            # Seguir insistiendo 50 min solo gasta cuota y ensucia el log.
            if fallos >= 3:
                _log("3 fallos consecutivos. Abortando el bucle.")
                raise

        restante = fin - time.time()
        if restante <= 0:
            break
        time.sleep(min(INTERVALO_SEG, restante))

    _log(f"Bucle terminado tras {vuelta} vueltas.")


if __name__ == "__main__":
    ejecutar()
