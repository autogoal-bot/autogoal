"""
Envoltorio de main.py para GitHub Actions.

Motivo: el cron de Actions es "best effort". Con carga alta GitHub
descarta ejecuciones enteras — se han visto huecos de 7 horas. Un cron
cada 10 min que corre 3 veces al dia no sirve para publicar al instante.

Solucion: una sola ejecucion que se queda viva haciendo polling interno.
Aunque GitHub retrase el arranque, dentro del bucle se publica a los
~2 minutos del pitido final.

27 min: el cron lanza uno cada 30, asi el bucle muere solo antes de
que llegue el siguiente. Si en vez de eso lo cancela el concurrency,
puede cortarse entre publicar en Instagram y guardar el registro,
y eso es exactamente lo que causaba los duplicados.
"""

import time
import traceback
from datetime import datetime, timezone

import main

DURACION_MIN = 27
INTERVALO_SEG = 120


def _log(msg):
    ahora = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ahora} UTC] {msg}", flush=True)



def _git(*args):
    """Ejecuta git en silencio. Devuelve True si fue bien."""
    import subprocess
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        _log(f"git {' '.join(args)} -> {r.stderr.strip()[:120]}")
    return r.returncode == 0


def _sincronizar():
    """Trae el registro mas reciente antes de decidir que publicar."""
    _git("config", "user.name", "autogoal-bot")
    _git("config", "user.email", "bot@autogoal.es")
    _git("stash", "push", "-q", "--", "publicados.json")
    _git("pull", "--rebase", "-q", "origin", "main")
    _git("stash", "pop", "-q")


def _persistir():
    """
    Sube el registro INMEDIATAMENTE tras publicar. Si esperamos al final
    del job, una cancelacion o un fallo pierde los IDs y el siguiente
    bucle republica lo mismo: eso causo los duplicados.
    """
    import subprocess
    _git("add", "-f", "publicados.json")
    hay_cambios = subprocess.run(
        ["git", "diff", "--staged", "--quiet"]).returncode != 0
    if not hay_cambios:
        return
    _git("commit", "-q", "-m", "Actualizar registro de publicados [skip ci]")
    if not _git("push", "-q"):
        _git("pull", "--rebase", "-q", "--autostash")
        _git("push", "-q")
    _log("Registro sincronizado con el repo.")


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
            _sincronizar()
            main.main()
            _persistir()
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
