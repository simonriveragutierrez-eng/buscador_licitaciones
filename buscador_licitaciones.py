def buscar_licitaciones():
    log("Consultando API de Mercado Publico...")
    if not TICKET or TICKET == "pendiente":
        log("ERROR: MERCADO_PUBLICO_TICKET no configurado.")
        return []

    # Fecha fija (mientras se resuelve el ticket real)
    # Esta fecha tiene 435 licitaciones comprobadas
    fecha = "07102025"

    url = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha=" + fecha + "&ticket=" + TICKET

    # Reintentos porque la API a veces falla con 500
    for intento in range(1, 4):
        try:
            log("Intento " + str(intento) + " - consultando fecha " + fecha + "...")
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

    log("ERROR: La API fallo despues de 3 intentos.")
    return []
