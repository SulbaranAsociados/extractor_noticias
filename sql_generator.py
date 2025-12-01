import os
import openai

# Asegúrate de tener tu clave de API de OpenAI como variable de entorno
# openai.api_key = os.getenv("OPENAI_API_KEY")

def get_sql_from_text(user_query: str) -> str:
    """
    Usa un LLM para convertir una pregunta en lenguaje natural a una consulta SQL.
    """
    
    # El prompt maestro que definimos en el Paso 1
    prompt_template = f"""
Eres un asistente experto que convierte preguntas de usuarios en consultas SQL para una base de datos PostgreSQL.

### CONTEXTO
La base de datos tiene la siguiente tabla:
CREATE TABLE telefonos_de_interes (
    id SERIAL PRIMARY KEY,
    nombre_entidad TEXT NOT NULL,
    telefono TEXT,
    direccion TEXT
);

### REGLAS
1.  Solo puedes generar consultas `SELECT`. NUNCA generes `UPDATE`, `DELETE` o `INSERT`.
2.  Busca siempre en la columna `nombre_entidad`.
3.  Usa el operador `ILIKE` con comodines (`%`) para hacer la búsqueda flexible e insensible a mayúsculas/minúsculas.
4.  Si no puedes generar una consulta razonable, devuelve "ERROR".

### EJEMPLOS
-   Usuario: "telefono ayuntamiento"
    SQL: SELECT telefono FROM telefonos_de_interes WHERE nombre_entidad ILIKE '%ayuntamiento%';
-   Usuario: "quiero comunicarme con el alcalde"
    SQL: SELECT telefono FROM telefonos_de_interes WHERE nombre_entidad ILIKE '%ayuntamiento%';
-   Usuario: "CAP"
    SQL: SELECT telefono FROM telefonos_de_interes WHERE nombre_entidad ILIKE '%cap%';
-   Usuario: "policia"
    SQL: SELECT telefono FROM telefonos_de_interes WHERE nombre_entidad ILIKE '%policia%';

### TAREA
Convierte la siguiente pregunta del usuario en una consulta SQL.

Usuario: "{user_query}"
SQL:
"""

    try:
        # Asumiendo que usas la versión más reciente de la librería de OpenAI
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini", # O el modelo que prefieras
            messages=[
                {"role": "system", "content": "Genera solo el código SQL solicitado."},
                {"role": "user", "content": prompt_template}
            ],
            temperature=0,
            max_tokens=150
        )
        
        sql_query = response.choices[0].message.content.strip()

        # Validación de seguridad básica
        if sql_query.upper().startswith("SELECT"):
            return sql_query
        else:
            return "ERROR: La consulta generada no es un SELECT válido."

    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    # Esto permite ejecutar el script desde la línea de comandos para probar
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        sql = get_sql_from_text(query)
        print(sql)
