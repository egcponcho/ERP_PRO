import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.atributos.instalacion import cargar_base
from app.core import organizacion
from app.core.db import crear_motor
from app.core.modelo import Base
from app.core.organizacion import Organizacion
from app.main import app
from app.web.dependencias import obtener_db
from tests import demo  # noqa: F401  (las tablas del módulo de ejemplo)

# Con TEST_DATABASE_URL (p. ej. postgresql+psycopg://erp@localhost/erp_test) las pruebas corren en esa
# base, que se vacía en cada prueba; sin ella, en SQLite en memoria.
URL_PRUEBAS = os.environ.get("TEST_DATABASE_URL")
C = "/api/atributos/config"


@pytest.fixture
def fabrica():
    motor = crear_motor(URL_PRUEBAS) if URL_PRUEBAS else crear_motor("sqlite://", poolclass=StaticPool)
    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    fabrica = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)
    with fabrica() as db:
        db.add_all([Organizacion(id=1, codigo="A", nombre="Empresa A"), Organizacion(id=2, codigo="B", nombre="Empresa B")])
        db.commit()
        for org in (1, 2):
            organizacion.fijar(db, org)
            cargar_base(db)
            db.commit()
    yield fabrica
    motor.dispose()


@pytest.fixture
def db(fabrica):
    """Sesión de la organización 1, para probar los servicios sin pasar por la API."""
    with fabrica() as s:
        organizacion.fijar(s, 1)
        yield s


class Cliente(TestClient):
    """Cliente de prueba que trabaja en una organización y revisa el código de respuesta."""

    def __init__(self, fabrica, org: int = 1):
        self.org = org

        def db():
            s = fabrica()
            organizacion.fijar(s, self.org)
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[obtener_db] = db
        super().__init__(app)

    def ok(self, metodo: str, url: str, esperado: int | None = None, **kw):
        r = self.request(metodo, url, **kw)
        codigo = esperado or {"post": 201, "delete": 204}.get(metodo.lower(), 200)
        assert r.status_code == codigo, f"{metodo} {url} → {r.status_code}: {r.text}"
        return r.json() if r.content else None

    def id_de(self, catalogo: str, codigo: str) -> int:
        return next(x["id"] for x in self.ok("get", f"{C}/{catalogo}") if x["codigo"] == codigo)


@pytest.fixture
def cli(fabrica):
    c = Cliente(fabrica)
    yield c
    app.dependency_overrides.clear()


def nuevo_atributo(cli: Cliente, codigo: str, tipo_dato: str, opciones=(), **kw) -> int:
    datos = {"codigo": codigo, "nombre": codigo.replace("_", " ").capitalize(), "tipo_dato": tipo_dato, **kw,
             "opciones": [{"codigo": o, "nombre": o.capitalize()} for o in opciones]}
    return cli.ok("post", f"{C}/atributos", json=datos)["id"]
