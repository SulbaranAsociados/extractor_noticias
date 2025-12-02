# Usa una imagen oficial de Python como base
FROM python:3.12-slim
 
# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app
# Instala las dependencias del scraper
COPY requirements-scraper.txt .
RUN pip install --no-cache-dir -r requirements-scraper.txt

# Copia el script del scraper
COPY scraper_vilaseca.py .
 
# Comando para ejecutar el script.
# Se ejecutará una vez y luego el contenedor terminará.
# Ideal para un Cron Job.
CMD ["python", "scraper_vilaseca.py"]
