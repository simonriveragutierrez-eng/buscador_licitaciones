import os
import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# --- 1. Configuración de Credenciales ---
TICKET = os.environ.get("MERCADO_PUBLICO_TICKET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_SENDER = "tu_correo@gmail.com"
EMAIL_RECIPIENT = "tu_correo@gmail.com"

# --- 2. Búsqueda de Licitaciones en Mercado Público ---
def buscar_licitaciones():
    print("Buscando licitaciones en Mercado Público...")
    # La API permite filtrar por fecha, estado, etc. Aquí buscamos las del día.
    # El formato de fecha es ddmmaaaa
    fecha_hoy = time.strftime("%d%m%Y")
    url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha={fecha_hoy}&ticket={TICKET}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error si la petición falla
        data = response.json()
        # La API devuelve una lista de licitaciones bajo la clave 'Listado'
        licitaciones = data.get("Listado", [])
        print(f"Se encontraron {len(licitaciones)} licitaciones para hoy.")
        return licitaciones
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de Mercado Público: {e}")
        return []

# --- 3. Filtrado de Licitaciones con IA (Gemini) ---
def filtrar_con_ia(licitaciones):
    print("Filtrando licitaciones con Gemini...")
    if not GEMINI_API_KEY:
        print("Advertencia: No se ha configurado GEMINI_API_KEY. Se devolverán todas las licitaciones.")
        return licitaciones

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Perfil de la empresa para el filtro
    perfil = "Geomática, Topografía, Cartografía, SIG, ArcGIS, Civil 3D, Fotogrametría"
    
    licitaciones_filtradas = []
    for lic in licitaciones:
        titulo = lic.get("Nombre", "Sin título")
        descripcion = lic.get("Descripcion", "")
        
        prompt = f"""
        Actúa como un experto en licitaciones de ingeniería y geociencias en Chile.
        Evalúa si la siguiente licitación es relevante para una empresa con este perfil: {perfil}.
        
        Título: {titulo}
        Descripción: {descripcion}
        
        Responde únicamente con la palabra "SI" si es relevante o "NO" si no lo es.
        """
        
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            if "SI" in response.text.upper():
                print(f"  -> ACEPTADA: {titulo}")
                licitaciones_filtradas.append(lic)
            else:
                print(f"  -> Descartada: {titulo}")
        except Exception as e:
            print(f"  -> Error al filtrar '{titulo}': {e}")
            # En caso de error, es mejor conservar la licitación para no perderla
            licitaciones_filtradas.append(lic)
        
        time.sleep(2) # Pequeña pausa para no exceder el límite de la API de Gemini
        
    return licitaciones_filtradas

# --- 4. Envío de Notificación por Correo (Opcional) ---
def enviar_correo(licitaciones_relevantes):
    if not licitaciones_relevantes or not EMAIL_PASSWORD:
        print("No hay licitaciones relevantes o no se configuró el correo. No se envía notificación.")
        return

    print("Enviando correo con los resultados...")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = f"🔍 {len(licitaciones_relevantes)} Licitaciones Relevantes Detectadas"
    
    cuerpo = "<h2>Licitaciones de Geomática/Topografía Encontradas</h2><ul>"
    for lic in licitaciones_relevantes:
        # Se construye el enlace a la ficha de la licitación
        link = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idLicitacion={lic.get('CodigoExterno')}"
        cuerpo += f"<li><strong>{lic.get('Nombre')}</strong> ({lic.get('CodigoExterno')}) - <a href='{link}'>Ver detalle</a></li>"
    cuerpo += "</ul>"
    
    msg.attach(MIMEText(cuerpo, 'html'))
    
    try:
        # Conexión al servidor SMTP de Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        print("¡Correo enviado exitosamente!")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

# --- 5. Función Principal ---
def main():
    licitaciones_hoy = buscar_licitaciones()
    if licitaciones_hoy:
        relevantes = filtrar_con_ia(licitaciones_hoy)
        enviar_correo(relevantes)
    else:
        print("No se encontraron licitaciones para procesar hoy.")

if __name__ == "__main__":
    main()
