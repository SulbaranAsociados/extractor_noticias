# Usa una imagen oficial de Python como base
FROM python:3.10-slim

# Instala cron
RUN apt-get update && apt-get -y install cron

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script de scraping al contenedor
COPY scraper.py .

# Crea el archivo de configuración para cron
RUN echo "0 */6 * * * root python3 /app/scraper.py >> /var/log/cron.log 2>&1" > /etc/cron.d/scrape-cron

# Da permisos de ejecución al archivo de cron
RUN chmod 0644 /etc/cron.d/scrape-cron

# Crea un archivo de log para que cron pueda escribir en él y dale permisos
RUN touch /var/log/cron.log
RUN chmod 0644 /var/log/cron.log

# El comando para iniciar cron y mantener el contenedor corriendo
# Inicia el servicio cron en segundo plano y luego muestra el log en tiempo real
CMD cron && tail -f /var/log/cron.log
