from contextlib import asynccontextmanager
from typing import Annotated

# Se importan pathlib.Path y os para manejar rutas y variables de entorno
from pathlib import Path
import os

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.sql import func

from db.db import Empleado, Proyecto, Tarea
import db.db as db
import db.db_connection as db_connection
from db.db_connection import db_dependency
from datetime import date, timedelta
import uvicorn

# Definición de BASE_DIR para construir rutas absolutas dentro del proyecto
BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Se construye la ruta al script SQL usando BASE_DIR
    archivo_sql = BASE_DIR / "db" / "data.sql"
    try:
        # Abrir y leer el archivo SQL
        with open(archivo_sql, 'r') as file:
            sql_content = file.read()

        # Ejecutar el script SQL usando conexión de bajo nivel para poblar la base
        connection = db_connection.engine.raw_connection()
        try:
            cursor = connection.cursor()
            cursor.executescript(sql_content)
            connection.commit()
        except Exception as e:
            print(f"Error al ejecutar el archivo SQL: {e}")
        finally:
            cursor.close()
            connection.close()

        print("Archivo SQL ejecutado con éxito.")
    except Exception as e:
        print(f"Error al abrir o ejecutar el archivo SQL: {e}")
    finally:
        # Al terminar el lifespan, cerrar el engine para liberar recursos
        db_connection.engine.dispose()

    # Punto de yield para permitir que la aplicación arranque
    yield

# Instanciar la aplicación FastAPI vinculando el manejador de lifespan
app = FastAPI(lifespan=lifespan)

# Crear tablas si no existen, usando la metadata de los modelos ORM
db.Base.metadata.create_all(bind=db_connection.engine)

# Configurar Jinja2Templates apuntando al directorio correcto
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get(
    "/filter-inprogress-tasks",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    description="Retorna el template con las tareas 'In progress' en un rango.",
)
def get_filter_form(request: Request):
    # Renderiza el formulario vacío al hacer GET
    return templates.TemplateResponse(
        "filter_inprogress_tasks.html",
        {"request": request, "start_date": "", "end_date": "", "tasks": []},
    )

@app.post(
    "/filter-inprogress-tasks",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    description="Procesa formulario y muestra las tareas 'In progress' filtradas.",
)
async def post_filter_form(
    request: Request,
    start_date: Annotated[date, Form(...)],
    end_date: Annotated[date, Form(...)],
    db: db_dependency
):
    # Consultar tareas uniendo empleados y proyectos, filtrando por estado
    result = db.query(
        Tarea.descripcion.label("descripcion"),
        Tarea.fecha_inicio.label("fecha_inicio"),
        Tarea.estimado.label("estimado"),
        Empleado.nombre.label("empleado_name"),
        Proyecto.nombre.label("proyecto_name"),
    ).join(Empleado).join(Proyecto).filter(
        Tarea.estado == "In progress",
    ).all()

    # Transformar resultados y aplicar filtro por fechas recibidas
    tasks = []
    for tarea in result:
        fecha_inicio = tarea.fecha_inicio
        fecha_fin = fecha_inicio + timedelta(days=tarea.estimado)
        if fecha_inicio > start_date and fecha_fin < end_date:
            tasks.append({
                "empleado": tarea.empleado_name,
                "descripcion": tarea.descripcion,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "dias_pasados": (end_date - fecha_fin).days,
                "proyecto": tarea.proyecto_name,
            })

    # Renderizar la misma plantilla con los resultados
    return templates.TemplateResponse(
        "filter_inprogress_tasks.html",
        {"request": request, "start_date": start_date, "end_date": end_date, "tasks": tasks},
    )

# # Entry point for the API
# if __name__ == "__main__":
#     # Run the application using uvicorn and enable auto-reload
#     uvicorn.run("main:app", reload=True)

# Entry point para despliegue en plataforma (e.g., Render)
if __name__ == "__main__":
    # Definir host 0.0.0.0 para escuchar todas las interfaces
    host = "0.0.0.0"
    # Leer puerto de la variable de entorno PORT o usar 8000 por defecto
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port)
