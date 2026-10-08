# -*- coding: utf-8 -*-
import os
import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

TICKET = os.environ.get("MERCADO_PUBLICO_TICKET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_SENDER = "simonriveragutierrez@gmail.com"
EMAIL_RECIPIENT = "simonriveragutierrez@gmail.com"

PERFIL = "Geomatica, Topografia, Cartografia, SIG, ArcGIS, Civil 3D, Fotogrametria, Teledeteccion"

PALABRAS_CLAVE = [
    "topografia", "topografía", "geomatica", "geomática",
    "cartografia", "cartografía", "sig", "gis", "arcgis",
    "fotogrametria", "fotogrametría", "teledeteccion", "teledetección",
    "catastro", "geodesia", "levantamiento", "drone", "dron",
    "autodesk", "civil 3d", "lidar", "satelital",
    "mdt", "ortomosaico", "curvas de nivel", "igm", "igac"
]


def log(msg):
    print("[" + time.strftime("%H:%M:%S") + "] " + msg)


def buscar_licitaciones():
    log("Consultando API de Mercado Publico...")
    if not TICKET or TICKET == "pendiente":
        log("ERROR: MERCADO_PUBLICO_TICKET no configurado.")
        return []

    fecha = "07102025"
    url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha=" + fecha + "&ticket=" + TICKET

    for intento in range(1, 4):
        try:
            log("Intento " + str(intento) + " - fecha " + fecha + "...")
            response = requests.get(url, timeout=30)
            if response.status_code == 500:
                log("  API 500. Reintentando en 5s...")
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


def filtrar_con_ia(licitaciones):
    log("Filtrando " + str(len(licitaciones)) + " candidatas con Gemini...")
    if not GEMINI_API_KEY or GEMINI_API_KEY == "prueba123":
        log("ADVERTENCIA: Sin GEMINI_API_KEY. Se devuelven todas.")
        return licitaciones
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        log("ERROR Gemini: " + str(e))
        return licitaciones

    filtradas = []
    for lic in licitaciones:
        titulo = lic.get("Nombre", "Sin titulo")
        prompt = (
            "Actua como experto en licitaciones de ingenieria en Chile.\n"
            "Evalua si es relevante para una empresa con perfil: " + PERFIL + "\n\n"
            "Titulo: " + titulo + "\n\n"
            'Responde unicamente "SI" o "NO".'
        )
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            if "SI" in response.text.upper():
                log("  ACEPTADA: " + titulo)
                filtradas.append(lic)
            else:
                log("  Descartada: " + titulo)
        except Exception as e:
            log("  Error: " + str(e))
            filtradas.append(lic)
        time.sleep(13)
    return filtradas


def enviar_correo(licitaciones):
    if not licitaciones:
        log("No hay licitaciones relevantes para enviar.")
        return
    if not EMAIL_PASSWORD:
        log("ADVERTENCIA: Sin EMAIL_PASSWORD. No se envia correo.")
        return
    log("Enviando correo con " + str(len(licitaciones)) + " licitaciones...")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = "Licitaciones relevantes: " + str(len(licitaciones))

    cuerpo = "<h2>Licitaciones de Geomatica/Topografia</h2><ul>"
    for lic in licitaciones:
        codigo = lic.get("CodigoExterno", "")
        link = "https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idLicitacion=" + codigo
        cuerpo += "<li><strong>" + lic.get("Nombre", "") + "</strong> (" + codigo + ") - <a href='" + link + "'>Ver detalle</a></li>"
    cuerpo += "</ul>"
    msg.attach(MIMEText(cuerpo, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        log("Correo enviado exitosamente.")
    except Exception as e:
        log("ERROR al enviar correo: " + str(e))


def main():
    log("=== AGENTE BUSCADOR DE LICITACIONES ===")
    licitaciones = buscar_licitaciones()
    if not licitaciones:
        log("Sin licitaciones para procesar.")
        return

    candidatas = []
    for lic in licitaciones:
        titulo_lower = lic.get("Nombre", "").lower()
        for palabra in PALABRAS_CLAVE:
            if palabra in titulo_lower:
                candidatas.append(lic)
                break

    log("Candidatas con palabras clave: " + str(len(candidatas)) + " de " + str(len(licitaciones)))

    if not candidatas:
        log("No hay licitaciones con palabras clave relevantes.")
        return

    relevantes = filtrar_con_ia(candidatas)
    enviar_correo(relevantes)


if __name__ == "__main__":
    main()
