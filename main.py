from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import schedule
import time
import threading
import os

# Importamos la función lógica desde tu script generador
from sql_generator import get_sql_from_text

# Importamos la lógica y configuración del scraper
from scraper_vilaseca import scrape_job, SCRAPE_INTERVAL_HOURS

# --- Configuración del Servidor de API y Scraper en segundo plano ---

def run_scheduler():
    """Función que se ejecutará en un hilo para manejar las tareas programadas."""
    
    # Programar la ejecución periódica del scraper
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(scrape_job)
    print(f"✅ Scraper programado para ejecutarse cada {SCRAPE_INTERVAL_HOURS} horas.")
    
    # Ejecutar el scraper una vez al inicio (opcional, pero bueno para un arranque rápido)
    print("🔄 Ejecutando el primer scraping al iniciar...")
    scrape_job()
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Comprobar cada 60 segundos si hay tareas pendientes

# Creamos la instancia de la aplicación FastAPI
app = FastAPI(
    title="Chatbot Services API",
    description="API para servicios de chatbot, incluyendo Text-to-SQL y scraping de noticias.",
    version="1.1.0",
)

@app.on_event("startup")
def startup_event():
    """Al iniciar la API, lanza el scheduler del scraper en un hilo de fondo."""
    print("🚀 La API está iniciando...")
    # Validar variables de entorno críticas para el scraper
    if not all([os.environ.get("SUPABASE_HOST"), os.environ.get("SUPABASE_PASSWORD")]):
        print("❌ ADVERTENCIA: Faltan las variables de entorno de Supabase. El scraper NO se ejecutará.")
    else:
        # Crear y empezar el hilo para el scheduler
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        print("🧵 Hilo del scraper iniciado en segundo plano.")

# --- Endpoints de la API ---

# Definimos un modelo para los datos de entrada de la petición.
class QueryRequest(BaseModel):
    query: str

# Definimos un modelo para la respuesta
class SQLResponse(BaseModel):
    sql_query: str
    error: str | None = None

@app.get("/", summary="Endpoint de estado")
def read_root():
    """Endpoint de estado para verificar que la API está funcionando."""
    return {"status": "API y scraper en ejecución"}

@app.post("/generate-sql", response_model=SQLResponse, summary="Genera una consulta SQL desde texto")
async def generate_sql_endpoint(request: QueryRequest):
    """
    Recibe una pregunta de usuario y la convierte en una consulta SQL.
    """
    print(f"Recibida petición para generar SQL para la consulta: '{request.query}'")
    
    # Llama a la función que contiene la lógica del LLM
    sql_query = get_sql_from_text(request.query)
    
    if sql_query.startswith("ERROR"):
        print(f"Error al generar SQL: {sql_query}")
        return {"sql_query": "", "error": sql_query}
    
    print(f"SQL generado exitosamente: {sql_query}")
    return {"sql_query": sql_query, "error": None}

# Esta sección permite ejecutar el servidor directamente para pruebas locales.
if __name__ == "__main__":
    # Cargar variables de entorno desde un archivo .env para pruebas locales (opcional)
    # from dotenv import load_dotenv
    # load_dotenv()
    print("Iniciando servidor en modo de desarrollo local...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)