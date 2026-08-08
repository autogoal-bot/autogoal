"""
Modulo de publicacion en Instagram.

Flujo en 3 pasos:
1. Subir la imagen a ImgBB para obtener una URL publica
2. Crear un "contenedor de media" en Instagram con esa URL
3. Publicar el contenedor en el feed
"""

import time
import requests
from config import (
    PAGE_ACCESS_TOKEN,
    INSTAGRAM_ACCOUNT_ID,
    INSTAGRAM_API_BASE,
    IMGBB_API_KEY,
    IMGBB_UPLOAD_URL,
)


def subir_imagen_a_imgbb(ruta_imagen):
    """
    Sube una imagen local a ImgBB y devuelve la URL publica.
    ImgBB es necesario porque Instagram Graph API no acepta uploads directos:
    exige una URL publica accesible desde internet.
    """
    print(f"[1/3] Subiendo imagen a ImgBB: {ruta_imagen}")

    with open(ruta_imagen, "rb") as archivo:
        respuesta = requests.post(
            IMGBB_UPLOAD_URL,
            params={"key": IMGBB_API_KEY},
            files={"image": archivo},
            timeout=30,
        )

    if respuesta.status_code != 200:
        raise Exception(f"ImgBB fallo: {respuesta.status_code} - {respuesta.text}")

    datos = respuesta.json()
    url_publica = datos["data"]["url"]
    print(f"      Imagen subida. URL: {url_publica}")
    return url_publica


def crear_contenedor_instagram(url_imagen, texto):
    """
    Paso 2 del flujo de Instagram: crear un "media container".
    Es como preparar el post pero sin publicarlo aun.
    Devuelve un ID que usaremos en el paso 3.
    """
    print(f"[2/3] Creando contenedor en Instagram...")

    endpoint = f"{INSTAGRAM_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "image_url": url_imagen,
        "caption": texto,
        "access_token": PAGE_ACCESS_TOKEN,
    }

    respuesta = requests.post(endpoint, data=payload, timeout=30)

    if respuesta.status_code != 200:
        raise Exception(f"Instagram fallo creando contenedor: {respuesta.text}")

    contenedor_id = respuesta.json()["id"]
    print(f"      Contenedor creado. ID: {contenedor_id}")
    return contenedor_id


def publicar_contenedor(contenedor_id):
    """
    Paso 3 del flujo: publicar el contenedor en el feed.
    Instagram procesa la imagen en su servidor antes de dejarnos publicar,
    por eso esperamos 5 segundos como margen de seguridad.
    """
    print(f"[3/3] Esperando 5 segundos y publicando...")
    time.sleep(5)

    endpoint = f"{INSTAGRAM_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    payload = {
        "creation_id": contenedor_id,
        "access_token": PAGE_ACCESS_TOKEN,
    }

    respuesta = requests.post(endpoint, data=payload, timeout=30)

    if respuesta.status_code != 200:
        raise Exception(f"Instagram fallo publicando: {respuesta.text}")

    post_id = respuesta.json()["id"]
    print(f"      Post publicado. ID: {post_id}")
    return post_id


def publicar_en_instagram(ruta_imagen, texto):
    """
    Funcion principal: orquesta los 3 pasos.
    Recibe la ruta de una imagen local y el texto del caption.
    Devuelve el ID del post publicado.
    """
    url_imagen = subir_imagen_a_imgbb(ruta_imagen)
    contenedor_id = crear_contenedor_instagram(url_imagen, texto)
    post_id = publicar_contenedor(contenedor_id)
    print(f"\n✅ Publicacion completa. Post ID: {post_id}")
    return post_id

def crear_contenedor_story(url_imagen):
    """
    Paso 2 para Stories: crear el contenedor con media_type="STORIES".
    Diferencias con el feed:
    - media_type="STORIES" es obligatorio
    - Sin caption: Instagram lo ignora en las Stories
    """
    print(f"[2/3] Creando contenedor STORY en Instagram...")

    endpoint = f"{INSTAGRAM_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "image_url": url_imagen,
        "media_type": "STORIES",
        "access_token": PAGE_ACCESS_TOKEN,
    }

    respuesta = requests.post(endpoint, data=payload, timeout=30)

    if respuesta.status_code != 200:
        raise Exception(f"Instagram fallo creando contenedor STORY: {respuesta.text}")

    contenedor_id = respuesta.json()["id"]
    print(f"      Contenedor STORY creado. ID: {contenedor_id}")
    return contenedor_id


def publicar_story(ruta_imagen):
    """
    Publica una imagen vertical (1080x1920 JPEG) como Story.
    Reutiliza la subida a ImgBB y la publicacion del feed.
    Las Stories NO llevan caption.
    Devuelve el ID de la Story publicada.
    """
    url_imagen = subir_imagen_a_imgbb(ruta_imagen)
    contenedor_id = crear_contenedor_story(url_imagen)
    story_id = publicar_contenedor(contenedor_id)
    print(f"\n✅ Story publicada. Story ID: {story_id}")
    return story_id

# --- Bloque de prueba ---
# Este bloque solo se ejecuta si corremos publicar.py directamente,
# no cuando otro archivo lo importe.
if __name__ == "__main__":
    ruta_test = "imagenes_generadas/partido_999999.png"
    texto_test = "Prueba tecnica de Autogoal. Ignorar."
    publicar_en_instagram(ruta_test, texto_test)