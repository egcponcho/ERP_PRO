"""Motor de atributos: configuración, validación de cada tipo de dato, valores
guardados en la tabla de un módulo, herencia de plantillas y referencias."""
import pytest
from sqlalchemy import select

from app.atributos import esquema, valores
from app.atributos.modelos import Atributo
from app.core import integridad
from tests.conftest import C, nuevo_atributo
from tests.demo import AsignacionFicha, Ficha, TipoFicha, ValorFicha


def _atributo(db, id_: int) -> Atributo:
    return db.get(Atributo, id_)


def _guardar_valor(db, ficha: Ficha, a: Atributo, entrada) -> ValorFicha:
    fila = next((v for v in ficha.valores if v.atributo_id == a.id), None) or ValorFicha(atributo=a, ficha=ficha)
    valores.aplicar(fila, valores.convertir(db, a, entrada))
    integridad.guardar(db, fila)
    return fila


def test_configuracion_de_atributos(cli):
    masa = cli.id_de("magnitudes", "MASA")
    peso = nuevo_atributo(cli, "peso", "decimal", magnitud_id=masa, unidad_defecto_id=cli.id_de("unidades", "KG"),
                          reglas={"minimo": 0, "maximo": 50})
    a = cli.ok("get", f"{C}/atributos/{peso}")
    assert a["unidad_defecto"] == "KG" and a["reglas"] == {"minimo": 0, "maximo": 50}
    # Reglas que no corresponden al tipo de dato
    cli.ok("post", f"{C}/atributos", 422, json={"codigo": "x", "nombre": "X", "tipo_dato": "texto", "reglas": {"maximo": 3}})
    # La magnitud solo en números; la unidad por defecto de la misma magnitud
    cli.ok("post", f"{C}/atributos", 422, json={"codigo": "y", "nombre": "Y", "tipo_dato": "texto", "magnitud_id": masa})
    cli.ok("post", f"{C}/atributos", 422, json={"codigo": "z", "nombre": "Z", "tipo_dato": "decimal", "magnitud_id": masa,
                                               "unidad_defecto_id": cli.id_de("unidades", "L")})
    # Opciones
    color = nuevo_atributo(cli, "color", "opcion", ["ROJO"])
    cli.ok("post", f"{C}/atributos/{color}/opciones", json={"codigo": "AZUL", "nombre": "Azul"})
    cli.ok("post", f"{C}/atributos/{color}/opciones", 409, json={"codigo": "AZUL", "nombre": "Otro azul"})
    cli.ok("post", f"{C}/atributos/{peso}/opciones", 422, json={"codigo": "A", "nombre": "A"})
    assert [o["codigo"] for o in cli.ok("get", f"{C}/atributos/{color}")["opciones"]] == ["ROJO", "AZUL"]


@pytest.mark.parametrize(("tipo", "kw", "entrada", "leido", "error"), [
    ("texto", {"reglas": {"longitud_max": 5}}, " Cuero ", "Cuero", None),
    ("texto", {"reglas": {"longitud_max": 3}}, "Cuero", None, "es demasiado largo"),
    ("texto", {"reglas": {"patron": "[A-Z]{3}"}}, "abc", None, "no tiene el formato esperado"),
    ("entero", {}, 12, 12, None),
    ("entero", {}, 1.5, None, "debe ser un número entero"),
    ("decimal", {"reglas": {"decimales": 2}}, "2.567", None, "admite hasta 2 decimales"),
    ("decimal", {"reglas": {"minimo": 1}}, 0.5, None, "debe ser al menos 1"),
    ("booleano", {}, "sí", True, None),
    ("booleano", {}, "quizá", None, "debe ser sí o no"),
    ("fecha", {"reglas": {"maximo": "2030-01-01"}}, "2026-10-21", "2026-10-21", None),
    ("fecha", {}, "21/10/2026", None, "debe ser una fecha AAAA-MM-DD"),
])
def test_cada_tipo_de_dato(cli, db, tipo, kw, entrada, leido, error):
    a = _atributo(db, nuevo_atributo(cli, "campo", tipo, **kw))
    if error:
        with pytest.raises(ValueError, match=error):
            valores.convertir(db, a, entrada)
        return
    f = Ficha(codigo="F1", nombre="Uno")
    integridad.guardar(db, f)
    assert valores.leer(_guardar_valor(db, f, a, entrada)) == leido


def test_numero_con_unidad_se_compara_en_la_unidad_de_referencia(cli, db):
    peso = _atributo(db, nuevo_atributo(cli, "peso", "decimal", magnitud_id=cli.id_de("magnitudes", "MASA"),
                                        unidad_defecto_id=cli.id_de("unidades", "KG"), reglas={"maximo": 2}))
    f = Ficha(codigo="F1", nombre="Uno")
    integridad.guardar(db, f)
    fila = _guardar_valor(db, f, peso, {"valor": 500, "unidad": "G"})
    assert valores.leer(fila) == {"valor": 500, "unidad": "G"} and valores.numero(fila.valor_numero_base) == 0.5
    assert valores.texto(fila) == "500 g"
    assert valores.leer(_guardar_valor(db, f, peso, 1.5)) == {"valor": 1.5, "unidad": "KG"}  # unidad por defecto
    with pytest.raises(ValueError, match="como máximo 2"):
        valores.convertir(db, peso, {"valor": 3000, "unidad": "G"})
    with pytest.raises(ValueError, match="no es de la magnitud"):
        valores.convertir(db, peso, {"valor": 1, "unidad": "L"})


