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


def log(msg):
    print("[" + time.strftime("%H:%M:%S") + "] " + msg)


def buscar_licitaciones():
    log("Consultando API de Mercado Publico...")
    if not TICKET or TICKET == "pendiente":
        log("ERROR: MERCADO_PUBLICO_TICKET no configurado.")
        return []
    fecha_hoy = time.strftime("%d%m%Y")
    url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha=" + fecha_hoy + "&ticket=" + TICKET
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        licitaciones = data.get("Listado", [])
        log("Se encontraron " + str(len(licitaciones)) + " licitaciones.")
        return licitaciones
    except Exception as e:
        log("ERROR: " + str(e))
        return []


def filtrar_con_ia(licitaciones):
    log("Filtrando con Gemini...")
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
        log("No hay licitaciones relevantes.")
        return
    if not EMAIL_PASSWORD:
        log("ADVERTENCIA: Sin EMAIL_PASSWORD.")
        return
    log("Enviando correo...")
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
        log("Correo enviado.")
    except Exception as e:
        log("ERROR correo: " + str(e))


def main():
    log("=== AGENTE BUSCADOR DE LICITACIONES ===")
    licitaciones = buscar_licitaciones()
    if licitaciones:
        relevantes = filtrar_con_ia(licitaciones)
        enviar_correo(relevantes)
    else:
        log("Sin licitaciones para procesar.")


if __name__ == "__main__":
    main()
