# Usa una imagen oficial de Python como base
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala las dependencias del scraper
# CORRECCIÓN: Ahora busca el archivo "requirements.txt"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script del scraper
COPY scraper_vilaseca.py .

# Comando para ejecutar el script, que se ejecutará 24/7
# y se auto-programará.
#
# NOTA IMPORTANTE: Asegúrate de configurar las siguientes variables de entorno en Easypanel:
# - SUPABASE_HOST
# - SUPABASE_PASSWORD
# - SCRAPE_INTERVAL_HOURS
CMD ["python", "scraper_vilaseca.py"]
