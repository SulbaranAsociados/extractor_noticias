dockerfileFROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY scraper_vilaseca.py .

# Ejecutar el script
CMD ["python", "scraper_vilaseca.py"]
```
