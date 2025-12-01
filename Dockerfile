# Usa una imagen oficial de Python como base
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia primero el archivo de requerimientos para aprovechar el caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos los archivos de la aplicación al contenedor
# Esto incluirá main.py, sql_generator.py, scraper_vilaseca.py, etc.
COPY . .

# Expone el puerto en el que se ejecutará la aplicación dentro del contenedor.
# Easypanel redirigirá el tráfico del exterior a este puerto.
EXPOSE 80

# Comando para iniciar el servidor de API con Uvicorn.
# Uvicorn se encargará de ejecutar la aplicación 'app' definida en el archivo 'main.py'.
# La aplicación, a su vez, iniciará el scraper en segundo plano.
#
# NOTA IMPORTANTE: Asegúrate de configurar las siguientes variables de entorno en Easypanel:
# - OPENAI_API_KEY
# - SUPABASE_HOST
# - SUPABASE_PASSWORD
# - SUPABASE_USER (opcional)
# - SUPABASE_DB (opcional)
# - SUPABASE_PORT (opcional)
# - SCRAPE_INTERVAL_HOURS (opcional)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
