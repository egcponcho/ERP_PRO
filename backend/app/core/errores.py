"""Error de negocio: un mensaje para el usuario con su código HTTP y, si hace
falta, un detalle estructurado. main.py lo convierte en la respuesta de la API.
"""


class ErrorNegocio(Exception):
    def __init__(self, mensaje: str, status: int = 400, codigo: str = "error", detalle=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status
        self.codigo = codigo
        self.detalle = detalle


def no_existe(que: str) -> ErrorNegocio:
    return ErrorNegocio(f"{que} no existe.", 404, "no_existe")


def invalido(mensaje: str, detalle=None) -> ErrorNegocio:
    return ErrorNegocio(mensaje, 422, "validacion", detalle)


def conflicto(mensaje: str, detalle=None) -> ErrorNegocio:
    return ErrorNegocio(mensaje, 409, "conflicto", detalle)
