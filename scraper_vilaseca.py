import os
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import sql
from urllib.parse import urljoin
import logging
from datetime import datetime, timezone
import time
import schedule

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuración de Supabase ---
SUPABASE_HOST = os.environ.get("SUPABASE_HOST")
SUPABASE_PASSWORD = os.environ.get("SUPABASE_PASSWORD")
SUPABASE_USER = os.environ.get("SUPABASE_USER", "postgres")
SUPABASE_DB = os.environ.get("SUPABASE_DB", "postgres")
SUPABASE_PORT = os.environ.get("SUPABASE_PORT", "5432")

# Configuración de intervalos (en horas)
SCRAPE_INTERVAL_HOURS = int(os.environ.get("SCRAPE_INTERVAL_HOURS", "6"))

def get_db_connection():
    """Establece y devuelve una conexión a Supabase."""
    try:
        conn = psycopg2.connect(
            dbname=SUPABASE_DB,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            sslmode='require'
        )
        logging.info("Conexión a Supabase establecida con éxito.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Error al conectar a Supabase: {e}")
        logging.error("Verifica que:")
        logging.error("1. SUPABASE_HOST tenga el formato: db.xxxxxxxxxxxxx.supabase.co")
        logging.error("2. SUPABASE_PASSWORD sea correcta")
        logging.error("3. Tu IP esté permitida en Supabase (o desactiva protección IP)")
        return None

def create_table_if_not_exists(cursor):
    """Crea la tabla news_articles si no existe."""
    create_table_command = """
    CREATE TABLE IF NOT EXISTS news_articles (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        url VARCHAR(2048) UNIQUE NOT NULL,
        content TEXT,
        images TEXT,
        source VARCHAR(255),
        date VARCHAR(255),
        scraped_at TIMESTAMP WITH TIME ZONE
    );
    """
    try:
        cursor.execute(create_table_command)
        logging.info("Tabla 'news_articles' asegurada.")
    except psycopg2.Error as e:
        logging.error(f"Error al crear la tabla: {e}")
        raise

def article_exists(cursor, url):
    """Verifica si un artículo con la misma URL ya existe en la base de datos."""
    query = "SELECT 1 FROM news_articles WHERE url = %s"
    cursor.execute(query, (url,))
    return cursor.fetchone() is not None

def insert_article(cursor, article):
    """Inserta un nuevo artículo en la base de datos."""
    insert_query = sql.SQL("""
        INSERT INTO news_articles (title, url, content, images, source, date, scraped_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """)
    images_str = str(article.get('images', []))
    
    cursor.execute(insert_query, (
        article.get('title'),
        article.get('url'),
        article.get('content'),
        images_str,
        article.get('source'),
        article.get('date'),
        article.get('scraped_at')
    ))

