// Textos para mostrar valores de atributos y fechas.
export const TIPOS_DATO = {
  texto: 'Texto', entero: 'Número entero', decimal: 'Número decimal', booleano: 'Sí / no',
  fecha: 'Fecha', opcion: 'Una opción', opciones: 'Varias opciones', referencia: 'Referencia',
}

export function fecha(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('es', { dateStyle: 'medium', timeStyle: 'short' })
}

export function valorTexto(valor, atributo) {
  if (valor === null || valor === undefined || valor === '') return '—'
  const t = atributo?.tipo_dato
  const nombreOpcion = (c) => atributo?.opciones?.find((o) => o.codigo === c)?.nombre || c
  if (t === 'opcion') return nombreOpcion(valor)
  if (t === 'opciones') return valor.map(nombreOpcion).join(', ')
  if (t === 'booleano') return valor ? 'Sí' : 'No'
  if (typeof valor === 'object' && 'valor' in valor) return `${valor.valor} ${valor.unidad || ''}`.trim()
  if (Array.isArray(valor)) return valor.join(', ')
  return String(valor)
}

// Tono de la insignia de un estado según sus reglas
export function tonoEstado(estado) {
  if (!estado) return ''
  if (estado.operable) return 'ok'
  if (estado.inicial || estado.codigo === 'BORRADOR') return 'info'
  return ''
}

// Clase de la insignia de un estado (.estado-ok, .estado-info…): color, forma y texto
export const claseEstado = (estado) => `estado-${tonoEstado(estado) || 'neutro'}`
