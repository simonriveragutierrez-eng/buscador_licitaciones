# -*- coding: utf-8 -*-
"""
Agente Buscador de Licitaciones Publicas de Geomatica y Topografia.
Consulta la API de Mercado Publico de Chile, filtra con Gemini y notifica por correo.
"""

import os
import time
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai


# ============================================================
# CONFIGURACION
# ============================================================

TICKET = os.environ.get("MERCADO_PUBLICO_TICKET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

EMAIL_SENDER = "simonriveragutierrez@gmail.com"
EMAIL_RECIPIENT = "simonriveragutierrez@gmail.com"

FECHA_CONSULTA = "07102025"

PERFIL = (
    "Geomatica, Topografia, Cartografia, SIG, ArcGIS, Civil 3D, "
    "Fotogrametria, Teledeteccion, Geodesia, Catastro"
)

PALABRAS_CLAVE = [
    "topografia", "topografía",
    "geomatica", "geomática",
    "cartografia", "cartografía",
    "sig", "gis", "arcgis",
    "fotogrametria", "fotogrametría",
    "teledeteccion", "teledetección",
    "catastro", "geodesia",
    "levantamiento", "drone", "dron",
    "autodesk", "civil 3d",
    "lidar", "satelital",
    "mdt", "ortomosaico",
    "curvas de nivel",
    "igm", "igac",
]


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def log(msg):
    print("[" + time.strftime("%H:%M:%S") + "] " + msg)


def buscar_licitaciones():
    """Consulta la API de Mercado Publico y devuelve las licitaciones."""
    log("Consultando API de Mercado Publico...")

    if not TICKET or TICKET == "pendiente":
        log("ERROR: MERCADO_PUBLICO_TICKET no configurado.")
        return []

    url = (
        "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
        "?fecha=" + FECHA_CONSULTA + "&ticket=" + TICKET
    )

    for intento in range(1, 4):
        try:
            log("Intento " + str(intento) + " - fecha " + FECHA_CONSULTA + "...")
            response = requests.get(url, timeout=30)

            if response.status_code == 500:
                log("  API devolvio 500. Reintentando en 5s...")
                time.sleep(5)
                continue

            response.raise_for_status()
            data = response.json()
            licitaciones = data.get("Listado", [])
            log("Se encontraron " + str(len(licitaciones)) + " licitaciones.")
            return licitaciones

        except Exception as e:
            log("  Intento " + str(intento) + " fallo: " + str(e))
            if intento < 3:
                time.sleep(5)

    log("ERROR: API fallo despues de 3 intentos.")
    return []


def prefiltrar_por_palabras_clave(licitaciones):
    """Filtra por palabras clave antes de llamar a Gemini (ahorra cuota)."""
    log("Aplicando prefiltro por palabras clave...")

    candidatas = []
    for lic in licitaciones:
        titulo_lower = lic.get("Nombre", "").lower()
        for palabra in PALABRAS_CLAVE:
            if palabra in titulo_lower:
                candidatas.append(lic)
                break

    log("Candidatas relevantes: " + str(len(candidatas)) + " de " + str(len(licitaciones)))
    return candidatas


def filtrar_con_ia(licitaciones):
    """Filtra con Gemini para confirmar relevancia. Reintenta si el modelo esta saturado."""
    log("Filtrando " + str(len(licitaciones)) + " candidatas con Gemini...")

    if not GEMINI_API_KEY or GEMINI_API_KEY == "prueba123":
        log("ADVERTENCIA: Sin GEMINI_API_KEY valida. Se devuelven todas.")
        return licitaciones

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        log("ERROR al inicializar Gemini: " + str(e))
        return licitaciones

    filtradas = []

    for lic in licitaciones:
        titulo = lic.get("Nombre", "Sin titulo")

        prompt = (
            "Actua como experto en licitaciones de ingenieria en Chile.\n"
            "Evalua si la siguiente licitacion es relevante para una empresa "
            "con este perfil: " + PERFIL + "\n\n"
            "Titulo: " + titulo + "\n\n"
            'Responde unicamente con "SI" o "NO".'
        )

        respuesta_ok = False
        for intento in range(1, 4):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                )

                # Extraer el texto de forma segura
                texto = ""
                if response and hasattr(response, "text") and response.text:
                    texto = response.text.upper()

                if "SI" in texto:
                    log("  ACEPTADA: " + titulo)
                    filtradas.append(lic)
                else:
                    log("  Descartada: " + titulo)

                respuesta_ok = True
                break

            except Exception as e:
                error_str = str(e)
                # Si es 503 (saturado), reintentar
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    log("  Modelo saturado (503). Reintento " + str(intento) + "/3 en 20s...")
                    time.sleep(20)
                else:
                    log("  Error al filtrar: " + error_str)
                    # Error no recuperable: aceptar la oferta para no perderla
                    filtradas.append(lic)
                    respuesta_ok = True
                    break

        if not respuesta_ok:
            log("  Fallaron los 3 reintentos. Se acepta por precaucion: " + titulo)
            filtradas.append(lic)

        time.sleep(15)

    return filtradas


def enviar_correo(licitaciones):
    """Envia un correo con las licitaciones relevantes."""
    if not licitaciones:
        log("No hay licitaciones relevantes para enviar.")
        return

    if not EMAIL_PASSWORD:
        log("ADVERTENCIA: Sin EMAIL_PASSWORD. No se envia correo.")
        return

    log("Enviando correo con " + str(len(licitaciones)) + " licitaciones...")

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    msg["Subject"] = "Licitaciones relevantes: " + str(len(licitaciones))

    cuerpo = "<h2>Licitaciones de Geomatica y Topografia</h2><ul>"
    for lic in licitaciones:
        codigo = lic.get("CodigoExterno", "")
        nombre = lic.get("Nombre", "Sin titulo")
        link = (
            "https://www.mercadopublico.cl/Procurement/Modules/RFB/"
            "DetailsAcquisition.aspx?idLicitacion=" + codigo
        )
        cuerpo += "<li><strong>" + nombre + "</strong> (" + codigo + ") - "
        cuerpo += "<a href='" + link + "'>Ver detalle</a></li>"
    cuerpo += "</ul>"

    msg.attach(MIMEText(cuerpo, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        log("Correo enviado exitosamente.")
    except Exception as e:
        log("ERROR al enviar correo: " + str(e))


# ============================================================
# FUNCION PRINCIPAL
# ============================================================

def main():
    log("=== AGENTE BUSCADOR DE LICITACIONES ===")

    licitaciones = buscar_licitaciones()
    if not licitaciones:
        log("Sin licitaciones para procesar.")
        return

    candidatas = prefiltrar_por_palabras_clave(licitaciones)
    if not candidatas:
        log("No hay licitaciones con palabras clave relevantes.")
        return

    relevantes = filtrar_con_ia(candidatas)
    enviar_correo(relevantes)

    log("=== PROCESO COMPLETADO ===")


if __name__ == "__main__":
    main()
