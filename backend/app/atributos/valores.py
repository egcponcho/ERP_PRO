"""Valores de atributos: validar lo que llega según el tipo de dato y las reglas
del atributo, guardarlo en su columna y devolverlo con la misma forma.

Formas de entrada y salida por tipo de dato:
    texto       "Cuero"
    entero      12
    decimal     2.5                      (sin magnitud)
    entero/decimal con magnitud          {"valor": 2.5, "unidad": "KG"} (o solo el número: unidad por defecto)
    booleano    true
    fecha       "2026-10-20"
    opcion      "ROJO"                   (código de la opción)
    opciones    ["ALGODON", "POLIESTER"]
    referencia  15                       (id del registro de la entidad referenciada)
"""
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.atributos.modelos import TIPOS_DATO, Atributo, AtributoOpcion, UnidadMedida, ValorBase
from app.core import referencias
from app.core.errores import invalido

REGLAS = {
    "texto": {"longitud_min", "longitud_max", "patron"},
    "entero": {"minimo", "maximo"},
    "decimal": {"minimo", "maximo", "decimales"},
    "fecha": {"minimo", "maximo"},
    "opciones": {"minimo", "maximo"},
    "booleano": set(),
    "opcion": set(),
    "referencia": set(),
}
LONGITUD_TEXTO = 1000


def numero(v) -> int | float | None:
    """Un Decimal tal como se entrega en JSON: entero si es exacto."""
    if v is None:
        return None
    d = Decimal(v).normalize()
    return int(d) if d == d.to_integral_value() else float(d)


# ---- Configuración de un atributo -------------------------------------------------------
def validar_definicion(db: Session, a: Atributo) -> None:
    """Revisa que el tipo de dato, la magnitud, la unidad, la entidad y las reglas sean coherentes."""
    if a.tipo_dato not in TIPOS_DATO:
        raise invalido(f"El tipo de dato debe ser uno de: {', '.join(TIPOS_DATO)}.")
    if a.magnitud_id and a.tipo_dato not in ("entero", "decimal"):
        raise invalido("Solo los atributos numéricos pueden tener magnitud.")
    if a.unidad_defecto_id:
        u = db.get(UnidadMedida, a.unidad_defecto_id)
        if not u or not a.magnitud_id or u.magnitud_id != a.magnitud_id:
            raise invalido("La unidad por defecto debe ser de la magnitud del atributo.")
    if a.tipo_dato == "referencia":
        if not a.entidad_referencia or not referencias.existe(a.entidad_referencia):
            raise invalido("Un atributo de referencia necesita una entidad registrada.",
                           {"entidades": referencias.entidades()})
    elif a.entidad_referencia:
        a.entidad_referencia = None
    reglas = dict(a.reglas or {})
    sobran = set(reglas) - REGLAS[a.tipo_dato]
    if sobran:
        raise invalido(f"Reglas no válidas para {a.tipo_dato}: {', '.join(sorted(sobran))}.")
    try:
        if "patron" in reglas:
            re.compile(reglas["patron"])
        for k in ("longitud_min", "longitud_max", "decimales"):
            if k in reglas and (not isinstance(reglas[k], int) or reglas[k] < 0):
                raise ValueError(k)
        if a.tipo_dato in ("entero", "decimal") or a.tipo_dato == "opciones":
            for k in ("minimo", "maximo"):
                if k in reglas:
                    Decimal(str(reglas[k]))
        if a.tipo_dato == "fecha":
            for k in ("minimo", "maximo"):
                if k in reglas:
                    date.fromisoformat(reglas[k])
    except (re.error, ValueError, InvalidOperation, TypeError) as e:
        raise invalido(f"Las reglas del atributo no son válidas ({e}).") from e


def atributo_dict(a: Atributo) -> dict:
    return {
        "id": a.id, "codigo": a.codigo, "nombre": a.nombre, "descripcion": a.descripcion, "tipo_dato": a.tipo_dato,
        "magnitud_id": a.magnitud_id, "unidad_defecto_id": a.unidad_defecto_id,
        "unidad_defecto": a.unidad_defecto.codigo if a.unidad_defecto else None,
        "entidad_referencia": a.entidad_referencia, "reglas": a.reglas or {}, "grupo_id": a.grupo_id,
        "orden": a.orden, "activo": a.activo,
        "opciones": [{"id": o.id, "codigo": o.codigo, "nombre": o.nombre, "orden": o.orden, "activa": o.activa}
                     for o in a.opciones] if a.tipo_dato in ("opcion", "opciones") else [],
    }


