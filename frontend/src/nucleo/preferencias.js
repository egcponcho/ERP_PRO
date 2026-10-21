// Preferencias de cada persona en este navegador: columnas, anchos y densidad de
// cada tabla, sus vistas guardadas y las filas por página. Cuando exista el
// módulo de acceso se guardarán en el perfil del usuario (mismo formato).
import { reactive } from 'vue'

const CLAVE = 'erp.preferencias'

function leer() {
  try { return JSON.parse(localStorage.getItem(CLAVE)) || {} } catch { return {} }
}

export const preferencias = reactive({ tablas: {}, vistas: {}, filas: 25, ...leer() })

function escribir() {
  try { localStorage.setItem(CLAVE, JSON.stringify(preferencias)) } catch { /* sin almacenamiento: dura la sesión */ }
}

export const filasDefecto = () => Number(preferencias.filas) || 25

export function guardarTabla(tabla, conf) {
  if (conf) preferencias.tablas[tabla] = conf
  else delete preferencias.tablas[tabla]
  escribir()
}

export function guardarVistas(pantalla, lista) {
  preferencias.vistas[pantalla] = lista
  escribir()
}
