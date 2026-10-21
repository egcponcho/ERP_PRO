"""Aplicación FastAPI: rutas del núcleo y de los módulos, y la interfaz compilada."""
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.atributos import api as atributos
from app.core.config import settings
from app.modelos import importar_todo
from app.web import errores

importar_todo()

app = FastAPI(title="ERP PRO", version="0.1.0")
errores.registrar(app)


@app.get("/api/salud")
def salud():
    return {"estado": "ok"}


app.include_router(atributos.config)
app.include_router(atributos.referencias)
# Cada módulo nuevo agrega aquí sus rutas: app.include_router(<modulo>.router)


# ---- Interfaz ----------------------------------------------------------------------------
# Con el frontend compilado (frontend/dist), el mismo servidor sirve la interfaz: los archivos
# de /assets y, para cualquier otra ruta que no sea de la API, index.html (la app decide la vista).
DIST = settings.FRONTEND_DIST
if DIST.is_dir() and (DIST / "index.html").is_file():
    if (DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def interfaz(ruta: str):
        if ruta.startswith("api/"):
            return JSONResponse({"mensaje": "Ruta no encontrada.", "codigo": "no_existe", "detalle": None}, status_code=404)
        archivo = (DIST / ruta).resolve()
        if ruta and archivo.is_file() and archivo.is_relative_to(DIST.resolve()):
            return FileResponse(archivo)
        return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-cache"})
else:

    @app.get("/", include_in_schema=False)
    def inicio():
        # Sin interfaz compilada, la raíz lleva a la documentación interactiva de la API
        return RedirectResponse("/docs")