# ---- Un valor ---------------------------------------------------------------------------
@dataclass
class Normalizado:
    texto: str | None = None
    numero: Decimal | None = None
    numero_base: Decimal | None = None
    unidad: UnidadMedida | None = None
    booleano: bool | None = None
    fecha: date | None = None
    opcion: AtributoOpcion | None = None
    opciones: list[AtributoOpcion] = field(default_factory=list)
    referencia_id: int | None = None

    def clave(self) -> str:
        """Lo que identifica el valor al comparar variantes (5 kg = 5000 g)."""
        if self.numero_base is not None:
            return f"n:{self.numero_base.normalize()}"
        if self.numero is not None:
            return f"n:{self.numero.normalize()}"
        if self.opcion is not None:
            return f"o:{self.opcion.id}"
        if self.opciones:
            return "m:" + ",".join(map(str, sorted(o.id for o in self.opciones)))
        if self.booleano is not None:
            return f"b:{int(self.booleano)}"
        if self.fecha is not None:
            return f"f:{self.fecha.isoformat()}"
        if self.referencia_id is not None:
            return f"r:{self.referencia_id}"
        return f"t:{(self.texto or '').strip().lower()}"


def vacio(v) -> bool:
    return v is None or v == "" or v == [] or (isinstance(v, dict) and v.get("valor") in (None, ""))


def _decimal(v) -> Decimal:
    if isinstance(v, bool):
        raise ValueError("debe ser un número")
    try:
        d = Decimal(str(v).replace(",", "")) if not isinstance(v, Decimal) else v
    except InvalidOperation as e:
        raise ValueError("debe ser un número") from e
    if not d.is_finite():
        raise ValueError("debe ser un número")
    return d


def convertir(db: Session, a: Atributo, entrada, reglas: dict | None = None) -> Normalizado:
    """El valor validado (ValueError con el motivo si no cumple). `reglas` reemplaza
    las del atributo (los filtros de búsqueda convierten sin reglas)."""
    reglas, t = (a.reglas or {}) if reglas is None else reglas, a.tipo_dato
    if t == "texto":
        if not isinstance(entrada, (str, int, float)) or isinstance(entrada, bool):
            raise ValueError("debe ser un texto")
        s = str(entrada).strip()
        if len(s) > min(reglas.get("longitud_max", LONGITUD_TEXTO), LONGITUD_TEXTO):
            raise ValueError("es demasiado largo")
        if len(s) < reglas.get("longitud_min", 0):
            raise ValueError("es demasiado corto")
        if reglas.get("patron") and not re.fullmatch(reglas["patron"], s):
            raise ValueError("no tiene el formato esperado")
        return Normalizado(texto=s)
    if t in ("entero", "decimal"):
        crudo, unidad_cod = (entrada.get("valor"), entrada.get("unidad")) if isinstance(entrada, dict) else (entrada, None)
        d = _decimal(crudo)
        if t == "entero" and d != d.to_integral_value():
            raise ValueError("debe ser un número entero")
        if "decimales" in reglas and d != d.to_integral_value() and -d.normalize().as_tuple().exponent > reglas["decimales"]:
            raise ValueError(f"admite hasta {reglas['decimales']} decimales")
        n = Normalizado(numero=d)
        factor_regla = Decimal(1)
        if a.magnitud_id:
            if unidad_cod:
                u = db.scalar(select(UnidadMedida).where(UnidadMedida.codigo == unidad_cod))
                if not u or u.magnitud_id != a.magnitud_id:
                    raise ValueError(f"la unidad {unidad_cod} no es de la magnitud del atributo")
            elif a.unidad_defecto:
                u = a.unidad_defecto
            else:
                raise ValueError("indique la unidad")
            n.unidad, n.numero_base = u, d * u.factor
            factor_regla = a.unidad_defecto.factor if a.unidad_defecto else Decimal(1)
        elif unidad_cod:
            raise ValueError("este atributo no lleva unidad")
        comparar = n.numero_base if n.numero_base is not None else d
        if "minimo" in reglas and comparar < Decimal(str(reglas["minimo"])) * factor_regla:
            raise ValueError(f"debe ser al menos {reglas['minimo']}")
        if "maximo" in reglas and comparar > Decimal(str(reglas["maximo"])) * factor_regla:
            raise ValueError(f"debe ser como máximo {reglas['maximo']}")
        return n
    if t == "booleano":
        if isinstance(entrada, bool):
            return Normalizado(booleano=entrada)
        s = str(entrada).strip().lower()
        if s in ("1", "true", "si", "sí", "yes"):
            return Normalizado(booleano=True)
        if s in ("0", "false", "no"):
            return Normalizado(booleano=False)
        raise ValueError("debe ser sí o no")
    if t == "fecha":
        try:
            f = entrada if isinstance(entrada, date) else date.fromisoformat(str(entrada)[:10])
        except ValueError as e:
            raise ValueError("debe ser una fecha AAAA-MM-DD") from e
        if "minimo" in reglas and f < date.fromisoformat(reglas["minimo"]):
            raise ValueError(f"debe ser desde {reglas['minimo']}")
        if "maximo" in reglas and f > date.fromisoformat(reglas["maximo"]):
            raise ValueError(f"debe ser hasta {reglas['maximo']}")
        return Normalizado(fecha=f)
    if t == "opcion":
        return Normalizado(opcion=_opcion(a, entrada))
    if t == "opciones":
        if not isinstance(entrada, list):
            raise ValueError("debe ser una lista de opciones")
        elegidas = list(dict.fromkeys(_opcion(a, x) for x in entrada))
        if "minimo" in reglas and len(elegidas) < int(reglas["minimo"]):
            raise ValueError(f"elija al menos {reglas['minimo']}")
        if "maximo" in reglas and len(elegidas) > int(reglas["maximo"]):
            raise ValueError(f"elija como máximo {reglas['maximo']}")
        return Normalizado(opciones=elegidas)
    if t == "referencia":
        if isinstance(entrada, bool) or not isinstance(entrada, int):
            raise ValueError("debe ser el id de un registro")
        if referencias.obtener(db, a.entidad_referencia, entrada) is None:
            raise ValueError(f"no existe en {a.entidad_referencia}")
        return Normalizado(referencia_id=entrada)
    raise ValueError("tipo de dato desconocido")


