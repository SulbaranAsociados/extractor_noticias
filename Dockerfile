# Usa una imagen oficial de Python como base, preferiblemente la misma versión que tu entorno local
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
# Asegúrate de que requirements.txt contenga 'schedule' y 'psycopg2-binary'
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script de scraping principal al contenedor
COPY scraper_vilaseca.py .

# Comando para ejecutar el script principal.
# El script ya tiene su propio scheduler interno.
# NOTA IMPORTANTE: Asegúrate de configurar las siguientes variables de entorno en Easypanel:
# - SUPABASE_HOST
# - SUPABASE_PASSWORD
# - SUPABASE_USER (opcional, por defecto 'postgres')
# - SUPABASE_DB (opcional, por defecto 'postgres')
# - SUPABASE_PORT (opcional, por defecto '5432')
# - SCRAPE_INTERVAL_HOURS (opcional, por defecto '6')
CMD ["python", "scraper_vilaseca.py"]
