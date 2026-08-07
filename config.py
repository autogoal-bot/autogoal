"""
Configuracion global del proyecto LaLiga Bot.
Carga variables sensibles desde .env y define constantes.
"""

import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# --- football-data.org (API principal de datos) ---
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
LALIGA_CODE = "PD"  # Primera Division (LaLiga) en football-data.org

# --- Instagram Graph API ---
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
INSTAGRAM_API_BASE = "https://graph.facebook.com/v21.0"

# --- ImgBB (hosting de imagenes) ---
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"

# --- La Liga ---
LALIGA_ID = 140
SEASON = 2026

# --- Validacion al arrancar ---
if not FOOTBALL_DATA_TOKEN:
    raise ValueError(
        "No se encontro FOOTBALL_DATA_TOKEN. Revisa el archivo .env."
    )

if not PAGE_ACCESS_TOKEN:
    raise ValueError(
        "No se encontro PAGE_ACCESS_TOKEN. Revisa el archivo .env."
    )

if not INSTAGRAM_ACCOUNT_ID:
    raise ValueError(
        "No se encontro INSTAGRAM_ACCOUNT_ID. Revisa el archivo .env."
    )

if not IMGBB_API_KEY:
    raise ValueError(
        "No se encontro IMGBB_API_KEY. Revisa el archivo .env."
    )