def _opcion(a: Atributo, codigo) -> AtributoOpcion:
    o = next((o for o in a.opciones if o.codigo.lower() == str(codigo).strip().lower()), None)
    if o is None:
        raise ValueError(f"la opción {codigo} no existe")
    if not o.activa:
        raise ValueError(f"la opción {codigo} está inactiva")
    return o


def aplicar(fila: ValorBase, n: Normalizado) -> None:
    fila.valor_texto, fila.valor_numero, fila.valor_numero_base = n.texto, n.numero, n.numero_base
    fila.unidad = n.unidad
    fila.unidad_id = n.unidad.id if n.unidad else None
    fila.valor_booleano, fila.valor_fecha, fila.referencia_id = n.booleano, n.fecha, n.referencia_id
    fila.opcion = n.opcion
    fila.opcion_id = n.opcion.id if n.opcion else None
    actuales = {s.opcion.id: s for s in fila.seleccion}
    Seleccion = type(fila).seleccion.property.mapper.class_  # noqa: N806  (la tabla de opciones elegidas del módulo)
    fila.seleccion = [actuales.get(o.id) or Seleccion(opcion=o) for o in n.opciones]


def normalizado_de(fila: ValorBase) -> Normalizado:
    return Normalizado(fila.valor_texto, fila.valor_numero, fila.valor_numero_base, fila.unidad, fila.valor_booleano,
                       fila.valor_fecha, fila.opcion, [s.opcion for s in fila.seleccion], fila.referencia_id)


def leer(fila: ValorBase):
    """El valor con la misma forma con la que se escribe."""
    t = fila.atributo.tipo_dato
    if t in ("entero", "decimal"):
        if fila.atributo.magnitud_id:
            return {"valor": numero(fila.valor_numero), "unidad": fila.unidad.codigo if fila.unidad else None}
        return numero(fila.valor_numero)
    if t == "booleano":
        return fila.valor_booleano
    if t == "fecha":
        return fila.valor_fecha.isoformat() if fila.valor_fecha else None
    if t == "opcion":
        return fila.opcion.codigo if fila.opcion else None
    if t == "opciones":
        return [s.opcion.codigo for s in sorted(fila.seleccion, key=lambda s: (s.opcion.orden, s.opcion.id))]
    if t == "referencia":
        return fila.referencia_id
    return fila.valor_texto


def texto(fila: ValorBase, etiquetas_ref: dict | None = None) -> str:
    """El valor para leerlo (nombres de opciones, número con su unidad)."""
    t = fila.atributo.tipo_dato
    if t in ("entero", "decimal"):
        u = fila.unidad.simbolo or fila.unidad.codigo if fila.unidad else ""
        return f"{numero(fila.valor_numero)} {u}".strip()
    if t == "opcion":
        return fila.opcion.nombre if fila.opcion else ""
    if t == "opciones":
        return ", ".join(s.opcion.nombre for s in sorted(fila.seleccion, key=lambda s: (s.opcion.orden, s.opcion.id)))
    if t == "booleano":
        return "Sí" if fila.valor_booleano else "No"
    if t == "referencia":
        return (etiquetas_ref or {}).get(fila.referencia_id, str(fila.referencia_id))
    v = leer(fila)
    return "" if v is None else str(v)
