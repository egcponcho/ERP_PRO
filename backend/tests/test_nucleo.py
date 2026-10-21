"""Núcleo: aislamiento entre organizaciones, concurrencia optimista, errores de
negocio, migraciones y la interfaz compilada."""
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core import integridad, organizacion
from app.core.errores import ErrorNegocio
from tests.conftest import URL_PRUEBAS, C, Cliente, nuevo_atributo
from tests.demo import Ficha

BACKEND = Path(__file__).parent.parent


def test_organizaciones_aisladas(fabrica, cli):
    color = nuevo_atributo(cli, "color", "opcion", ["ROJO", "AZUL"])
    kg = cli.id_de("unidades", "KG")
    otra = Cliente(fabrica, org=2)  # desde aquí las peticiones son de la organización 2
    assert otra.ok("get", f"{C}/atributos") == []
    otra.ok("get", f"{C}/atributos/{color}", 404)
    otra.ok("patch", f"{C}/atributos/{color}", 404, json={"nombre": "x"})
    # No puede usar la configuración de la otra organización
    r = otra.ok("post", f"{C}/atributos", 422, json={"codigo": "peso", "nombre": "Peso", "tipo_dato": "decimal",
                                                     "magnitud_id": otra.id_de("magnitudes", "MASA"), "unidad_defecto_id": kg})
    assert r["codigo"] == "validacion"
    # El mismo código puede existir en cada organización
    assert nuevo_atributo(otra, "color", "texto") != color


def test_no_guarda_registros_de_otra_organizacion(fabrica):
    with fabrica() as db:
        organizacion.fijar(db, 1)
        f = Ficha(codigo="F1", nombre="Uno")
        integridad.guardar(db, f)
        db.commit()
        organizacion.fijar(db, 2)
        assert db.scalars(select(Ficha)).all() == []
        f.nombre = "Cambio desde la organización 2"
        with pytest.raises(ErrorNegocio) as e:
            db.flush()
        assert e.value.codigo == "otra_organizacion"


def test_concurrencia_optimista(fabrica):
    with fabrica() as a, fabrica() as b:
        for s in (a, b):
            organizacion.fijar(s, 1)
        integridad.guardar(a, Ficha(codigo="F1", nombre="Uno"))
        a.commit()
        fa, fb = a.scalar(select(Ficha)), b.scalar(select(Ficha))
        fa.nombre = "Primera edición"
        a.commit()
        assert fa.version == 2
        fb.nombre = "Edición atrasada"
        from sqlalchemy.orm.exc import StaleDataError

        with pytest.raises(StaleDataError):
            b.commit()


def test_concurrencia_responde_409():
    from fastapi.testclient import TestClient
    from sqlalchemy.orm.exc import StaleDataError

    from app.main import app

    @app.get("/api/_prueba_conflicto")
    def _conflicto():
        raise StaleDataError("cambió")

    try:
        r = TestClient(app).get("/api/_prueba_conflicto")
        assert r.status_code == 409 and r.json()["codigo"] == "conflicto"
    finally:
        app.router.routes = [x for x in app.router.routes if getattr(x, "path", "") != "/api/_prueba_conflicto"]


def test_unicidad_y_errores_de_negocio(cli):
    nuevo_atributo(cli, "color", "texto")
    r = cli.ok("post", f"{C}/atributos", 409, json={"codigo": "color", "nombre": "Otro", "tipo_dato": "texto"})
    assert r["codigo"] == "conflicto" and r["mensaje"] == "Ya existe un atributo con ese código."
    r = cli.ok("post", f"{C}/atributos", 422, json={"codigo": "Mal Código", "nombre": "x", "tipo_dato": "texto"})
    assert r["codigo"] == "validacion" and r["detalle"][0]["campo"] == "codigo"
    cli.ok("get", f"{C}/atributos/999", 404)


def test_migraciones_coinciden_con_los_modelos(tmp_path):
    """upgrade, check y downgrade en un proceso aparte: sin las tablas de ejemplo de las pruebas."""
    url = URL_PRUEBAS or f"sqlite:///{tmp_path / 'm.db'}"
    codigo = f"""
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from app.core.db import crear_motor
url = {url!r}
if url.startswith("postgresql"):  # parte de una base vacía
    with crear_motor(url).begin() as con:
        con.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
cfg = Config("alembic.ini")
cfg.attributes["url"] = url
command.upgrade(cfg, "head")
command.check(cfg)  # falla si los modelos tienen cambios sin migración
command.downgrade(cfg, "base")
"""
    r = subprocess.run([sys.executable, "-c", codigo], cwd=BACKEND, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_url_de_la_plataforma_usa_psycopg():
    from app.core.config import url_base_datos

    assert url_base_datos("postgres://u:c@h/b") == "postgresql+psycopg://u:c@h/b"
    assert url_base_datos("postgresql://u:c@h/b") == "postgresql+psycopg://u:c@h/b"
    assert url_base_datos("postgresql+psycopg://u@h/b") == "postgresql+psycopg://u@h/b"
    assert url_base_datos("sqlite:///./erp_pro.db") == "sqlite:///./erp_pro.db"


def test_sirve_la_interfaz_compilada(tmp_path, monkeypatch):
    """Con FRONTEND_DIST, las rutas de la app devuelven index.html y la API sigue respondiendo JSON."""
    import importlib

    from fastapi.testclient import TestClient

    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<div id=app></div>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    monkeypatch.setenv("FRONTEND_DIST", str(tmp_path))
    import app.core.config as config
    import app.main as principal

    importlib.reload(config)
    try:
        importlib.reload(principal)
        c = TestClient(principal.app)
        assert "id=app" in c.get("/cualquier/ruta").text
        assert c.get("/assets/app.js").text == "console.log(1)"
        assert c.get("/favicon.svg").text == "<svg/>"
        assert "root:" not in c.get("/../../etc/passwd").text
        assert c.get("/api/no-existe").status_code == 404
        assert c.get("/api/salud").json() == {"estado": "ok"}
    finally:
        monkeypatch.delenv("FRONTEND_DIST")
        importlib.reload(config)
        importlib.reload(principal)
