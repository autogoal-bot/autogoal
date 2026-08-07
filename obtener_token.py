"""
Obtiene el Page Token PERMANENTE de forma automatica y lo verifica.
Pide los datos por consola para no dejarlos en el codigo.
"""

import requests

APP_ID = "2168561603717392"
PAGE_ID = "1249004994962920"

print("=" * 60)
print("GENERADOR DE PAGE TOKEN PERMANENTE - AUTOGOAL")
print("=" * 60)

app_secret = input("\n1. Pega tu APP SECRET (66c819c...): ").strip()
user_token = input("2. Pega tu USER TOKEN de 60 dias (EAAe...): ").strip()

# Paso 1: asegurar que el user token es de larga duracion
print("\n[1/3] Verificando/extendiendo el user token...")
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
    print("ERROR:", data)
    exit()
long_token = data["access_token"]
print(f"    OK. Expira en {data.get('expires_in', 0)} segundos (~60 dias)")

# Paso 2: obtener el Page Token usando el long-lived user token
print("\n[2/3] Obteniendo Page Token...")
r = requests.get(
    f"https://graph.facebook.com/v21.0/{PAGE_ID}",
    params={"fields": "access_token", "access_token": long_token},
    timeout=30,
)
data = r.json()
if "access_token" not in data:
    print("ERROR:", data)
    exit()
page_token = data["access_token"]
print("    OK. Page Token obtenido.")

# Paso 3: verificar que NO caduca (expires_at == 0)
print("\n[3/3] Verificando que es permanente...")
r = requests.get(
    "https://graph.facebook.com/v21.0/debug_token",
    params={"input_token": page_token, "access_token": page_token},
    timeout=30,
)
info = r.json().get("data", {})
tipo = info.get("type")
expira = info.get("expires_at")

print(f"    Tipo: {tipo}")
print(f"    expires_at: {expira}")

print("\n" + "=" * 60)
if tipo == "PAGE" and expira == 0:
    print("EXITO: Token PERMANENTE (tipo PAGE, no caduca)")
    print("=" * 60)
    print("\nCopia este token a tu .env como PAGE_ACCESS_TOKEN:\n")
    print(page_token)
else:
    print("ATENCION: revisa el resultado, puede no ser permanente.")
    print("=" * 60)
    print("\nToken obtenido (usar con cuidado):\n")
    print(page_token)
print()
