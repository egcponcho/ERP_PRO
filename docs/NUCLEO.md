# Cómo construir un módulo sobre el núcleo

El núcleo no sabe nada de ningún rubro. Un módulo nuevo (clientes, inventario,
ventas…) vive en `backend/app/modulos/<modulo>/` y usa estas piezas. El ejemplo
completo y probado está en `backend/tests/demo.py`.

## 1. Modelos

```python
from app.core.modelo import Base, ConTiempos, ConVersion
from app.core.organizacion import DeOrganizacion

class Cliente(DeOrganizacion, ConTiempos, ConVersion, Base):
    __tablename__ = "clientes"
    __table_args__ = (UniqueConstraint("organizacion_id", "codigo"),)
    ...
```

- `DeOrganizacion`: agrega `organizacion_id`. Toda consulta del ORM se limita a la
  organización de la sesión, y un registro nuevo la toma solo. Un id de otra
  organización simplemente «no existe» (404).
- `ConTiempos`: `creado_en` y `actualizado_en`.
- `ConVersion`: concurrencia optimista. Si otra petición cambió el registro, el
  guardado falla y la API responde 409 «vuelva a cargarlo».

Agregue el módulo a `importar_todo()` en `app/modelos/__init__.py` y genere la
migración: `alembic revision --autogenerate -m "<modulo>"`.

## 2. Errores e integridad

- `raise no_existe("El cliente")` → 404, `invalido("…", detalle)` → 422,
  `conflicto("…")` → 409. La interfaz muestra `mensaje` y marca los campos de
  `detalle` (`[{campo, mensaje}]`).
- `integridad.verificar_referencias(db, obj)` antes de guardar: revisa que cada
  llave foránea apunte a un registro de la misma organización.
- `integridad.guardar(db, obj, "Ya existe un cliente con ese código.")` y
  `integridad.borrar(db, obj, "El cliente")`: una violación de unicidad o un
  registro en uso responden 409 y la sesión sigue usable.

## 3. Atributos

Si el módulo necesita características configurables, declara dos tablas:

```python
from app.atributos.modelos import SeleccionBase, ValorBase

class ValorCliente(ValorBase, Base):
    __tablename__ = "valores_cliente"
    __dueno__ = "cliente_id"
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"), index=True)
    seleccion: Mapped[list[SeleccionCliente]] = relationship(cascade="all, delete-orphan", lazy="selectin",
                                                            back_populates="valor")

class SeleccionCliente(SeleccionBase, Base):
    __tablename__ = "seleccion_cliente"
    valor_id: Mapped[int] = mapped_column(ForeignKey("valores_cliente.id", ondelete="CASCADE"), primary_key=True)
    valor: Mapped[ValorCliente] = relationship(back_populates="seleccion")
```

Para guardar un valor: `valores.aplicar(fila, valores.convertir(db, atributo, entrada))`.
Para devolverlo: `valores.leer(fila)` (misma forma que la entrada) o `valores.texto(fila)`.
La configuración de unidades y atributos ya sabe revisar las tablas de valores de
todos los módulos antes de cambiar un tipo de dato o el factor de una unidad.

**Plantillas heredables** (tipos de cliente, clases de activo…): un modelo con
`codigo`, `padre` y `asignaciones`, donde cada asignación hereda de
`AsignacionBase` (y puede agregar sus propias columnas). `esquema.resolver(plantilla)`
devuelve los campos efectivos: los heredados más los propios, con los ocultos fuera.

**Referencias**: `referencias.registrar("cliente", Cliente)` al importar el módulo.
Así cualquier atributo de tipo `referencia` puede apuntar a clientes, y la
interfaz los busca en `/api/referencias/cliente`.

## 4. Rutas

```python
DB = Annotated[Session, Depends(obtener_db)]  # app.web.dependencias
router = APIRouter(prefix="/api/clientes", tags=["clientes"])
```

Las rutas que escriben confirman con `db.commit()`. Incluya el router en
`app/main.py`. Para catálogos de configuración simples, `app.atributos.configuracion.Catalogo`
da alta, edición, baja y listado con sus validaciones.

## 5. Interfaz

- Una entrada en `MODULOS` de `App.vue` y sus rutas en `router.js`
  (`meta.modulo`, `meta.migas`, `meta.titulo`).
- `TablaDatos` para listas, `PanelEnLinea` para formularios dentro de la página,
  `BotonConfirmar` para bajas, `CampoAtributo` para cualquier atributo según su tipo.
- Colores, tipografía y espaciado solo con los tokens de `styles.css`
  (`design-system/MASTER.md`).
