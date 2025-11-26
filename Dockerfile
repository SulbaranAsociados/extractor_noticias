# Usa una imagen oficial de Python como base
FROM python:3.10-slim

# Instala cron y procps (necesario para que algunos comandos de shell funcionen bien)
RUN apt-get update && apt-get -y install cron procps

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script de scraping al contenedor
COPY scraper.py .

# Crea el archivo de configuración para cron con la ruta absoluta a Python
RUN echo "0 */6 * * * root /usr/local/bin/python /app/scraper.py >> /var/log/cron.log 2>&1" > /etc/cron.d/scrape-cron

# Da los permisos correctos al archivo de cron
RUN chmod 0644 /etc/cron.d/scrape-cron

# Crea el archivo de log para que cron pueda escribir en él
RUN touch /var/log/cron.log

# El comando final para iniciar cron en primer plano.
# Esto es más robusto y mantiene el contenedor activo.
CMD ["cron", "-f"]
