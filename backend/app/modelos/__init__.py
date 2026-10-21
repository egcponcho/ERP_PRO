"""Punto único que importa los modelos de todos los módulos (para Alembic y el arranque)."""


def importar_todo() -> None:
    from app.atributos import modelos  # noqa: F401
    from app.core import organizacion  # noqa: F401
    # Cada módulo nuevo agrega aquí su línea: from app.modulos.<modulo> import modelos
