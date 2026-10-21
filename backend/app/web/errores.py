"""Errores como respuesta de la API: siempre {mensaje, codigo, detalle}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm.exc import StaleDataError

from app.core.errores import ErrorNegocio


def _error_negocio(_request: Request, exc: ErrorNegocio):
    return JSONResponse({"mensaje": exc.mensaje, "codigo": exc.codigo, "detalle": exc.detalle}, status_code=exc.status)


def _concurrencia(_request: Request, _exc: StaleDataError):
    return JSONResponse({"mensaje": "Otra persona modificó el registro mientras tanto: vuelva a cargarlo.",
                         "codigo": "conflicto", "detalle": None}, status_code=409)


def _validacion(_request: Request, exc: RequestValidationError):
    detalle = [{"campo": ".".join(str(x) for x in err["loc"][1:]), "mensaje": err["msg"]} for err in exc.errors()]
    return JSONResponse({"mensaje": "Revise los datos.", "codigo": "validacion", "detalle": detalle}, status_code=422)


def registrar(app: FastAPI) -> None:
    app.add_exception_handler(ErrorNegocio, _error_negocio)
    app.add_exception_handler(StaleDataError, _concurrencia)
    app.add_exception_handler(RequestValidationError, _validacion)
