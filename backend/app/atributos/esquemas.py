"""Contratos de entrada de la configuración de atributos (pydantic).

Cada catálogo tiene su modelo de alta; el de edición es el mismo con todos
los campos opcionales (`parcial`).
"""
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

Codigo = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9][A-Za-z0-9._\-]*$")


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


def parcial(modelo: type[BaseModel]) -> type[BaseModel]:
    """El mismo modelo con todos sus campos opcionales (para PATCH)."""
    campos = {n: (f.annotation | None, None) for n, f in modelo.model_fields.items()}
    return create_model(f"{modelo.__name__}Edicion", __base__=Entrada, **campos)


class MagnitudEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    activa: bool = True


class UnidadEntrada(Entrada):
    codigo: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9][A-Za-z0-9._\-/]*$")
    nombre: str = Field(min_length=1, max_length=100)
    simbolo: str | None = Field(default=None, max_length=20)
    magnitud_id: int
    factor: Decimal = Field(default=Decimal(1), gt=0)
    decimales: int = Field(default=0, ge=0, le=10)
    activa: bool = True


class GrupoAtributoEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = 0
    activo: bool = True


class OpcionEntrada(Entrada):
    codigo: str = Codigo
    nombre: str = Field(min_length=1, max_length=100)
    orden: int = 0
    activa: bool = True


class AtributoEntrada(Entrada):
    codigo: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_]*$")
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    tipo_dato: Literal["texto", "entero", "decimal", "booleano", "fecha", "opcion", "opciones", "referencia"]
    magnitud_id: int | None = None
    unidad_defecto_id: int | None = None
    entidad_referencia: str | None = None
    reglas: dict[str, Any] = Field(default_factory=dict)
    grupo_id: int | None = None
    orden: int = 0
    activo: bool = True


class AtributoAlta(AtributoEntrada):
    opciones: list[OpcionEntrada] = Field(default_factory=list)
