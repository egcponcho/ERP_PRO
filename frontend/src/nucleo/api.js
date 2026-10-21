// Cliente de la API: JSON de ida y vuelta, errores como ApiError {mensaje, codigo, detalle}.
const BASE = '/api'

export class ApiError extends Error {
  constructor(status, cuerpo) {
    super(cuerpo?.mensaje || `Error ${status}`)
    this.status = status
    this.codigo = cuerpo?.codigo
    this.detalle = cuerpo?.detalle
  }

  // {campo: mensaje} para marcar cada campo del formulario (detalle = [{campo, mensaje}])
  get porCampo() {
    const res = {}
    if (Array.isArray(this.detalle)) for (const d of this.detalle) if (d?.campo) res[d.campo] = d.mensaje
    return res
  }
}

function qs(params) {
  if (!params) return ''
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    // Una lista se manda repetida: ?tipo=A&tipo=B
    for (const x of Array.isArray(v) ? v : [v]) if (x !== null && x !== undefined && x !== '') p.append(k, x)
  }
  const s = p.toString()
  return s ? `?${s}` : ''
}

async function pedir(metodo, ruta, { cuerpo, params } = {}) {
  let r
  try {
    r = await fetch(`${BASE}${ruta}${qs(params)}`, {
      method: metodo,
      headers: cuerpo !== undefined ? { 'Content-Type': 'application/json' } : {},
      body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
    })
  } catch {
    throw new ApiError(0, { mensaje: 'No hay conexión con el servidor. Revise que la API esté encendida.' })
  }
  if (r.status === 204) return null
  const texto = await r.text()
  let datos = null
  try { datos = texto ? JSON.parse(texto) : null } catch { datos = { mensaje: texto } }
  if (!r.ok) throw new ApiError(r.status, datos)
  return datos
}

export const api = {
  get: (ruta, params) => pedir('GET', ruta, { params }),
  post: (ruta, cuerpo) => pedir('POST', ruta, { cuerpo: cuerpo ?? {} }),
  patch: (ruta, cuerpo) => pedir('PATCH', ruta, { cuerpo }),
  put: (ruta, cuerpo) => pedir('PUT', ruta, { cuerpo }),
  del: (ruta) => pedir('DELETE', ruta),
}
