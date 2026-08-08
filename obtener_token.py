"""
Obtiene el Page Token PERMANENTE, lo VERIFICA y lo ESCRIBE en .env
automaticamente. Elimina el copy-paste manual (causa de los tokens malos).
Solo escribe si el token es type=PAGE y expires_at=0.
"""

import re
import sys
import requests
from pathlib import Path

APP_ID = "2168561603717392"
PAGE_ID = "1249004994962920"
ARCHIVO_ENV = Path(".env")

print("=" * 60)
print("GENERADOR DE PAGE TOKEN PERMANENTE - AUTOGOAL (auto-escribe .env)")
print("=" * 60)

app_secret = input("\n1. Pega tu APP SECRET: ").strip()
user_token = input("2. Pega tu USER TOKEN del Explorer (EAA...): ").strip()

# Paso 1: extender el user token a larga duracion
print("\n[1/4] Extendiendo el user token...")
r = requests.get(
    "https://graph.facebook.com/v21.0/oauth/access_token",
    params={
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": app_secret,
        "fb_exchange_token": user_token,
    },
    timeout=30,
)
data = r.json()
if "access_token" not in data:
    print("ERROR extendiendo:", data)
    sys.exit(1)
long_token = data["access_token"]
print("    OK.")

# Paso 2: obtener el Page Token
print("\n[2/4] Obteniendo Page Token...")
r = requests.get(
    f"https://graph.facebook.com/v21.0/{PAGE_ID}",
    params={"fields": "access_token", "access_token": long_token},
    timeout=30,
)
data = r.json()
if "access_token" not in data:
    print("ERROR obteniendo Page Token:", data)
    sys.exit(1)
page_token = data["access_token"]
print("    OK.")

# Paso 3: verificar que es PAGE y permanente
print("\n[3/4] Verificando que es PAGE y expires_at=0...")
r = requests.get(
    "https://graph.facebook.com/v21.0/debug_token",
    params={"input_token": page_token, "access_token": page_token},
    timeout=30,
)
info = r.json().get("data", {})
tipo = info.get("type")
expira = info.get("expires_at")
print(f"    Tipo: {tipo} | expires_at: {expira}")

if not (tipo == "PAGE" and expira == 0):
    print("\n" + "=" * 60)
    print("ABORTADO: el token NO es permanente. NO se ha tocado el .env.")
    print("Repite generando un USER TOKEN nuevo en el Explorer.")
    print("=" * 60)
    sys.exit(1)

# Paso 4: escribir en .env (reemplazando solo la linea PAGE_ACCESS_TOKEN)
print("\n[4/4] Escribiendo el token en .env...")
contenido = ARCHIVO_ENV.read_text(encoding="utf-8")
nueva_linea = f"PAGE_ACCESS_TOKEN={page_token}"
if re.search(r"^PAGE_ACCESS_TOKEN=.*$", contenido, flags=re.MULTILINE):
    contenido = re.sub(r"^PAGE_ACCESS_TOKEN=.*$", nueva_linea, contenido, flags=re.MULTILINE)
else:
    contenido = contenido.rstrip() + "\n" + nueva_linea + "\n"
ARCHIVO_ENV.write_text(contenido, encoding="utf-8")

# Re-leer y confirmar
releido = ARCHIVO_ENV.read_text(encoding="utf-8")
m = re.search(r"^PAGE_ACCESS_TOKEN=(.*)$", releido, flags=re.MULTILINE)
ok_escrito = m and m.group(1).strip() == page_token

print("\n" + "=" * 60)
if ok_escrito:
    print("EXITO: token PERMANENTE (PAGE, expires_at=0) escrito en .env.")
    print("No hace falta copiar nada. Siguiente: actualizar el Secret de GitHub.")
else:
    print("ATENCION: no se pudo confirmar la escritura en .env. Revisa manualmente.")
print("=" * 60)
