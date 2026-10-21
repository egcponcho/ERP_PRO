"""Configuración por variables de entorno."""
import os
from pathlib import Path


def url_base_datos(url: str) -> str:
    """La URL con el controlador psycopg 3: las plataformas (Render, Railway…) la dan
    como postgres:// o postgresql://, que SQLAlchemy asociaría a psycopg2."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


class Config:
    DATABASE_URL: str = url_base_datos(os.environ.get("DATABASE_URL", "sqlite:///./erp_pro.db"))
    # Organización con la que trabaja la API mientras no exista el módulo de acceso
    ORGANIZACION_POR_DEFECTO: int = int(os.environ.get("ORGANIZACION_POR_DEFECTO", "1"))
    # Interfaz compilada (npm run build); si no existe, la API funciona sola
    FRONTEND_DIST: Path = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parents[3] / "frontend" / "dist"))


settings = Config()