def scrape_diari_tarragona():
    """Scrapea la página principal del Diari de Tarragona para encontrar noticias de Vila-seca."""
    main_url = "https://www.diaridetarragona.com/"
    articles_found = []
    try:
        logging.info(f"Accediendo a {main_url}")
        response = requests.get(main_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for article_tag in soup.find_all('article'):
            title_tag = article_tag.find(['h2', 'h3'], class_='c-article__title')
            if title_tag and title_tag.find('a'):
                title = title_tag.text.strip()
                if 'vila-seca' in title.lower() or 'vilaseca' in title.lower():
                    link = title_tag.find('a')['href']
                    full_url = urljoin(main_url, link)
                    articles_found.append({
                        'url': full_url,
                        'source': 'Diari de Tarragona'
                    })
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al acceder a {main_url}: {e}")
    
    logging.info(f"Encontrados {len(articles_found)} artículos potenciales en Diari de Tarragona.")
    return articles_found

def scrape_vilaseca_cat():
    """Scrapea la página de noticias del Ayuntamiento de Vila-seca."""
    main_url = "https://vila-seca.cat/es/actualidad-ayuntamiento/noticias-actualidad"
    articles_found = []
    try:
        logging.info(f"Accediendo a {main_url}")
        response = requests.get(main_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for item in soup.select("div.article-list-text"):
            link_tag = item.select_one("h4 a")
            if link_tag and link_tag.has_attr('href'):
                full_url = urljoin(main_url, link_tag['href'])
                articles_found.append({
                    'url': full_url,
                    'source': 'Ayuntamiento Vila-seca'
                })
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al acceder a {main_url}: {e}")

    logging.info(f"Encontrados {len(articles_found)} artículos potenciales en la web del Ayuntamiento.")
    return articles_found

def get_article_details(article_url, source):
    """Obtiene y parsea el contenido de una página de artículo específica."""
    try:
        logging.info(f"Procesando artículo: {article_url}")
        response = requests.get(article_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title, content, images = None, None, []
        base_url = os.path.dirname(article_url)

        if source == 'Diari de Tarragona':
            title_tag = soup.select_one('h1.c-detail__title')
            content_elements = soup.select('div.c-detail__body p.paragraph')
            image_elements = soup.select('figure.c-detail__media img, div.c-detail__body img')
            title = title_tag.text.strip() if title_tag else ''
            content = '\n\n'.join(p.text.strip() for p in content_elements)
            for img in image_elements:
                src = img.get('src')
                if src: images.append(urljoin(base_url, src))
        
        elif source == 'Ayuntamiento Vila-seca':
            title_tag = soup.select_one('.page-header h2, h1.item-title, h1')
            content_elements = soup.select('div[itemprop="articleBody"] p')
            image_elements = soup.select('div[itemprop="articleBody"] img')
            title = title_tag.text.strip() if title_tag else ''
            content = '\n\n'.join(p.text.strip() for p in content_elements)
            for img in image_elements:
                src = img.get('src')
                if src: images.append(urljoin(base_url, src))

        if title and content:
            return {'title': title, 'content': content, 'images': images}

    except requests.exceptions.RequestException as e:
        logging.error(f"Fallo al obtener detalles de {article_url}: {e}")
    except Exception as e:
        logging.error(f"Fallo al parsear {article_url}: {e}")

    return None

def scrape_job():
    """Función principal que orquesta el proceso de scraping y guardado."""
    logging.info("=" * 80)
    logging.info("--- Iniciando el proceso de scraping ---")
    logging.info(f"Fecha y hora: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logging.info("=" * 80)
    
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos. Se reintentará en el próximo ciclo.")
        return
        
    try:
        with conn.cursor() as cursor:
            create_table_if_not_exists(cursor)
            
            articles_to_fetch = scrape_diari_tarragona() + scrape_vilaseca_cat()
            if not articles_to_fetch:
                logging.info("No se encontraron artículos para procesar.")
                return

            new_articles_count = 0
            for article_summary in articles_to_fetch:
                url = article_summary['url']
                if article_exists(cursor, url):
                    logging.info(f"Artículo ya existente, omitiendo: {url}")
                    continue

                details = get_article_details(url, article_summary['source'])
                if details:
                    full_article = {**article_summary, **details}
                    full_article['scraped_at'] = datetime.now(timezone.utc)
                    insert_article(cursor, full_article)
                    new_articles_count += 1
                    logging.info(f"Artículo nuevo guardado: \"{details['title']}\"")
                else:
                    logging.warning(f"No se pudieron obtener los detalles completos de: {url}")
            
            conn.commit()
            logging.info("=" * 80)
            logging.info(f"--- Proceso de scraping finalizado. {new_articles_count} artículos nuevos guardados. ---")
            logging.info(f"Próxima ejecución en {SCRAPE_INTERVAL_HOURS} horas")
            logging.info("=" * 80)

    except psycopg2.Error as e:
        logging.error(f"Error de base de datos durante la operación: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logging.error(f"Error inesperado durante el scraping: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("Conexión a la base de datos cerrada.")

def main():
    """Punto de entrada principal con scheduler."""
    logging.info("🚀 Iniciando servicio de scraping de noticias de Vila-seca")
    logging.info(f"📅 Intervalo de scraping configurado: cada {SCRAPE_INTERVAL_HOURS} horas")
    
    # Validar variables de entorno críticas
    if not all([SUPABASE_HOST, SUPABASE_PASSWORD]):
        logging.error("❌ ERROR: Variables de entorno SUPABASE_HOST y SUPABASE_PASSWORD son obligatorias")
        logging.error("El servicio no puede continuar sin estas variables.")
        return
    
    # Ejecutar scraping inmediatamente al iniciar
    logging.info("🔄 Ejecutando primer scraping...")
    scrape_job()
    
    # Programar ejecuciones periódicas
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(scrape_job)
    
    logging.info(f"✅ Scheduler iniciado correctamente")
    logging.info(f"⏰ Próxima ejecución programada en {SCRAPE_INTERVAL_HOURS} horas")
    logging.info("🔄 El servicio está corriendo... (Presiona Ctrl+C para detener)")
    
    # Mantener el servicio corriendo
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto si hay tareas pendientes
        except KeyboardInterrupt:
            logging.info("\n👋 Servicio detenido por el usuario")
            break
        except Exception as e:
            logging.error(f"❌ Error en el loop principal: {e}")
            logging.info("⏳ Esperando 60 segundos antes de continuar...")
            time.sleep(60)

if __name__ == "__main__":
    main()