def test_opciones_se_guardan_en_la_tabla_del_modulo(cli, db):
    a = _atributo(db, nuevo_atributo(cli, "materiales", "opciones", ["ALGODON", "POLIESTER", "LANA"], reglas={"maximo": 2}))
    f = Ficha(codigo="F1", nombre="Uno")
    integridad.guardar(db, f)
    fila = _guardar_valor(db, f, a, ["lana", "ALGODON"])
    db.commit()
    assert valores.leer(fila) == ["ALGODON", "LANA"] and valores.texto(fila) == "Algodon, Lana"
    assert valores.leer(_guardar_valor(db, f, a, ["POLIESTER"])) == ["POLIESTER"]
    with pytest.raises(ValueError, match="como máximo 2"):
        valores.convertir(db, a, ["ALGODON", "POLIESTER", "LANA"])
    with pytest.raises(ValueError, match="no existe"):
        valores.convertir(db, a, ["SEDA"])


def test_atributo_con_valores_no_cambia_de_tipo(cli, db):
    id_ = nuevo_atributo(cli, "talla", "entero")
    f = Ficha(codigo="F1", nombre="Uno")
    integridad.guardar(db, f)
    _guardar_valor(db, f, _atributo(db, id_), 40)
    db.commit()
    r = cli.ok("patch", f"{C}/atributos/{id_}", 409, json={"tipo_dato": "texto"})
    assert r["detalle"] == {"campos": ["tipo_dato"]}
    cli.ok("delete", f"{C}/atributos/{id_}", 409)
    cli.ok("patch", f"{C}/atributos/{id_}", json={"nombre": "Talla EU"})


def test_cambiar_el_factor_de_una_unidad_recalcula_los_valores(cli, db):
    masa = cli.id_de("magnitudes", "MASA")
    lb = cli.id_de("unidades", "LB")
    peso = _atributo(db, nuevo_atributo(cli, "peso", "decimal", magnitud_id=masa, unidad_defecto_id=cli.id_de("unidades", "KG")))
    f = Ficha(codigo="F1", nombre="Uno")
    integridad.guardar(db, f)
    _guardar_valor(db, f, peso, {"valor": 10, "unidad": "LB"})
    db.commit()
    cli.ok("patch", f"{C}/unidades/{lb}", json={"factor": 0.5})
    db.expire_all()
    assert valores.numero(db.scalar(select(ValorFicha.valor_numero_base))) == 5
    cli.ok("patch", f"{C}/unidades/{lb}", 409, json={"magnitud_id": cli.id_de("magnitudes", "VOLUMEN")})


def test_herencia_de_plantillas(cli, db):
    color, talla, suela = (_atributo(db, nuevo_atributo(cli, c, "texto")) for c in ("color", "talla", "suela"))
    calzado = TipoFicha(codigo="CALZADO", nombre="Calzado", asignaciones=[
        AsignacionFicha(atributo=color, orden=1), AsignacionFicha(atributo=talla, orden=2), AsignacionFicha(atributo=suela)])
    deportivo = TipoFicha(codigo="DEPORTIVO", nombre="Deportivo", padre=calzado, asignaciones=[
        AsignacionFicha(atributo=talla, obligatorio=True, orden=2), AsignacionFicha(atributo=suela, oculto=True)])
    integridad.guardar(db, deportivo)
    e = esquema.resolver(deportivo)
    assert [(c.codigo, c.obligatorio, c.heredado_de) for c in e.campos] == [("color", False, "CALZADO"), ("talla", True, None)]
    assert esquema.a_dict(e)["ruta"] == ["CALZADO", "DEPORTIVO"]
    assert esquema.descendientes(db, TipoFicha, calzado.id) == {calzado.id, deportivo.id}


def test_referencias_a_otra_entidad(cli, db):
    for codigo, nombre in (("F1", "Mesa"), ("F2", "Silla"), ("F3", "Mesita")):
        integridad.guardar(db, Ficha(codigo=codigo, nombre=nombre))
    db.commit()
    assert "ficha" in cli.ok("get", "/api/referencias")
    assert [r["nombre"] for r in cli.ok("get", "/api/referencias/ficha", params={"q": "mes"})] == ["Mesa", "Mesita"]
    silla = cli.ok("get", "/api/referencias/ficha", params={"q": "F2"})[0]
    assert silla == {"id": silla["id"], "codigo": "F2", "nombre": "Silla"}
    assert cli.ok("get", f"/api/referencias/ficha/{silla['id']}") == silla
    cli.ok("get", "/api/referencias/ficha/999", 404)
    cli.ok("get", "/api/referencias/nada", 404)

    cli.ok("post", f"{C}/atributos", 422, json={"codigo": "r", "nombre": "R", "tipo_dato": "referencia", "entidad_referencia": "nada"})
    ref = _atributo(db, nuevo_atributo(cli, "relacionada", "referencia", entidad_referencia="ficha"))
    assert valores.convertir(db, ref, silla["id"]).referencia_id == silla["id"]
    with pytest.raises(ValueError, match="no existe en ficha"):
        valores.convertir(db, ref, 999)
