from logging.config import fileConfig

from alembic import context
from app.core.config import settings
from app.core.db import crear_motor
from app.core.modelo import Base
from app.modelos import importar_todo

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

importar_todo()
url = context.config.attributes.get("url") or settings.DATABASE_URL


def run_migrations_offline() -> None:
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with crear_motor(url).connect() as conexion:
        context.configure(connection=conexion, target_metadata=Base.metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
