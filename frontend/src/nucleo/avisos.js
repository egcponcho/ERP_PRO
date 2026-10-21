// Avisos breves (toasts) compartidos por toda la app.
import { reactive } from 'vue'

export const avisos = reactive({ lista: [] })
let siguiente = 1

export function avisar(texto, tipo = 'ok', ms = 3800) {
  const id = siguiente++
  avisos.lista.push({ id, texto, tipo })
  if (ms) setTimeout(() => cerrarAviso(id), ms)
}

export function cerrarAviso(id) {
  const i = avisos.lista.findIndex((a) => a.id === id)
  if (i >= 0) avisos.lista.splice(i, 1)
}

export function avisarError(e) {
  avisar(e?.message || 'Ocurrió un error inesperado.', 'error', 6000)
}
