name: Agente Buscador de Licitaciones

on:
  schedule:
    # Se ejecuta de lunes a viernes a las 12:00 UTC (9:00 AM en Chile)
    - cron: '0 12 * * 1-5'
  workflow_dispatch: # Permite ejecutarlo manualmente con un botón

jobs:
  run-agent:
    runs-on: ubuntu-latest
    steps:
    - name: Clonar repositorio
      uses: actions/checkout@v4

    - name: Configurar Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Instalar dependencias
      run: pip install -r requirements.txt

    - name: Ejecutar agente buscador
      env:
        # Inyecta los secretos guardados en GitHub
        MERCADO_PUBLICO_TICKET: ${{ secrets.MERCADO_PUBLICO_TICKET }}
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
      run: python buscador_licitaciones.py
